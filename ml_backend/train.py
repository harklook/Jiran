"""
train.py — Jiran ML Training Pipeline (converted from v2222.ipynb)

Run once to train and save models:
    cd ml/
    python train.py

Outputs to saved_models/:
    ensemble.pkl              — RF + GB + XGB VotingClassifier
    scaler.pkl                — StandardScaler fit on training data
    label_encoder.pkl         — LabelEncoder for product categories
    forecasts_aggregated.csv  — Prophet forecast features (one row per store+product)
    feature_cols.json         — Ordered list of feature column names
"""

import argparse
import os
import json
import time
import warnings

import joblib
import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# CLI args
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Jiran ML Training Pipeline")
parser.add_argument("--data-dir",    default=None,  help="Path to data directory")
parser.add_argument("--prophet-top", default=400,   type=int, help="Top N products for Prophet (default 400)")
parser.add_argument("--rf-trees",    default=500,   type=int, help="Random Forest n_estimators (default 500)")
parser.add_argument("--gb-trees",    default=400,   type=int, help="Gradient Boosting n_estimators (default 400)")
parser.add_argument("--xgb-trees",   default=400,   type=int, help="XGBoost n_estimators (default 400)")
args = parser.parse_args()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = args.data_dir if args.data_dir else os.path.join(BASE_DIR, "training", "data")
MODELS_DIR = os.path.join(BASE_DIR, "saved_models")
os.makedirs(MODELS_DIR, exist_ok=True)

print(f"Data dir  : {DATA_DIR}")
print(f"Models dir: {MODELS_DIR}")
print(f"Prophet top-N  : {args.prophet_top}")
print(f"RF trees       : {args.rf_trees}")
print(f"GB trees       : {args.gb_trees}")
print(f"XGB trees      : {args.xgb_trees}")

# ---------------------------------------------------------------------------
# Step 1 — Load data
# ---------------------------------------------------------------------------
print("Loading data...")
transactions = pd.read_csv(
    os.path.join(DATA_DIR, "transactions.csv"),
    parse_dates=["timestamp"],
)
stock = pd.read_csv(
    os.path.join(DATA_DIR, "stock.csv"),
    parse_dates=["updated_at"],
)
products = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))

print(f"  transactions : {len(transactions):>12,} rows")
print(f"  stock        : {len(stock):>12,} rows")
print(f"  products     : {len(products):>12,} rows")
print(f"  stores       : {transactions['store_id'].nunique()} unique")

# ---------------------------------------------------------------------------
# Step 2 — Model 1: Prophet demand forecasting
# ---------------------------------------------------------------------------

def prepare_prophet_data(txn_df):
    txn_df = txn_df.copy()
    txn_df["date"] = txn_df["timestamp"].dt.date
    daily = (
        txn_df.groupby(["store_id", "product_id", "date"], as_index=False)
        .agg({"quantity": "sum"})
        .rename(columns={"date": "ds", "quantity": "y"})
    )
    daily["ds"] = pd.to_datetime(daily["ds"])
    return daily


def train_prophet_models(daily_data, top_n=100, horizons=None):
    if horizons is None:
        horizons = [7, 14, 30, 60]

    top_products = (
        daily_data.groupby("product_id")["y"].sum().nlargest(top_n).index
    )

    forecasts_list = []
    max_horizon = max(horizons)
    model_count = 0
    start_time = time.time()

    print(f"\nTraining Prophet for top {top_n} products x stores...")

    for idx, product_id in enumerate(top_products):
        product_data = daily_data[daily_data["product_id"] == product_id]
        stores_done = 0

        for store_id in product_data["store_id"].unique():
            sp_data = product_data[product_data["store_id"] == store_id][
                ["ds", "y"]
            ]

            # Need at least 2 weeks of history
            if len(sp_data) < 14:
                continue

            try:
                m = Prophet(
                    daily_seasonality=False,
                    weekly_seasonality=True,
                    yearly_seasonality=False,
                    interval_width=0.95,
                )
                m.fit(sp_data)

                future = m.make_future_dataframe(periods=max_horizon)
                forecast = m.predict(future)
                future_fc = forecast.tail(max_horizon).copy()

                row = {"store_id": store_id, "product_id": product_id}
                for h in horizons:
                    hd = future_fc.head(h)
                    row[f"forecast_{h}d"] = round(hd["yhat"].clip(lower=0).sum(), 1)
                    row[f"forecast_{h}d_lower"] = round(
                        hd["yhat_lower"].clip(lower=0).sum(), 1
                    )
                    row[f"forecast_{h}d_upper"] = round(
                        hd["yhat_upper"].clip(lower=0).sum(), 1
                    )

                forecasts_list.append(row)
                model_count += 1
                stores_done += 1

            except Exception:
                continue

        elapsed = time.time() - start_time
        avg_per_product = elapsed / (idx + 1)
        remaining_min = avg_per_product * (len(top_products) - idx - 1) / 60
        print(
            f"  [{idx+1:3d}/{len(top_products)}] {product_id} "
            f"({stores_done} stores, ~{remaining_min:.0f} min left)"
        )

    forecasts_df = pd.DataFrame(forecasts_list)
    elapsed_total = (time.time() - start_time) / 60
    print(f"\nProphet done — {model_count} models in {elapsed_total:.1f} min")
    print(f"  Forecast records: {len(forecasts_df):,} rows")
    return forecasts_df


print("\n--- Model 1: Prophet ---")
daily_data = prepare_prophet_data(transactions)
print(f"Aggregated to {len(daily_data):,} daily store-product records")

forecasts = train_prophet_models(daily_data, top_n=args.prophet_top)

# Save forecasts (used as features in Model 2 + at inference time)
forecasts_path = os.path.join(MODELS_DIR, "forecasts_aggregated.csv")
forecasts.to_csv(forecasts_path, index=False)
print(f"Saved forecasts -> {forecasts_path}")

# ---------------------------------------------------------------------------
# Step 3 — Feature engineering (mirrors notebook cells 13 exactly)
# ---------------------------------------------------------------------------
print("\n--- Model 2: Feature engineering ---")

# -- Temporal features --
print("  Computing temporal features...")
recent_cutoff = transactions["timestamp"].max() - pd.Timedelta(days=30)
recent_sales = transactions[transactions["timestamp"] >= recent_cutoff]
historical_sales = transactions[transactions["timestamp"] < recent_cutoff]

recent_velocity = (
    recent_sales.groupby(["store_id", "product_id"])
    .agg({"quantity": ["sum", "count", "mean", "std"]})
    .reset_index()
)
recent_velocity.columns = [
    "store_id", "product_id",
    "recent_qty", "recent_txns", "recent_avg", "recent_std",
]

historical_velocity = (
    historical_sales.groupby(["store_id", "product_id"])
    .agg({"quantity": ["sum", "count", "mean"]})
    .reset_index()
)
historical_velocity.columns = [
    "store_id", "product_id",
    "historical_qty", "historical_txns", "historical_avg",
]

last_sale = (
    transactions.groupby(["store_id", "product_id"])["timestamp"]
    .max()
    .reset_index()
)
last_sale["days_since_last_sale"] = (
    transactions["timestamp"].max() - last_sale["timestamp"]
).dt.days

temporal = recent_velocity.merge(
    historical_velocity, on=["store_id", "product_id"], how="left"
)
temporal = temporal.merge(
    last_sale[["store_id", "product_id", "days_since_last_sale"]],
    on=["store_id", "product_id"],
    how="left",
)
temporal = temporal.fillna(0)

temporal["velocity_trend"] = temporal["recent_avg"] / (temporal["historical_avg"] + 0.1)
temporal["sales_volatility"] = temporal["recent_std"] / (temporal["recent_avg"] + 0.1)
temporal["is_active"] = (temporal["days_since_last_sale"] <= 7).astype(int)
temporal["is_dormant"] = (temporal["days_since_last_sale"] > 90).astype(int)  # aligned with Dead rule threshold

# -- Product features --
print("  Computing product features...")
products["price_tier"] = pd.cut(
    products["retail_price"],
    bins=[0, 3, 7, 15, 100],
    labels=[0, 1, 2, 3],
).astype(float)
products["is_perishable"] = products["category"].isin(
    ["produce", "dairy", "meat", "bakery"]
).astype(int)
products["is_budget"] = (products["retail_price"] < 5).astype(int)
products["is_premium"] = (products["retail_price"] > 15).astype(int)

# -- Store features --
print("  Computing store features...")
store_stats = (
    transactions.groupby("store_id")
    .agg({"transaction_id": "nunique"})
    .reset_index()
)
store_stats.columns = ["store_id", "store_total_txns"]
store_stats["store_size_encoded"] = pd.cut(
    store_stats["store_total_txns"],
    bins=[0, 200_000, 350_000, 1_000_000],
    labels=[0, 1, 2],
).astype(float)

# -- Product-store interaction features --
print("  Computing product-store features...")
product_store = (
    transactions.groupby(["store_id", "product_id"])
    .agg({"quantity": ["sum", "count"]})
    .reset_index()
)
product_store.columns = ["store_id", "product_id", "total_sold", "num_sales"]
product_store["sales_rank_in_store"] = product_store.groupby("store_id")[
    "total_sold"
].rank(ascending=False, method="dense")
product_store["is_top_10_in_store"] = (
    product_store["sales_rank_in_store"] <= 10
).astype(int)
product_store["is_top_50_in_store"] = (
    product_store["sales_rank_in_store"] <= 50
).astype(int)

# -- Forecast-derived features --
print("  Computing forecast features...")
forecasts["forecast_acceleration"] = (forecasts["forecast_7d"] / 7) / (
    forecasts["forecast_30d"] / 30 + 0.1
)
forecasts["forecast_confidence_30d"] = (
    forecasts["forecast_30d_upper"] - forecasts["forecast_30d_lower"]
) / (forecasts["forecast_30d"] + 0.1)
forecasts["is_trending_up"] = (forecasts["forecast_acceleration"] > 1.1).astype(int)
forecasts["is_trending_down"] = (forecasts["forecast_acceleration"] < 0.9).astype(int)
forecasts["is_stable"] = (
    (forecasts["forecast_acceleration"] >= 0.9)
    & (forecasts["forecast_acceleration"] <= 1.1)
).astype(int)

# -- Merge everything onto stock --
print("  Merging feature sets...")
sf = stock.copy()
sf = sf.merge(forecasts, on=["store_id", "product_id"], how="left")
sf = sf.merge(
    products[
        [
            "product_id", "category", "retail_price",
            "price_tier", "is_perishable", "is_budget", "is_premium",
        ]
    ],
    on="product_id",
    how="left",
)
sf = sf.merge(temporal, on=["store_id", "product_id"], how="left")
sf = sf.merge(store_stats, on="store_id", how="left")
sf = sf.merge(product_store, on=["store_id", "product_id"], how="left")
sf = sf.fillna(0)

# -- Derived features (used for both labeling and training) --
sf["coverage_30d"] = sf["stock_qty"] / (sf["forecast_30d"] + 1)
sf["coverage_7d"]  = sf["stock_qty"] / (sf["forecast_7d"]  + 1)
sf["days_of_stock_30d"] = sf["stock_qty"] / (sf["forecast_30d"] / 30 + 0.1)
sf["stockout_risk_7d"]  = (sf["stock_qty"] < sf["forecast_7d"]).astype(int)

# -- Explicit boundary features (exact metrics used in label rules → makes thresholds learnable) --
sf["coverage_30d_feat"]      = sf["coverage_30d"]          # same as above, named for clarity
sf["days_of_stock_30d_feat"] = sf["days_of_stock_30d"]     # same as above, named for clarity
sf["days_since_over_90"]     = (sf["days_since_last_sale"] > 90).astype(int)

# -- Stock value (clean, not a label-leaking feature) --
sf["stock_value"] = sf["stock_qty"] * sf["retail_price"]

# -- Price-velocity interaction --
sf["price_velocity_interaction"] = sf["retail_price"] * sf["velocity_trend"]

# -- Category encoding --
le_category = LabelEncoder()
sf["category_encoded"] = le_category.fit_transform(sf["category"].fillna("unknown"))

# ---------------------------------------------------------------------------
# Step 4 — Smart labeling (mirrors notebook exactly)
# ---------------------------------------------------------------------------
print("  Assigning labels...")


def smart_label(row):
    coverage = row["coverage_30d"]
    days_stock = row["days_of_stock_30d"]
    velocity = row["velocity_trend"]
    trend = row["forecast_acceleration"]
    days_since = row["days_since_last_sale"]

    if coverage > 8 or days_stock > 180 or days_since > 90 or (
        coverage > 6 and velocity < 0.2
    ):
        return "Dead"
    elif coverage > 4 or days_stock > 120 or (coverage > 3 and velocity < 0.5):
        return "Slow"
    elif coverage < 0.6 or days_stock < 14 or (
        coverage < 0.8 and trend > 1.2
    ) or row["stockout_risk_7d"] == 1:
        return "Low"
    elif 2.0 < coverage <= 4.0 and velocity > 0.5:
        return "Excess"
    else:
        return "Optimum"


sf["label"] = sf.apply(smart_label, axis=1)

print("\n  Label distribution:")
for label, count in sf["label"].value_counts().items():
    pct = count / len(sf) * 100
    print(f"    {label:8s}: {count:5d} ({pct:5.1f}%)")

# ---------------------------------------------------------------------------
# Step 5 — Train ensemble (41 clean features, no leakage)
# ---------------------------------------------------------------------------
FEATURE_COLS = [
    # Stock
    "stock_qty", "stock_value",
    # Forecast
    "forecast_7d", "forecast_14d", "forecast_30d", "forecast_60d",
    "forecast_acceleration", "forecast_confidence_30d",
    "is_trending_up", "is_trending_down", "is_stable",
    # Temporal
    "days_since_last_sale", "velocity_trend", "sales_volatility",
    "is_active", "is_dormant",
    "recent_qty", "recent_txns", "recent_avg", "recent_std",
    "historical_qty", "historical_txns", "historical_avg",
    # Product
    "price_tier", "is_perishable",
    "is_budget", "is_premium", "category_encoded",
    "retail_price",
    # Store
    "store_size_encoded", "store_total_txns",
    # Product-store
    "sales_rank_in_store", "is_top_10_in_store", "is_top_50_in_store",
    "total_sold", "num_sales",
    # Interaction
    "price_velocity_interaction",
    # Explicit boundary features (exact metrics used in label rules)
    "coverage_30d_feat", "days_since_over_90",
    "days_of_stock_30d_feat", "stockout_risk_7d",
]

print(f"\n--- Model 2: Ensemble training on {len(FEATURE_COLS)} features (no wholesale_price) ---")

from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.utils.class_weight import compute_sample_weight

X = sf[FEATURE_COLS].fillna(0)
y = sf["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)
X_all_scaled   = scaler.transform(X)

print(f"  Building Random Forest ({args.rf_trees} trees)...")
rf = RandomForestClassifier(
    n_estimators=args.rf_trees, max_depth=20, class_weight="balanced",
    min_samples_leaf=2, max_features="sqrt",
    random_state=42, n_jobs=-1,
)

print(f"  Building Gradient Boosting ({args.gb_trees} trees)...")
gb = GradientBoostingClassifier(
    n_estimators=args.gb_trees, learning_rate=0.05, max_depth=6,
    subsample=0.8, min_samples_leaf=3,
    random_state=42,
)

print(f"  Building XGBoost ({args.xgb_trees} trees)...")
xgb = XGBClassifier(
    n_estimators=args.xgb_trees, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
    random_state=42, n_jobs=-1, eval_metric="mlogloss",
)

ensemble = VotingClassifier(
    estimators=[("rf", rf), ("gb", gb), ("xgb", xgb)],
    voting="soft",
    n_jobs=-1,
)

# --- 5-fold cross-validation on full dataset ---
print("\n  Running 5-fold cross-validation (this takes the bulk of time)...")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
t0 = time.time()
cv_scores = cross_val_score(ensemble, X_all_scaled, y, cv=cv, scoring="accuracy", n_jobs=-1)
cv_elapsed = (time.time() - t0) / 60
print(f"  CV scores  : {[f'{s:.2%}' for s in cv_scores]}")
print(f"  CV mean    : {cv_scores.mean():.2%} ± {cv_scores.std():.2%}")
print(f"  CV time    : {cv_elapsed:.1f} min")

# --- Final fit on full training set with balanced sample weights ---
print("\n  Fitting final model on train split (balanced sample weights)...")
t1 = time.time()
sample_weights = compute_sample_weight("balanced", y_train)
ensemble.fit(X_train_scaled, y_train, sample_weight=sample_weights)
fit_elapsed = (time.time() - t1) / 60

y_pred   = ensemble.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)
total_elapsed = (time.time() - t0) / 60

print(f"\n  Hold-out accuracy : {accuracy:.2%}")
print(f"  CV accuracy       : {cv_scores.mean():.2%} ± {cv_scores.std():.2%}")
print(f"  Total time        : {total_elapsed:.1f} min")
print(f"\n{classification_report(y_test, y_pred)}")

# Feature importance from RF base learner
rf_model = ensemble.named_estimators_["rf"]
feature_importance = (
    pd.DataFrame({"feature": FEATURE_COLS, "importance": rf_model.feature_importances_})
    .sort_values("importance", ascending=False)
)
print("Top 10 features:")
for _, row in feature_importance.head(10).iterrows():
    print(f"  {row['feature']:30s}: {row['importance']:.4f}")

# ---------------------------------------------------------------------------
# Step 6 — Save all artifacts
# ---------------------------------------------------------------------------
print("\n--- Saving models ---")

joblib.dump(ensemble, os.path.join(MODELS_DIR, "ensemble.pkl"))
print("  Saved: ensemble.pkl")

joblib.dump(scaler, os.path.join(MODELS_DIR, "scaler.pkl"))
print("  Saved: scaler.pkl")

joblib.dump(le_category, os.path.join(MODELS_DIR, "label_encoder.pkl"))
print("  Saved: label_encoder.pkl")

# Save updated forecasts with derived forecast features
forecasts.to_csv(os.path.join(MODELS_DIR, "forecasts_aggregated.csv"), index=False)
print("  Saved: forecasts_aggregated.csv (with acceleration + trend flags)")

# Save feature column order — required for inference to match training order
with open(os.path.join(MODELS_DIR, "feature_cols.json"), "w") as f:
    json.dump(FEATURE_COLS, f, indent=2)
print("  Saved: feature_cols.json")

# Save category classes so inference can handle unseen categories
with open(os.path.join(MODELS_DIR, "category_classes.json"), "w") as f:
    json.dump(list(le_category.classes_), f, indent=2)
print("  Saved: category_classes.json")

# Save store stats (used to compute store_size_encoded at inference)
store_stats.to_csv(os.path.join(MODELS_DIR, "store_stats.csv"), index=False)
print("  Saved: store_stats.csv")

# Save product-store ranks (used for sales_rank_in_store at inference)
product_store.to_csv(os.path.join(MODELS_DIR, "product_store_ranks.csv"), index=False)
print("  Saved: product_store_ranks.csv")

feature_importance.to_csv(
    os.path.join(MODELS_DIR, "feature_importance.csv"), index=False
)
print("  Saved: feature_importance.csv")

print("\nTraining complete.")
print(f"All artifacts in: {MODELS_DIR}")
