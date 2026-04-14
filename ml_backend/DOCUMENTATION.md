# Jiran ML Pipeline — Documentation

## Overview

This pipeline reads live inventory, product, and transaction data exported from Supabase view tables, runs an ensemble ML model to predict stock status for every product in every store, generates transfer and restock recommendations, and pushes the results back to Supabase.

---

## How to Run

```bash
cd /Users/muhammadabdulmohsin/MLLLL-copy

# Run ML only — writes 3 local JSON files
python3 run_local_view_ml.py

# Run ML + push results to Supabase
python3 run_local_view_ml.py --push
```

Custom input files (optional):
```bash
python3 run_local_view_ml.py \
  --inventory /path/to/v_inventory_snapshot.json \
  --products  /path/to/v_store_products.json \
  --transactions /path/to/v_store_transactions.json \
  --push
```

---

## Input Files

Three JSON files exported from Supabase view tables. Default paths point to `~/Downloads/`.

| File | View | Key Fields |
|---|---|---|
| `v_inventory_snapshot.json` | `v_inventory_snapshot` | `store_id`, `product_id`, `stock_qty`, `updated_at` |
| `v_store_products.json` | `v_store_products` | `store_id`, `product_id`, `product_name`, `category`, `retail_price` |
| `v_store_transactions.json` | `v_store_transactions` | `store_id`, `product_id`, `transaction_id`, `quantity`, `timestamp` |

> **Important:** `product_id` in these views is a store-scoped integer assigned by each POS system. The same physical product will have different `product_id` values in different stores. The pipeline handles this automatically using product name matching for cross-store logic.

---

## Pipeline Steps (`run_local_view_ml.py`)

### 1. Load & Normalise

- All three files are loaded into DataFrames.
- `store_id` and `product_id` are cast to `str` across all three sources so joins work cleanly.
- Products: categories are lowercased and stripped. Duplicates on `(store_id, product_id)` are dropped keeping the latest.
- Inventory: deduplicated on `(store_id, product_id)` keeping the most recent `updated_at`.

### 2. Aggregate Transactions

Transactions are split into two windows relative to the most recent timestamp in the data:

| Window | Columns produced |
|---|---|
| Last 30 days (recent) | `recent_qty`, `recent_txns`, `recent_avg`, `recent_std` |
| Older than 30 days (historical) | `historical_qty`, `historical_txns`, `historical_avg` |
| All time | `total_sold`, `num_sales`, `days_since_last_sale` |
| Per store | `store_total_txns` |

### 3. Build Model Input

Inventory is joined to products (`inner join` on `store_id + product_id`), then all transaction aggregations are left-joined. The result is one row per `(store_id, product_id)` with all features populated.

A `canonical_product_id` column is also computed = `product_name.strip().lower()`. This is used internally by the transfer engine to match the same physical product across stores (since POS-assigned `product_id` values differ per store).

### 4. Run ML Predictions

The trained ensemble model (`saved_models/ensemble.pkl`) predicts a stock status label for every row.

**41 features used:**

| Feature Group | Features |
|---|---|
| Stock | `stock_qty`, `stock_value` |
| Forecast (Prophet) | `forecast_7d/14d/30d/60d`, `forecast_acceleration`, `forecast_confidence_30d`, `is_trending_up/down/stable` |
| Sales temporal | `days_since_last_sale`, `velocity_trend`, `sales_volatility`, `is_active`, `is_dormant`, `recent_qty/txns/avg/std`, `historical_qty/txns/avg` |
| Product | `price_tier`, `is_perishable`, `is_budget`, `is_premium`, `category_encoded`, `retail_price` |
| Store | `store_size_encoded`, `store_total_txns` |
| Product-store rank | `sales_rank_in_store`, `is_top_10/50_in_store`, `total_sold`, `num_sales` |
| Interactions | `price_velocity_interaction`, `coverage_30d_feat`, `days_since_over_90`, `days_of_stock_30d_feat`, `stockout_risk_7d` |

**Output labels:**

| Label | Meaning |
|---|---|
| `Low` | Stock is critically low — needs restocking or transfer in |
| `Optimum` | Healthy stock level |
| `Excess` | Overstocked — candidate to donate to Low stores |
| `Slow` | Stock is moving slowly — candidate to donate |
| `Dead` | No recent sales — candidate to donate |

**Known categories:** `bakery`, `beverages`, `dairy`, `frozen`, `meat`, `pantry`, `produce`, `snacks`. Unknown categories (e.g. `household`, `electronics`, `personal care`) are encoded as `-1` and handled gracefully by the model.

**Forecast fallback:** If a `(store_id, product_id)` pair was not in the Prophet training set, forecast features default to 0 and `recent_qty` is used as the 30-day demand proxy.

### 5. Compute Transfer Recommendations

For each product (grouped by canonical name across all stores):

1. **Donors** = stores where prediction is `Excess`, `Dead`, or `Slow`
2. **Receivers** = stores where prediction is `Low`
3. Receivers are sorted most urgent first (lowest stock coverage).
4. For each receiver, the engine checks if a single donor can cover the full need:
   - **Single-store transfer** — one donor covers the full need. Preferred (simpler logistics).
   - **Combined transfer** — multiple donors each contribute. All transfers share a `group_id`.
5. If no donors can cover the remaining gap → a **restock** recommendation is issued instead.

Donor priority order: `Excess` → `Dead` → `Slow`.

Coverage targets:
- Receiver target: `1.5×` 30-day demand
- Donor minimum retained after transfer: `0.9×` 30-day demand (Excess) or `1.5×` (Slow)

### 6. Write Output Files

Three files written to `MLLLL-copy/`:

| File | Contents |
|---|---|
| `ml_predictions.json` | Stock status label + all 5 class probabilities for every product |
| `ml_transfers.json` | Cross-store transfer recommendations |
| `ml_restocks.json` | Supplier restock recommendations (Low items with no donors) |

Each file contains a `metadata` block (source files, row counts, mapping checks, category coverage) and a `summary` block.

---

## Supabase Push (`--push`)

Results are pushed via two PostgreSQL RPC functions which handle all ID resolution server-side.

### ID Mapping Chain

POS-assigned identifiers in the view files are human-readable (`store_id = "MM-RT-063"`, `product_id = 49202`). Supabase tables use UUIDs. The RPC functions resolve the chain internally:

```
store_id (e.g. "MM-RT-063")
  → retailer_profiles.store_id → retailer_profiles.id       (retailer_id UUID)
  → pos_connections.retailer_id → pos_connections.id         (pos_connection_id UUID)
  + product_id (numeric)
  → product_variations.product_id + pos_connection_id        (product_variation_id)
```

### RPC Functions

| Function | Table written to | Behaviour |
|---|---|---|
| `batch_insert_ml_predictions(payload jsonb)` | `ml_inventory_predictions` | Truncates table then inserts fresh predictions |
| `batch_insert_ml_transfers(payload jsonb)` | `ml_inventory_transfer_recommendations` | Truncates table then inserts fresh transfers |

Both functions return `{"inserted": N, "skipped": N}`.

Rows are skipped only if the `store_id` or `product_id` cannot be resolved to a valid UUID chain (e.g. test data not present in `retailer_profiles`).

### Tables Written

**`ml_inventory_predictions`**

| Column | Source |
|---|---|
| `retailer_id` | resolved from `store_id` |
| `pos_connection_id` | resolved from `store_id` |
| `product_variation_id` | resolved from `product_id` |
| `product_name` | from view |
| `prediction` | ML label: Low / Optimum / Excess / Slow / Dead |
| `confidence` | max class probability |
| `prob_dead/excess/low/optimum/slow` | all 5 class probabilities |

**`ml_inventory_transfer_recommendations`**

| Column | Source |
|---|---|
| `from_retailer_id`, `from_pos_connection_id`, `from_product_variation_id` | resolved from `from_store` + `from_product_id` |
| `to_retailer_id`, `to_pos_connection_id`, `to_product_variation_id` | resolved from `to_store` + `to_product_id` |
| `transfer_qty` | units to move |
| `from/to_label` | ML label of each store |
| `from/to_stock_before/after` | stock levels before and after transfer |
| `from/to_coverage_after` | days of demand coverage after transfer |
| `demand_30d` | estimated 30-day demand for this product |
| `transfer_type` | `macro` (covers ≥50% of need) or `micro` (partial) |
| `transfer_mode` | `single` (one donor) or `combined` (multiple donors) |

---

## Model Artifacts (`saved_models/`)

| File | Description |
|---|---|
| `ensemble.pkl` | Trained RF + GB + XGB voting classifier |
| `scaler.pkl` | StandardScaler fitted on training data |
| `label_encoder.pkl` | LabelEncoder for category strings |
| `feature_cols.json` | Ordered list of 41 feature column names |
| `category_classes.json` | Known category strings the model was trained on |
| `forecasts_aggregated.csv` | Prophet forecast features per `(store_id, product_id)` |
| `store_stats.csv` | Store size encoding per `store_id` |
| `product_store_ranks.csv` | Sales rank per `(store_id, product_id)` |
| `feature_importance.csv` | Feature importance from training |

---

## Key Design Decisions

**Why canonical product name instead of product_id for transfers?**
Each POS system assigns its own integer `product_id` per store, so the same physical product has different IDs across stores. The transfer engine groups by `product_name.strip().lower()` (canonical name) to correctly identify the same product across stores. Predictions still use the original `product_id` for model feature lookups.

**Why RPC functions instead of direct inserts?**
Direct inserts from Python would require fetching and joining UUID lookups for 1000+ rows across 3 tables. The RPC approach pushes that resolution to the database where it runs in a single transaction with no round-trips, and handles FK constraints correctly.

**Why truncate instead of upsert?**
Each ML run produces a complete fresh view of all store-product pairs. Truncate + insert is simpler and avoids stale rows from products that may have been removed from the catalogue since the last run.
