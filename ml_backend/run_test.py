"""
run_test.py — Validation test using real product/store IDs from training data.

Product: COMMON00041 (produce, retail 24.13 AED)
Known Prophet forecasts (forecast_30d):
  store_AE: 2055  → stock 8000  → coverage 3.89x → EXCESS  (transfer donor)
  store_AD: 2441  → stock 500   → coverage 0.20x → LOW     (transfer recipient)
  store_AC: 1251  → stock 1388  → coverage 1.11x → OPTIMUM
  store_AA:  699  → stock 3913  → coverage 5.60x → SLOW
  store_AF:  635  → stock 5000  → coverage 7.87x → DEAD

Filler products use real IDs too, testing other categories/edge cases.
"""

import sys
import requests

API = "http://localhost:8001"

products = [

    # ── TRANSFER SCENARIO: COMMON00041 across 5 real stores ──────────────────

    {   # store_AE — EXCESS: 8000 units vs ~2056/30d demand → ~3.9x coverage
        "store_id": "store_AE", "product_id": "COMMON00041",
        "product_name": "COMMON00041 [store_AE — expect EXCESS → donor]",
        "category": "produce",
        "stock_qty": 8000,
        "retail_price": 24.13,
        "recent_qty": 1989, "recent_txns": 1989, "recent_avg": 1.0, "recent_std": 0.0,
        "historical_qty": 10382, "historical_txns": 10382, "historical_avg": 1.0,
        "total_sold": 12371, "num_sales": 12371,
        "days_since_last_sale": 0,
        "store_total_txns": 620440,
    },
    {   # store_AD — LOW: only 500 units vs ~2441/30d demand → 0.20x coverage, stockout imminent
        "store_id": "store_AD", "product_id": "COMMON00041",
        "product_name": "COMMON00041 [store_AD — expect LOW → recipient]",
        "category": "produce",
        "stock_qty": 500,
        "retail_price": 24.13,
        "recent_qty": 2357, "recent_txns": 2357, "recent_avg": 1.0, "recent_std": 0.0,
        "historical_qty": 12685, "historical_txns": 12685, "historical_avg": 1.0,
        "total_sold": 15042, "num_sales": 15042,
        "days_since_last_sale": 0,
        "store_total_txns": 825062,
    },
    {   # store_AC — OPTIMUM: real stock 1388 vs 1251/30d → 1.11x coverage
        "store_id": "store_AC", "product_id": "COMMON00041",
        "product_name": "COMMON00041 [store_AC — expect OPTIMUM]",
        "category": "produce",
        "stock_qty": 1388,
        "retail_price": 24.13,
        "recent_qty": 1169, "recent_txns": 1169, "recent_avg": 1.0, "recent_std": 0.0,
        "historical_qty": 5951, "historical_txns": 5951, "historical_avg": 1.0,
        "total_sold": 7120, "num_sales": 7120,
        "days_since_last_sale": 0,
        "store_total_txns": 637476,
    },
    {   # store_AA — SLOW: real stock 3913 vs 699/30d → 5.6x coverage, ~167 days of stock
        "store_id": "store_AA", "product_id": "COMMON00041",
        "product_name": "COMMON00041 [store_AA — expect SLOW]",
        "category": "produce",
        "stock_qty": 3913,
        "retail_price": 24.13,
        "recent_qty": 776, "recent_txns": 776, "recent_avg": 1.0, "recent_std": 0.0,
        "historical_qty": 4159, "historical_txns": 4159, "historical_avg": 1.0,
        "total_sold": 4935, "num_sales": 4935,
        "days_since_last_sale": 0,
        "store_total_txns": 754570,
    },
    {   # store_AF — DEAD: large stock, no recent activity, 5000 vs 635/30d → 7.9x coverage
        "store_id": "store_AF", "product_id": "COMMON00041",
        "product_name": "COMMON00041 [store_AF — expect DEAD]",
        "category": "produce",
        "stock_qty": 5000,
        "retail_price": 24.13,
        "recent_qty": 0, "recent_txns": 0, "recent_avg": 0.0, "recent_std": 0.0,
        "historical_qty": 4570, "historical_txns": 4570, "historical_avg": 1.0,
        "total_sold": 5343, "num_sales": 5343,
        "days_since_last_sale": 95,
        "store_total_txns": 579643,
    },

    # ── FILLER: other products / edge cases ───────────────────────────────────

    {   # Different product, real store — healthy optimum
        "store_id": "store_AB", "product_id": "COMMON00039",
        "product_name": "COMMON00039 [store_AB — filler, expect OPTIMUM/LOW]",
        "category": "snacks",
        "stock_qty": 900,
        "retail_price": 8.50,
        "recent_qty": 600, "recent_txns": 300, "recent_avg": 2.0, "recent_std": 0.5,
        "historical_qty": 2400, "historical_txns": 1200, "historical_avg": 2.0,
        "total_sold": 3000, "num_sales": 1500,
        "days_since_last_sale": 1,
        "store_total_txns": 579643,
    },
    {   # Unknown category — should still return a valid prediction
        "store_id": "store_AC", "product_id": "COMMON00017",
        "product_name": "COMMON00017 [store_AC — unknown category edge case]",
        "category": "new_category_xyz",
        "stock_qty": 200,
        "retail_price": 12.00,
        "recent_qty": 100, "recent_txns": 50, "recent_avg": 2.0, "recent_std": 0.4,
        "historical_qty": 400, "historical_txns": 200, "historical_avg": 2.0,
        "total_sold": 500, "num_sales": 250,
        "days_since_last_sale": 2,
        "store_total_txns": 637476,
    },
    {   # Zero stock — hard stockout
        "store_id": "store_AA", "product_id": "COMMON00053",
        "product_name": "COMMON00053 [store_AA — zero stock edge case]",
        "category": "beverages",
        "stock_qty": 0,
        "retail_price": 6.00,
        "recent_qty": 150, "recent_txns": 75, "recent_avg": 2.0, "recent_std": 0.3,
        "historical_qty": 600, "historical_txns": 300, "historical_avg": 2.0,
        "total_sold": 750, "num_sales": 375,
        "days_since_last_sale": 0,
        "store_total_txns": 754570,
    },
    {   # Cold start — brand new, no history
        "store_id": "store_AD", "product_id": "COMMON00046",
        "product_name": "COMMON00046 [store_AD — cold start, all zeros]",
        "category": "dairy",
        "stock_qty": 50,
        "retail_price": 5.50,
        "recent_qty": 0, "recent_txns": 0, "recent_avg": 0.0, "recent_std": 0.0,
        "historical_qty": 0, "historical_txns": 0, "historical_avg": 0.0,
        "total_sold": 0, "num_sales": 0,
        "days_since_last_sale": 0,
        "store_total_txns": 825062,
    },
    {   # Premium item, slow sales
        "store_id": "store_AE", "product_id": "COMMON00006",
        "product_name": "COMMON00006 [store_AE — premium, slow sales]",
        "category": "beverages",
        "stock_qty": 400,
        "retail_price": 28.00,
        "recent_qty": 10, "recent_txns": 10, "recent_avg": 1.0, "recent_std": 0.0,
        "historical_qty": 40, "historical_txns": 40, "historical_avg": 1.0,
        "total_sold": 50, "num_sales": 50,
        "days_since_last_sale": 5,
        "store_total_txns": 620440,
    },
]

# ─────────────────────────────────────────────────────────────
# Call API
# ─────────────────────────────────────────────────────────────

print(f"\n{'='*68}")
print(f"  JIRAN ML API TEST — 37-feature model (no wholesale_price)")
print(f"  Using real product/store IDs from training data")
print(f"{'='*68}")
print(f"  Sending {len(products)} products to {API}/predict-stock\n")

try:
    resp = requests.post(f"{API}/predict-stock", json={"products": products}, timeout=30)
    resp.raise_for_status()
except Exception as e:
    print(f"  ERROR: {e}")
    sys.exit(1)

data = resp.json()
results = data["results"]

# ─────────────────────────────────────────────────────────────
# Print results
# ─────────────────────────────────────────────────────────────

LABEL_ICON = {
    "Low":     "⚠️  LOW    ",
    "Optimum": "✅ OPTIMUM",
    "Excess":  "📦 EXCESS ",
    "Slow":    "🐢 SLOW   ",
    "Dead":    "💀 DEAD   ",
}

print(f"  {'Product':<48} {'Label':<12} {'Conf':>6}")
print(f"  {'-'*68}")
for r in results:
    icon = LABEL_ICON.get(r["prediction"], r["prediction"])
    print(f"  {r['product_name']:<48} {icon}  {r['confidence']:.0%}")

# ─────────────────────────────────────────────────────────────
# Transfer recommendation
# ─────────────────────────────────────────────────────────────

print(f"\n{'='*68}")
print(f"  TRANSFER ANALYSIS — COMMON00041 across 5 stores")
print(f"{'='*68}")

target_pid = "COMMON00041"
target_results = {r["store_id"]: r for r in results if r["product_id"] == target_pid}
excess_stores = [(s, r) for s, r in target_results.items() if r["prediction"] == "Excess"]
low_stores    = [(s, r) for s, r in target_results.items() if r["prediction"] == "Low"]

if excess_stores and low_stores:
    for (src, sr) in excess_stores:
        for (dst, dr) in low_stores:
            print(f"\n  ✅ TRANSFER RECOMMENDED:")
            print(f"     FROM : {src}  →  {sr['prediction']} (conf {sr['confidence']:.0%})")
            print(f"     TO   : {dst}  →  {dr['prediction']} (conf {dr['confidence']:.0%})")
            print(f"     Product: COMMON00041 (produce, AED 24.13)")
else:
    print("\n  Transfer pair not detected with current thresholds.")

print(f"\n  COMMON00041 status per store:")
expected = {"store_AE":"EXCESS","store_AD":"LOW","store_AC":"OPTIMUM","store_AA":"SLOW","store_AF":"DEAD"}
all_match = True
for store in ["store_AE","store_AD","store_AC","store_AA","store_AF"]:
    r = target_results.get(store)
    if r:
        icon = LABEL_ICON.get(r["prediction"], r["prediction"])
        exp = expected[store]
        match = "✓" if r["prediction"].upper() == exp else "✗"
        print(f"    {store}: {icon}  conf {r['confidence']:.0%}  [expected {exp}] {match}")
        if r["prediction"].upper() != exp:
            all_match = False

# ─────────────────────────────────────────────────────────────
# Filler product results
# ─────────────────────────────────────────────────────────────

print(f"\n{'='*68}")
print(f"  FILLER / EDGE CASE RESULTS")
print(f"{'='*68}")
for r in results:
    if r["product_id"] != target_pid:
        icon = LABEL_ICON.get(r["prediction"], r["prediction"])
        print(f"  {r['product_name'][:52]:<52} {icon}  {r['confidence']:.0%}")

# ─────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────

label_counts = {}
for r in results:
    label_counts[r["prediction"]] = label_counts.get(r["prediction"], 0) + 1

print(f"\n{'='*68}")
print(f"  SUMMARY")
print(f"{'='*68}")
print(f"  Total predictions : {len(results)}")
print(f"  Label breakdown   : {label_counts}")
print(f"  Transfer labels OK: {'✅ YES' if excess_stores and low_stores else '❌ NO — check model coverage'}")
print(f"  All match expected: {'✅ YES' if all_match else '⚠️  PARTIAL — see above'}")
print(f"  Model features    : 37 (no wholesale_price, expiry_date, unit_quantity)")
print(f"{'='*68}\n")
