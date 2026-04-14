"""
stress_test.py — 30-minute continuous API test with randomised store/product data.

Runs repeated /recommend calls with varied scenarios, saves every output to
test_output/, prints a live scoreboard, and writes a final summary report.

Usage:
    python stress_test.py              # 30-minute run
    python stress_test.py --mins 5    # shorter run for quick check
"""

import argparse
import csv
import json
import os
import random
import time
from datetime import datetime

import requests

API     = "http://localhost:8001"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "..", "test_output")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Scenario catalogue — each entry is a profile the random generator uses
# ---------------------------------------------------------------------------
STORES = [
    "STORE_DUBAI_MALL", "STORE_ABU_DHABI_1", "STORE_SHARJAH_CENTRAL",
    "STORE_JBR",        "STORE_DEIRA",        "STORE_MARINA",
    "STORE_MIRDIF",     "STORE_AL_AIN",       "STORE_FUJAIRAH",
    "STORE_RAK",
]

PRODUCTS = [
    ("MILK_FULL_CREAM",   "Full Cream Milk 1L",        "dairy",     4.50),
    ("MILK_SKIM",         "Skimmed Milk 1L",            "dairy",     4.25),
    ("ORANGE_JUICE_1L",   "Orange Juice 1L",            "beverages", 8.90),
    ("APPLE_JUICE_2L",    "Apple Juice 2L",             "beverages", 12.50),
    ("COCA_COLA_6PK",     "Coca Cola 6-Pack",           "beverages", 22.00),
    ("WATER_500ML",       "Mineral Water 500ml",        "beverages", 2.00),
    ("BREAD_WHITE",       "White Bread Loaf",           "bakery",    6.50),
    ("CROISSANT_BUTTER",  "Butter Croissant",           "bakery",    4.00),
    ("CHICKEN_BREAST",    "Chicken Breast 1kg",         "meat",      32.00),
    ("BEEF_MINCE",        "Beef Mince 500g",            "meat",      28.50),
    ("TOMATOES_KG",       "Fresh Tomatoes 1kg",         "produce",   5.50),
    ("BANANA_KG",         "Bananas 1kg",                "produce",   4.00),
    ("CHEDDAR_200G",      "Cheddar Cheese 200g",        "dairy",     14.75),
    ("YOGURT_PLAIN",      "Plain Yogurt 500g",          "dairy",     7.25),
    ("CHIPS_LAYS",        "Lays Chips 150g",            "snacks",    6.50),
    ("CHOCOLATE_BAR",     "Chocolate Bar 100g",         "snacks",    5.00),
    ("RICE_BASMATI_5KG",  "Basmati Rice 5kg",           "pantry",    38.00),
    ("PASTA_500G",        "Penne Pasta 500g",           "pantry",    7.50),
    ("OLIVE_OIL_1L",      "Extra Virgin Olive Oil 1L",  "pantry",    42.00),
    ("DETERGENT_2L",      "Laundry Detergent 2L",       "household", 28.00),
    ("SHAMPOO_400ML",     "Shampoo 400ml",              "household", 22.50),
    ("FROZEN_PIZZA",      "Frozen Pizza Margherita",    "frozen",    35.00),
    ("ICE_CREAM_1L",      "Vanilla Ice Cream 1L",       "frozen",    24.00),
    ("TUNA_CAN",          "Tuna in Brine 185g",         "pantry",    8.50),
    ("EGGS_12PK",         "Free Range Eggs x12",        "dairy",     19.00),
]

SCENARIOS = {
    # name: (stock_multiplier, recent_demand_mult, days_since, label_hint)
    "dead_stock":       (15.0, 0.0,  120, "Dead"),
    "slow_mover":       (5.0,  0.3,  10,  "Slow"),
    "low_stock":        (0.3,  1.0,  1,   "Low"),
    "stockout":         (0.0,  1.0,  0,   "Low"),
    "excess_healthy":   (3.0,  1.0,  1,   "Excess"),
    "optimum":          (1.5,  1.0,  1,   "Optimum"),
    "high_velocity":    (0.8,  2.5,  0,   "Low"),
    "premium_slow":     (8.0,  0.15, 5,   "Dead"),
    "new_product":      (2.0,  0.0,  0,   "Optimum"),
    "clearance":        (4.5,  0.8,  2,   "Slow"),
}

# ---------------------------------------------------------------------------
# Data generator
# ---------------------------------------------------------------------------

def make_product(store_id, pid, pname, cat, price, scenario_name, store_txns):
    sc       = SCENARIOS[scenario_name]
    base_dem = random.randint(50, 800)          # base 30d demand units
    stock    = max(0, round(base_dem * sc[0] * random.uniform(0.8, 1.2)))
    r_dem    = round(base_dem * sc[1] * random.uniform(0.7, 1.3))
    r_txns   = max(0, round(r_dem / random.uniform(1.0, 3.0)))
    r_avg    = round(r_dem / max(r_txns, 1), 2)
    r_std    = round(r_avg * random.uniform(0.0, 0.4), 2)
    h_dem    = round(base_dem * random.uniform(3, 8))
    h_txns   = max(0, round(h_dem / random.uniform(1.0, 3.0)))
    h_avg    = round(h_dem / max(h_txns, 1), 2)

    return {
        "store_id":             store_id,
        "product_id":           pid,
        "product_name":         f"{pname} [{scenario_name}]",
        "category":             cat,
        "stock_qty":            float(stock),
        "retail_price":         price,
        "recent_qty":           float(r_dem),
        "recent_txns":          float(r_txns),
        "recent_avg":           r_avg,
        "recent_std":           r_std,
        "historical_qty":       float(h_dem),
        "historical_txns":      float(h_txns),
        "historical_avg":       h_avg,
        "total_sold":           float(r_dem + h_dem),
        "num_sales":            float(r_txns + h_txns),
        "days_since_last_sale": float(sc[2] + random.randint(0, 5)),
        "store_total_txns":     float(store_txns),
    }


def generate_batch(n_stores=4, n_products_per_store=15):
    """Build one randomised batch across n_stores."""
    stores  = random.sample(STORES, k=min(n_stores, len(STORES)))
    all_prods = random.sample(PRODUCTS, k=min(n_products_per_store, len(PRODUCTS)))
    products  = []
    store_txns = {s: random.randint(100_000, 900_000) for s in stores}

    for store in stores:
        for pid, pname, cat, price in all_prods:
            scenario = random.choice(list(SCENARIOS.keys()))
            products.append(make_product(
                store, pid, pname, cat, price, scenario, store_txns[store]
            ))
    return products


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_predictions(path, predictions):
    fields = ["store_id","product_id","product_name","prediction","confidence",
              "prob_dead","prob_excess","prob_low","prob_optimum","prob_slow"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for p in predictions:
            probs = p.get("probabilities", {})
            w.writerow({
                "store_id": p["store_id"], "product_id": p["product_id"],
                "product_name": p.get("product_name",""),
                "prediction": p["prediction"],
                "confidence": round(p["confidence"], 4),
                "prob_dead":    round(probs.get("Dead",0),4),
                "prob_excess":  round(probs.get("Excess",0),4),
                "prob_low":     round(probs.get("Low",0),4),
                "prob_optimum": round(probs.get("Optimum",0),4),
                "prob_slow":    round(probs.get("Slow",0),4),
            })


def write_csv(path, records):
    if not records:
        open(path, "w").close()
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        w.writeheader(); w.writerows(records)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(duration_mins):
    end_time   = time.time() + duration_mins * 60
    run_num    = 0
    total_pred = 0
    total_tran = 0
    total_rest = 0
    errors     = 0
    label_tally = {"Dead":0,"Slow":0,"Low":0,"Excess":0,"Optimum":0}
    run_log    = []

    print(f"\n{'='*60}")
    print(f"  JIRAN ML — STRESS TEST  ({duration_mins} min)")
    print(f"  API : {API}")
    print(f"  OUT : {OUT_DIR}")
    print(f"{'='*60}\n")

    while time.time() < end_time:
        run_num += 1
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        # randomise batch size each run
        n_stores = random.randint(2, 6)
        n_prods  = random.randint(8, len(PRODUCTS))
        products = generate_batch(n_stores, n_prods)

        try:
            t0   = time.time()
            resp = requests.post(f"{API}/recommend",
                                 json={"products": products}, timeout=30)
            resp.raise_for_status()
            elapsed = round(time.time() - t0, 2)
            result  = resp.json()
        except Exception as e:
            errors += 1
            print(f"  [run {run_num:03d}] ERROR: {e}")
            time.sleep(2)
            continue

        predictions = result.get("predictions") or result.get("results") or []
        transfers   = result.get("transfers", [])
        restocks    = result.get("restocks", [])
        summary     = result.get("summary", {})

        # tally
        for p in predictions:
            label_tally[p["prediction"]] = label_tally.get(p["prediction"],0) + 1
        total_pred += len(predictions)
        total_tran += len(transfers)
        total_rest += len(restocks)

        # save outputs
        prefix = f"{ts}_run{run_num:03d}"
        write_predictions(f"{OUT_DIR}/{prefix}_predictions.csv", predictions)
        write_csv(f"{OUT_DIR}/{prefix}_transfers.csv",  transfers)
        write_csv(f"{OUT_DIR}/{prefix}_restocks.csv",   restocks)
        with open(f"{OUT_DIR}/{prefix}_summary.json","w") as f:
            json.dump(summary, f, indent=2)

        run_log.append({
            "run": run_num, "timestamp": ts,
            "stores": n_stores, "products_sent": len(products),
            "predictions": len(predictions), "transfers": len(transfers),
            "restocks": len(restocks), "latency_s": elapsed,
        })

        remaining = max(0, int(end_time - time.time()))
        lc = summary.get("label_counts", {})
        print(f"  [{run_num:03d}] {elapsed:4.1f}s | "
              f"{len(products):3d} products | "
              f"T:{len(transfers)} R:{len(restocks)} | "
              f"Dead={lc.get('Dead',0)} Slow={lc.get('Slow',0)} "
              f"Low={lc.get('Low',0)} Excess={lc.get('Excess',0)} "
              f"Opt={lc.get('Optimum',0)} | "
              f"{remaining//60}m{remaining%60:02d}s left")

        # small gap between runs
        time.sleep(random.uniform(1, 4))

    # ── Final report ──────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  FINAL REPORT  ({run_num} runs, {duration_mins} min)")
    print(f"{'='*60}")
    print(f"  Total predictions : {total_pred}")
    print(f"  Total transfers   : {total_tran}")
    print(f"  Total restocks    : {total_rest}")
    print(f"  Errors            : {errors}")
    print(f"\n  Label distribution:")
    for label, n in sorted(label_tally.items(), key=lambda x: -x[1]):
        pct = n / max(total_pred, 1) * 100
        bar = "█" * int(pct / 2)
        print(f"    {label:<8}: {n:5d} ({pct:4.1f}%)  {bar}")

    avg_lat = sum(r["latency_s"] for r in run_log) / max(len(run_log),1)
    print(f"\n  Avg latency : {avg_lat:.2f}s per run")
    print(f"  Output dir  : {OUT_DIR}")

    # save run log
    log_path = os.path.join(OUT_DIR, f"stress_test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    with open(log_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(run_log[0].keys()))
        w.writeheader(); w.writerows(run_log)
    print(f"  Run log     : {os.path.basename(log_path)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mins", type=int, default=30)
    args = parser.parse_args()
    run(args.mins)
