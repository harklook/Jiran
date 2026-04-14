"""
map_supabase_inventory.py
─────────────────────────
Reads Supabase CSV exports and produces ml_inventory rows for the ML API watcher.

JOIN LOGIC (per user spec)
──────────────────────────
ACTIVE CONNECTION FILTER
  pos_connections WHERE is_active = 't'
    AND retailer_id IN (SELECT id FROM retailer_profiles)

INVENTORY (per active connection)
  product_inventory  ← stock per (product_variation × location)
    └─ product_variations (active=t, pos_connection_id = active)
         └─ products (name, category, retail_price via price on variation)

ORDER HISTORY (per active connection)
  orders (pos_connection_id = active)
    └─ order_items (pos_connection_id = active)
         └─ mapped to products via:
            order_items.item_name == products.name
              WHERE products.id == product_variations.product_id

OUTPUT
  localdatasb/ml_inventory.csv     — ML API ready
  localdatasb/create_ml_tables.sql — SQL to create Supabase tables

RUN
  python map_supabase_inventory.py           # local CSV only
  python map_supabase_inventory.py --push    # also upload to Supabase
"""

import argparse
import os
from datetime import datetime, timezone, timedelta

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SB_DIR  = "/Users/muhammadabdulmohsin/Downloads/Supabase_copy"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "localdatasb")
os.makedirs(OUT_DIR, exist_ok=True)

NOW = datetime.now(timezone.utc)
D30 = NOW - timedelta(days=30)

# ---------------------------------------------------------------------------
# Category normalisation to ML training vocabulary
# ---------------------------------------------------------------------------
CAT_MAP = {
    "beverages": "beverages", "beverage": "beverages",
    "frozen": "frozen",
    "produce": "produce",
    "household": "household",
    "pantry": "pantry",
    "personal care": "personal_care", "personal_care": "personal_care",
    "snacks": "snacks", "chocolates & sweets": "snacks",
    "bakery": "bakery",
    "dairy": "dairy",
    "meat": "meat",
}

def norm_cat(c):
    if pd.isna(c):
        return "general"
    return CAT_MAP.get(str(c).lower().strip(), "general")

# ---------------------------------------------------------------------------
# Load CSVs
# ---------------------------------------------------------------------------
print("Loading Supabase CSVs…")

pos_conn   = pd.read_csv(f"{SB_DIR}/pos_connections.csv")
retailers  = pd.read_csv(f"{SB_DIR}/retailer_profiles.csv")
pv         = pd.read_csv(f"{SB_DIR}/product_variations.csv")    # stock + price + pos_connection_id
pi         = pd.read_csv(f"{SB_DIR}/product_inventory.csv")     # stock per location
prods      = pd.read_csv(f"{SB_DIR}/products.csv")              # name, category
locs       = pd.read_csv(f"{SB_DIR}/pos_locations.csv")
ords       = pd.read_csv(f"{SB_DIR}/orders.csv")
oi         = pd.read_csv(f"{SB_DIR}/order_items.csv")

print(f"  pos_connections   : {len(pos_conn)}")
print(f"  retailer_profiles : {len(retailers)}")
print(f"  product_variations: {len(pv)}")
print(f"  product_inventory : {len(pi)}")
print(f"  products          : {len(prods)}")
print(f"  locations         : {len(locs)}")
print(f"  orders            : {len(ords)}")
print(f"  order_items       : {len(oi)}")

# ---------------------------------------------------------------------------
# Step 1 — Active pos_connection_ids
#   pos_connections WHERE is_active = 't' AND retailer_id IN retailer_profiles
# ---------------------------------------------------------------------------
retailer_ids = set(retailers["id"].dropna().astype(str))

active_conn = pos_conn[
    (pos_conn["is_active"] == "t") &
    (pos_conn["retailer_id"].astype(str).isin(retailer_ids))
]["id"].astype(str).unique()

print(f"\nActive pos_connection_ids ({len(active_conn)}):")
for cid in active_conn:
    row = pos_conn[pos_conn["id"] == cid].iloc[0]
    print(f"  {cid}  retailer={row['retailer_id']}  provider={row['provider']}")

# ---------------------------------------------------------------------------
# Step 2 — Active product_variations filtered by active connection
#   product_variations WHERE active = 't' AND pos_connection_id IN active_conn
# ---------------------------------------------------------------------------
pv["active"] = pv["active"].astype(str)
pv_active = pv[
    (pv["active"] == "t") &
    (pv["pos_connection_id"].astype(str).isin(active_conn))
].copy()
pv_active["product_id"] = pv_active["product_id"].astype(str)

print(f"\nActive product_variations: {len(pv_active)}")

# ---------------------------------------------------------------------------
# Step 3 — Products enriched with category
#   Join pv_active → products on product_variations.product_id = products.id
# ---------------------------------------------------------------------------
prods["id"] = prods["id"].astype(str)
prods["category_norm"] = prods["category"].apply(norm_cat)

prod_lookup = prods[["id", "name", "category_norm"]].rename(columns={
    "id": "product_id",
    "name": "product_name",
    "category_norm": "category",
})

pv_enriched = pv_active.merge(prod_lookup, on="product_id", how="left")
pv_enriched["product_name"] = pv_enriched["product_name"].fillna(pv_enriched["name"])
pv_enriched["category"]     = pv_enriched["category"].fillna("general")
pv_enriched["retail_price"] = pd.to_numeric(pv_enriched["price"], errors="coerce").fillna(0)

print(f"Variations with product info: {pv_enriched['product_name'].notna().sum()}")

# ---------------------------------------------------------------------------
# Step 4 — Stock per (product × location)
#   product_inventory WHERE pos_connection_id IN active_conn
#   JOIN product_variations to resolve product_id + price + name
# ---------------------------------------------------------------------------
pi["pos_connection_id"] = pi["pos_connection_id"].astype(str)
pi_active = pi[pi["pos_connection_id"].isin(active_conn)].copy()

# Merge inventory → variation info
stock = pi_active.merge(
    pv_enriched[["id", "product_id", "product_name", "category",
                 "retail_price", "pos_connection_id"]].rename(
        columns={"id": "product_variation_id"}),
    on=["product_variation_id", "pos_connection_id"],
    how="left"
)

# Store name from pos_locations (deduplicated)
loc_lookup = locs[["id", "name"]].drop_duplicates("id").rename(
    columns={"id": "pos_location_id", "name": "store_name"})

# product_inventory.pos_location_id sometimes contains store names or noise
# ('Regular' = corrupt variation name → skip; named stores → create synthetic IDs)
known_loc_ids = set(loc_lookup["pos_location_id"])
SYNTHETIC_STORES = {}  # name → synthetic ID
for loc_val in stock["pos_location_id"].dropna().unique():
    if loc_val not in known_loc_ids:
        # Looks like a real location name (not a UUID-style ID and not 'Regular')
        if not loc_val.startswith(("LF", "LQ")) and loc_val.upper() != "REGULAR":
            slug = loc_val.upper().replace(" ", "_")
            synthetic_id = f"STORE_{slug}"
            SYNTHETIC_STORES[loc_val] = synthetic_id
            new_row = pd.DataFrame([{"pos_location_id": synthetic_id,
                                      "store_name": loc_val}])
            loc_lookup = pd.concat([loc_lookup, new_row], ignore_index=True)
            print(f"  [location] '{loc_val}' not in pos_locations → STORE_{slug}")

# Replace raw location names with synthetic IDs in stock
def resolve_loc_id(v):
    if v in SYNTHETIC_STORES:
        return SYNTHETIC_STORES[v]
    return v

stock["pos_location_id"] = stock["pos_location_id"].apply(resolve_loc_id)

# Drop noise rows ('Regular' rows that aren't real locations)
noise_vals = {"REGULAR", "REGULAR".lower()}
stock = stock[~stock["pos_location_id"].str.upper().isin(noise_vals)]

stock = stock.merge(loc_lookup, on="pos_location_id", how="left")
stock["store_id"] = stock["pos_location_id"]

# Aggregate stock across any connection duplicates
stock_agg = (
    stock[stock["product_id"].notna()]
    .groupby(["store_id", "store_name", "product_id", "product_name",
               "category", "retail_price"], dropna=False)
    .agg(stock_qty=("quantity", "sum"))
    .reset_index()
)

print(f"\nStock rows (product × location): {len(stock_agg)}")
print(f"Unique stores  : {stock_agg['store_id'].nunique()}")
print(f"Unique products: {stock_agg['product_id'].nunique()}")

# ---------------------------------------------------------------------------
# Step 5 — Sales history from orders + order_items (active connections only)
# ---------------------------------------------------------------------------
ords["pos_connection_id"] = ords["pos_connection_id"].fillna("").astype(str)
oi["pos_connection_id"]   = oi["pos_connection_id"].fillna("").astype(str)

# Active orders (by connection)
ords_active = ords[ords["pos_connection_id"].isin(active_conn)].copy()
ords_active["order_time"] = pd.to_datetime(
    ords_active["order_time"], format="mixed", utc=True)

print(f"\nActive orders         : {len(ords_active)}")

# Join order_items to active orders
oi_active = oi[oi["pos_connection_id"].isin(active_conn)].copy()
sales = oi_active.merge(
    ords_active[["id", "order_time", "pos_connection_id",
                 "external_location_id"]].rename(
        columns={"id": "order_id_x", "pos_connection_id": "order_conn"}),
    left_on="order_id", right_on="order_id_x", how="inner"
)
print(f"Active order_items    : {len(sales)}")

# Resolve store_id for orders via two strategies (in priority order):
#   1. orders.pos_connection_id → primary location from product_inventory for that connection
#   2. external_location_id name → loc_lookup (fallback)
#
# Build connection → primary location mapping from product_inventory
conn_to_loc = (
    pi[pi["pos_connection_id"].isin(active_conn)]
    .groupby("pos_connection_id")["pos_location_id"]
    .agg(lambda x: x.mode()[0] if len(x) > 0 else None)  # most common location per connection
    .to_dict()
)
# Replace any raw location names with their synthetic IDs
for conn, loc_val in conn_to_loc.items():
    if loc_val and loc_val in SYNTHETIC_STORES:
        conn_to_loc[conn] = SYNTHETIC_STORES[loc_val]
print(f"  Connection → location map: {conn_to_loc}")

# Apply: prefer connection-based resolution
sales["store_id"] = sales["order_conn"].map(conn_to_loc)

# Fallback: external_location_id name match for any still-null
name_to_locid = loc_lookup.set_index("store_name")["pos_location_id"].to_dict()
mask_null = sales["store_id"].isna()
if mask_null.any():
    sales.loc[mask_null, "store_id"] = (
        sales.loc[mask_null, "external_location_id"].map(name_to_locid)
    )

# Map order_items → products:
#   order_items.item_name == products.name
#   WHERE products.id == product_variations.product_id
prod_name_lower = (
    prods[["id", "name"]]
    .assign(name_lower=prods["name"].str.lower().str.strip())
    .drop_duplicates("name_lower")
    .set_index("name_lower")["id"]
    .to_dict()
)
sales["product_id"] = (
    sales["item_name"].str.lower().str.strip().map(prod_name_lower)
)

# Keep only rows where both store and product resolved
sales = sales.dropna(subset=["store_id", "product_id"])
sales["quantity"] = pd.to_numeric(sales["quantity"], errors="coerce").fillna(0)

print(f"Sales with resolved store+product: {len(sales)}")

# Split recent vs historical
recent_mask = sales["order_time"] >= D30

def agg_sales(df, prefix):
    if df.empty:
        return pd.DataFrame(columns=["store_id", "product_id",
            f"{prefix}_qty", f"{prefix}_txns", f"{prefix}_avg", f"{prefix}_std"])
    g = df.groupby(["store_id", "product_id"])["quantity"]
    return pd.DataFrame({
        f"{prefix}_qty":  g.sum(),
        f"{prefix}_txns": g.count(),
        f"{prefix}_avg":  g.mean().round(4),
        f"{prefix}_std":  g.std().fillna(0).round(4),
    }).reset_index()

recent_agg = agg_sales(sales[recent_mask],  "recent")
hist_agg   = agg_sales(sales[~recent_mask], "historical")

total_agg = (
    sales.groupby(["store_id", "product_id"])
    .agg(total_sold=("quantity", "sum"),
         num_sales=("quantity", "count"),
         last_sale_ts=("order_time", "max"))
    .reset_index()
)
store_txns = (
    sales.groupby("store_id")["quantity"].count()
    .reset_index().rename(columns={"quantity": "store_total_txns"})
)

print(f"  Recent  ({D30.date()} → now): {len(sales[recent_mask])} line items")
print(f"  Hist    (before {D30.date()}): {len(sales[~recent_mask])} line items")

# ---------------------------------------------------------------------------
# Step 6 — Merge everything into ml_inventory
# ---------------------------------------------------------------------------
ml = stock_agg.copy()
ml = ml.merge(recent_agg, on=["store_id", "product_id"], how="left")
ml = ml.merge(hist_agg[["store_id","product_id","historical_qty",
                          "historical_txns","historical_avg"]],
              on=["store_id","product_id"], how="left")
ml = ml.merge(total_agg, on=["store_id","product_id"], how="left")
ml = ml.merge(store_txns, on="store_id", how="left")

ml["last_sale_ts"] = pd.to_datetime(ml["last_sale_ts"], utc=True, errors="coerce")
ml["days_since_last_sale"] = (
    (NOW - ml["last_sale_ts"]).dt.total_seconds() / 86400
).clip(lower=0).fillna(999).round(1)

num_cols = ["recent_qty","recent_txns","recent_avg","recent_std",
            "historical_qty","historical_txns","historical_avg",
            "total_sold","num_sales","store_total_txns"]
ml[num_cols] = ml[num_cols].fillna(0)

out_cols = [
    "store_id", "product_id", "store_name", "product_name", "category",
    "stock_qty", "retail_price",
    "recent_qty", "recent_txns", "recent_avg", "recent_std",
    "historical_qty", "historical_txns", "historical_avg",
    "total_sold", "num_sales", "days_since_last_sale", "store_total_txns",
]
ml = ml[out_cols]

print(f"\n{'='*60}")
print(f"  FINAL ml_inventory: {len(ml)} rows")
print(f"  Stores            : {ml['store_id'].nunique()}")
print(f"  Categories        : {ml['category'].value_counts().to_dict()}")
print(f"  With any sales    : {(ml['total_sold']>0).sum()}")
print(f"  With recent sales : {(ml['recent_qty']>0).sum()}")
print(f"  Zero stock        : {(ml['stock_qty']==0).sum()}")
print(f"{'='*60}")
print(ml[["store_name","product_name","category","stock_qty",
          "retail_price","recent_qty","total_sold","days_since_last_sale"]]
      .head(12).to_string(index=False))

# ---------------------------------------------------------------------------
# Step 7 — Save locally
# ---------------------------------------------------------------------------
out_csv = os.path.join(OUT_DIR, "ml_inventory.csv")
ml.to_csv(out_csv, index=False)
print(f"\nSaved → {out_csv}")

# SQL for Supabase table creation
sql = """-- Run in Supabase SQL editor before first --push
create table if not exists ml_inventory (
  store_id              text not null,
  product_id            text not null,
  store_name            text,
  product_name          text,
  category              text,
  stock_qty             float8 default 0,
  retail_price          float8 default 0,
  recent_qty            float8 default 0,
  recent_txns           float8 default 0,
  recent_avg            float8 default 0,
  recent_std            float8 default 0,
  historical_qty        float8 default 0,
  historical_txns       float8 default 0,
  historical_avg        float8 default 0,
  total_sold            float8 default 0,
  num_sales             float8 default 0,
  days_since_last_sale  float8 default 0,
  store_total_txns      float8 default 0,
  updated_at            timestamptz default now(),
  primary key (store_id, product_id)
);

create table if not exists ml_triggers (
  id             uuid primary key default gen_random_uuid(),
  status         text not null default 'pending',
  trigger_type   text not null default 'recommend',
  filter_store   text,
  filter_product text,
  created_at     timestamptz default now(),
  completed_at   timestamptz,
  error_msg      text,
  result_file    text
);

-- Fire a run after ml_inventory is populated:
-- insert into ml_triggers (status, trigger_type) values ('pending', 'recommend');
"""
sql_path = os.path.join(OUT_DIR, "create_ml_tables.sql")
with open(sql_path, "w") as f:
    f.write(sql)
print(f"Saved → {sql_path}")

# ---------------------------------------------------------------------------
# Step 8 — Optionally push to Supabase
# ---------------------------------------------------------------------------
def push_to_supabase(df):
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from supabase_watcher import SUPABASE_URL, SUPABASE_KEY
    from supabase import create_client

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    records = df.to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if isinstance(v, float) and not pd.isna(v):
                r[k] = round(v, 4)
            elif pd.isna(v) if not isinstance(v, (str, bool)) else False:
                r[k] = None

    batch, total, pushed = 100, len(records), 0
    for i in range(0, total, batch):
        client.table("ml_inventory").upsert(
            records[i:i+batch], on_conflict="store_id,product_id"
        ).execute()
        pushed += len(records[i:i+batch])
        print(f"  Pushed {pushed}/{total}…", end="\r")
    print(f"\nPushed {pushed} rows → Supabase ml_inventory")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--push", action="store_true",
                        help="Upload to Supabase ml_inventory table")
    args = parser.parse_args()
    if args.push:
        print("\nPushing to Supabase…")
        push_to_supabase(ml)
    else:
        print("\nRun with --push to upload to Supabase.")
