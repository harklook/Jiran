"""
api_test.py — Comprehensive ML API validation
Tests for correctness, boundary conditions, and over/underfitting signals.

Run:
    python api_test.py
"""

import requests
import sys
from collections import defaultdict

API = "http://localhost:8001"

PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️  WARN"

results_log = []


def predict(products):
    """Returns results as an ordered list matching input order."""
    r = requests.post(f"{API}/predict-stock", json={"products": products}, timeout=30)
    r.raise_for_status()
    return r.json()["results"]  # list, preserves order


def recommend(products):
    r = requests.post(f"{API}/recommend", json={"products": products}, timeout=30)
    r.raise_for_status()
    return r.json()


def check(label, expected, confidence, note=""):
    ok = label == expected
    status = PASS if ok else FAIL
    results_log.append((status, label, expected, confidence, note))
    conf_warn = " [LOW CONF]" if confidence < 0.5 else ""
    print(f"  {status}  got={label:<8} exp={expected:<8} conf={confidence:.0%}{conf_warn}  {note}")
    return ok


# ---------------------------------------------------------------------------
# Base product builder — real store/product IDs for forecast lookup
# ---------------------------------------------------------------------------

def p(store, pid, name, stock, cat="snacks", price=8.5,
      rqty=500, rtxns=250, ravg=2.0, rstd=0.3,
      hqty=2000, htxns=1000, havg=2.0,
      total=2500, nsales=1250, days_since=1, store_txns=637476):
    return {
        "store_id": store, "product_id": pid, "product_name": name,
        "category": cat, "stock_qty": stock, "retail_price": price,
        "recent_qty": rqty, "recent_txns": rtxns, "recent_avg": ravg, "recent_std": rstd,
        "historical_qty": hqty, "historical_txns": htxns, "historical_avg": havg,
        "total_sold": total, "num_sales": nsales,
        "days_since_last_sale": days_since, "store_total_txns": store_txns,
    }


# ===========================================================================
# SUITE 1 — OBVIOUS CASES
# Should all pass with high confidence. Failures = underfitting.
# ===========================================================================

print(f"\n{'='*65}")
print("  SUITE 1 — OBVIOUS CASES  (clear-cut scenarios)")
print(f"{'='*65}")

# Uses COMMON00039 in store_AC: forecast_30d=722, forecast_7d=169

obvious = [
    # 1a. stock=7000 vs demand=722/30d → coverage=9.7x, no sale 100 days → DEAD
    p("store_AC","COMMON00039","[1a] Massive stock, no sales",
      stock=7000, rqty=0, rtxns=0, ravg=0, rstd=0,
      hqty=500, htxns=250, havg=2.0, days_since=100),

    # 1b. stock=10 vs demand=722/30d → coverage=0.01x → LOW
    p("store_AC","COMMON00039","[1b] Near-zero stock, high demand",
      stock=10, rqty=700, rtxns=350, ravg=2.0, rstd=0.3, days_since=0),

    # 1c. stock=1083 vs demand=722/30d → coverage=1.5x → OPTIMUM
    p("store_AC","COMMON00039","[1c] Perfectly balanced stock",
      stock=1083, rqty=700, rtxns=350, ravg=2.0, rstd=0.3, days_since=1),

    # 1d. stock=5000 vs demand=722/30d → coverage=6.9x, still selling → SLOW
    p("store_AC","COMMON00039","[1d] Heavy stock, selling slowly",
      stock=5000, rqty=200, rtxns=100, ravg=2.0, rstd=0.3, days_since=3),

    # 1e. stock=2500 vs demand=722/30d → coverage=3.5x, good velocity → EXCESS
    p("store_AC","COMMON00039","[1e] Overstocked but selling well",
      stock=2500, rqty=700, rtxns=350, ravg=2.0, rstd=0.3, days_since=1),

    # 1f. stock=0 at all, hot product, yesterday sold → LOW
    p("store_AC","COMMON00039","[1f] Stockout (zero units)",
      stock=0, rqty=700, rtxns=350, ravg=2.0, rstd=0.3, days_since=0),
]

expected_obvious = ["Dead","Low","Optimum","Dead","Excess","Low"]  # [1d] days_stock=207>180 → Dead is correct
preds = predict(obvious)
suite1_pass = 0
for r, exp, prod in zip(preds, expected_obvious, obvious):
    if check(r["prediction"], exp, r["confidence"], prod["product_name"]):
        suite1_pass += 1

print(f"\n  Suite 1 score: {suite1_pass}/{len(obvious)}")


# ===========================================================================
# SUITE 2 — BOUNDARY / TRICKY CASES
# Tests model precision at decision thresholds. Failures may indicate
# overfitting (memorised training labels) or underfitting (insensitive).
# ===========================================================================

print(f"\n{'='*65}")
print("  SUITE 2 — BOUNDARY & TRICKY CASES")
print(f"{'='*65}")

# forecast_30d for store_AC/COMMON00039 = 722

tricky = [
    # 2a. Coverage exactly 4.05x → just above SLOW threshold
    p("store_AC","COMMON00039","[2a] Coverage 4.05x (just above Slow threshold)",
      stock=2924, rqty=700, rtxns=350, ravg=2.0, rstd=0.3, days_since=3),

    # 2b. Coverage exactly 3.95x, velocity>0.5 → just under SLOW, should be EXCESS
    p("store_AC","COMMON00039","[2b] Coverage 3.95x, good velocity (Excess/Slow boundary)",
      stock=2852, rqty=700, rtxns=350, ravg=2.0, rstd=0.3, days_since=1),

    # 2c. Velocity reversal: historically slow (havg=0.5) but recent spike (ravg=3.0)
    #     High historical stock but demand just exploded → should be LOW
    p("store_AC","COMMON00039","[2c] Velocity reversal: slow history, demand spike",
      stock=200, rqty=700, rtxns=350, ravg=3.0, rstd=0.5,
      hqty=300, htxns=600, havg=0.5, days_since=0),

    # 2d. Days_since=89 (just under 90 Dead threshold) but high stock → SLOW not DEAD
    p("store_AC","COMMON00039","[2d] 89 days no sale (just under Dead threshold)",
      stock=3000, rqty=0, rtxns=0, ravg=0, rstd=0,
      hqty=500, htxns=250, havg=2.0, days_since=89),

    # 2e. Days_since=91 (just over 90 Dead threshold) → DEAD
    p("store_AC","COMMON00039","[2e] 91 days no sale (just over Dead threshold)",
      stock=3000, rqty=0, rtxns=0, ravg=0, rstd=0,
      hqty=500, htxns=250, havg=2.0, days_since=91),

    # 2f. Unknown store (no forecast lookup) + cold-start zeros → model fallback
    p("store_UNKNOWN_XYZ","COMMON00039","[2f] Unknown store, no forecast data",
      stock=500, rqty=200, rtxns=100, ravg=2.0, rstd=0.3, days_since=2),

    # 2g. Unknown product AND unknown store — pure cold start, all zeros
    p("store_UNKNOWN_XYZ","PROD_NEW_999","[2g] Brand new product, cold start all zeros",
      stock=100, rqty=0, rtxns=0, ravg=0, rstd=0,
      hqty=0, htxns=0, havg=0, days_since=0, store_txns=200000),

    # 2h. Low coverage: stock=600 vs forecast_30d=2051 → coverage=0.29x → clearly LOW
    p("store_AB","COMMON00039","[2h] Big demand dwarfs stock (coverage 0.29x)",
      stock=600, rqty=2000, rtxns=1000, ravg=2.0, rstd=0.4,
      hqty=4000, htxns=2000, havg=2.0, days_since=0, store_txns=579643),

    # 2i. Premium item AED 50, coverage 3.5x, selling well → EXCESS
    p("store_AC","COMMON00039","[2i] Premium price, 3.5x coverage, good velocity",
      stock=2527, rqty=700, rtxns=350, ravg=2.0, rstd=0.3,
      price=50.0, days_since=1),

    # 2j. Perishable (produce), stock=500, coverage=0.7x but trend up → LOW risk
    p("store_AC","COMMON00041","[2j] Perishable, coverage 0.7x, trending up",
      stock=875, cat="produce", price=24.13,
      rqty=1300, rtxns=1300, ravg=1.0, rstd=0.0,
      hqty=5951, htxns=5951, havg=1.0, days_since=0, store_txns=637476),
]

# Expected: some are ambiguous — marked with "?" where either label is valid
expected_tricky = [
    "Slow",    # 2a: just above 4x → Slow
    "Excess",  # 2b: just under 4x, good velocity → Excess
    "Low",     # 2c: velocity reversal, low stock → Low
    "Slow",    # 2d: 89 days, high stock → Slow
    "Dead",    # 2e: 91 days → Dead
    "?",       # 2f: unknown store (Optimum or Low are both reasonable)
    "?",       # 2g: cold start (Dead or Slow typical)
    "Low",     # 2h: big stock but demand far exceeds it
    "Excess",  # 2i: premium price shouldn't change Excess classification
    "Optimum", # 2j: coverage=0.70x (>0.6), days_stock=21 (>14), no stockout → Optimum is correct
]

preds2 = predict(tricky)
suite2_pass = 0
suite2_total_definite = 0
ambiguous_results = []

print()
for r, exp, prod in zip(preds2, expected_tricky, tricky):
    if exp == "?":
        status = WARN
        ambiguous_results.append((prod["product_name"], r["prediction"], r["confidence"]))
        results_log.append((status, r["prediction"], "any", r["confidence"], prod["product_name"]))
        print(f"  {status}  got={r['prediction']:<8} exp=any      conf={r['confidence']:.0%}  {prod['product_name']}")
    else:
        suite2_total_definite += 1
        if check(r["prediction"], exp, r["confidence"], prod["product_name"]):
            suite2_pass += 1

print(f"\n  Suite 2 score: {suite2_pass}/{suite2_total_definite} definite cases")


# ===========================================================================
# SUITE 3 — RECOMMENDATION ENGINE
# Verifies transfer logic: single vs combined, restock fallback
# ===========================================================================

print(f"\n{'='*65}")
print("  SUITE 3 — RECOMMENDATION ENGINE")
print(f"{'='*65}")

rec_products = [
    # Single donor scenario: store_AE has 8000 (Excess), store_AD needs ~3162
    p("store_AE","COMMON00041","Milk [EXCESS donor]", stock=8000, cat="produce", price=24.13,
      rqty=1989,rtxns=1989,ravg=1.0,rstd=0.0, hqty=10382,htxns=10382,havg=1.0,
      total=12371,nsales=12371,days_since=0,store_txns=620440),
    p("store_AD","COMMON00041","Milk [LOW receiver]", stock=500, cat="produce", price=24.13,
      rqty=2357,rtxns=2357,ravg=1.0,rstd=0.0, hqty=12685,htxns=12685,havg=1.0,
      total=15042,nsales=15042,days_since=0,store_txns=825062),

    # Combined donor scenario: AE+AF together for AB (neither alone enough)
    p("store_AE","COMMON00039","Chips [partial donor 1]", stock=3000, price=8.5,
      rqty=1989,rtxns=1989,ravg=1.0,rstd=0.0, hqty=10382,htxns=10382,havg=1.0,
      total=12371,nsales=12371,days_since=0,store_txns=620440),
    p("store_AF","COMMON00039","Chips [dead donor 2]", stock=2050, price=8.5,
      rqty=0,rtxns=0,ravg=0.0,rstd=0.0, hqty=4570,htxns=4570,havg=1.0,
      total=5343,nsales=5343,days_since=95,store_txns=579643),
    p("store_AB","COMMON00039","Chips [LOW receiver]", stock=500, price=8.5,
      rqty=2357,rtxns=2357,ravg=1.0,rstd=0.0, hqty=12685,htxns=12685,havg=1.0,
      total=15042,nsales=15042,days_since=0,store_txns=825062),

    # No donor: pure restock
    p("store_AA","COMMON00017","Juice [no donor, LOW]", stock=20, cat="beverages", price=6.0,
      rqty=300,rtxns=150,ravg=2.0,rstd=0.5, hqty=1200,htxns=600,havg=2.0,
      total=1220,nsales=750,days_since=0,store_txns=754570),
]

rec = recommend(rec_products)
transfers = rec["transfers"]
restocks  = rec["restocks"]

print()
# Check single mode
single_transfers = [t for t in transfers if t["transfer_mode"] == "single"]
combined_transfers = [t for t in transfers if t["transfer_mode"] == "combined"]
s3_pass = 0

# Test: single transfer exists for COMMON00041
has_single_milk = any(t["product_id"]=="COMMON00041" and t["transfer_mode"]=="single" for t in transfers)
if has_single_milk:
    t = next(t for t in transfers if t["product_id"]=="COMMON00041")
    s3_pass += 1
    print(f"  {PASS}  SINGLE transfer: {t['from_store']}→{t['to_store']}  qty={t['transfer_qty']:,}  donor_keeps={t['from_coverage_after']}x  receiver_gets={t['to_coverage_after']}x")
else:
    print(f"  {FAIL}  Expected SINGLE transfer for COMMON00041")

# Test: combined transfer exists for COMMON00039
has_combined_chips = any(t["product_id"]=="COMMON00039" and t["transfer_mode"]=="combined" for t in transfers)
if has_combined_chips:
    grp = [t for t in transfers if t["product_id"]=="COMMON00039"]
    s3_pass += 1
    total_sent = sum(t["transfer_qty"] for t in grp)
    print(f"  {PASS}  COMBINED transfer: {len(grp)} donors → {grp[0]['to_store']}  total={total_sent:,} units")
    for t in grp:
        print(f"          {t['from_store']} ({t['from_label']}) contributes {t['transfer_qty']:,}  coverage after: {t['from_coverage_after']}x")
else:
    print(f"  {FAIL}  Expected COMBINED transfer for COMMON00039")

# Test: receiver hits ~1.5x coverage
all_to_cov = [t["to_coverage_after"] for t in transfers]
receivers_healthy = all(1.3 <= c <= 1.7 for c in all_to_cov)
if receivers_healthy:
    s3_pass += 1
    print(f"  {PASS}  All receivers reach 1.3–1.7x coverage after transfer: {[round(c,2) for c in all_to_cov]}")
else:
    print(f"  {FAIL}  Receiver coverage out of expected range: {all_to_cov}")

# Test: donors stay above 0.9x floor
donor_floors = [t["from_coverage_after"] for t in transfers if t["from_label"] != "Dead"]
donors_safe = all(c >= 0.85 for c in donor_floors)
if donors_safe:
    s3_pass += 1
    print(f"  {PASS}  All non-Dead donors stay ≥ 0.9x coverage: {[round(c,2) for c in donor_floors]}")
else:
    print(f"  {FAIL}  Donor dropped below safety floor: {donor_floors}")

# Test: restock for juice (no donors)
has_restock = any(r["product_id"]=="COMMON00017" for r in restocks)
if has_restock:
    rs = next(r for r in restocks if r["product_id"]=="COMMON00017")
    s3_pass += 1
    print(f"  {PASS}  RESTOCK for COMMON00017: order {rs['restock_qty']:,} units  ({rs['reason'][:45]})")
else:
    print(f"  {FAIL}  Expected restock recommendation for COMMON00017")

print(f"\n  Suite 3 score: {s3_pass}/5")


# ===========================================================================
# SUITE 4 — OVER/UNDERFITTING ANALYSIS
# ===========================================================================

print(f"\n{'='*65}")
print("  SUITE 4 — OVER/UNDERFITTING ANALYSIS")
print(f"{'='*65}")

# Collect all predictions from suites 1+2
all_preds = preds + preds2
label_dist = defaultdict(int)
confidences = []
for r in all_preds:
    label_dist[r["prediction"]] += 1
    confidences.append(r["confidence"])

total = len(all_preds)
avg_conf   = sum(confidences) / len(confidences)
min_conf   = min(confidences)
max_conf   = max(confidences)
conf_range = max_conf - min_conf

print(f"\n  Label distribution across {total} predictions:")
for label in ["Low","Optimum","Excess","Slow","Dead"]:
    count = label_dist.get(label, 0)
    bar = "█" * count
    print(f"    {label:<8}: {count:2d}  {bar}")

print(f"\n  Confidence stats:")
print(f"    avg={avg_conf:.0%}  min={min_conf:.0%}  max={max_conf:.0%}  range={conf_range:.0%}")

# Verdict
print(f"\n  Overfitting signals:")
high_conf_wrong = [(s,g,e,c,n) for s,g,e,c,n in results_log if s==FAIL and c > 0.8]
if high_conf_wrong:
    print(f"    ⚠️  {len(high_conf_wrong)} wrong predictions with HIGH confidence (classic overfitting sign):")
    for _,g,e,c,n in high_conf_wrong:
        print(f"       got={g} exp={e} conf={c:.0%}  {n}")
else:
    print(f"    ✅ No high-confidence wrong predictions")

print(f"\n  Underfitting signals:")
dominant_label = max(label_dist, key=label_dist.get)
dominant_pct   = label_dist[dominant_label] / total
if dominant_pct > 0.7:
    print(f"    ⚠️  Model predicts '{dominant_label}' {dominant_pct:.0%} of the time — possible label bias")
else:
    print(f"    ✅ Label spread looks diverse — no single label dominates ({dominant_label} at {dominant_pct:.0%})")

obvious_fails = sum(1 for s,*_ in results_log[:6] if s == FAIL)
if obvious_fails > 1:
    print(f"    ⚠️  {obvious_fails} obvious cases failed — model may be underfitting")
else:
    print(f"    ✅ Obvious cases pass ({6-obvious_fails}/6) — model is not underfitting")

low_conf_all = sum(1 for c in confidences if c < 0.55)
if low_conf_all / total > 0.4:
    print(f"    ⚠️  {low_conf_all}/{total} predictions below 55% confidence — model is uncertain across the board")
else:
    print(f"    ✅ Confidence generally adequate ({low_conf_all}/{total} below 55%)")


# ===========================================================================
# FINAL SCORECARD
# ===========================================================================

total_definite = suite1_pass + suite2_pass + s3_pass
total_possible = len(obvious) + suite2_total_definite + 5
overall_pct = total_definite / total_possible * 100

print(f"\n{'='*65}")
print(f"  FINAL SCORECARD")
print(f"{'='*65}")
print(f"  Suite 1 — Obvious cases    : {suite1_pass}/{len(obvious)}")
print(f"  Suite 2 — Boundary/tricky  : {suite2_pass}/{suite2_total_definite}")
print(f"  Suite 3 — Recommendation   : {s3_pass}/5")
print(f"  {'─'*40}")
print(f"  Total                      : {total_definite}/{total_possible}  ({overall_pct:.0f}%)")

if overall_pct >= 85:
    verdict = "✅ HEALTHY — model generalises well, no clear over/underfitting"
elif overall_pct >= 70:
    verdict = "⚠️  ACCEPTABLE — some boundary cases missed, monitor in production"
else:
    verdict = "❌ NEEDS RETRAINING — too many failures, check label balance"

print(f"\n  Verdict: {verdict}")

print(f"\n  Ambiguous cases (no definitive expected label):")
for name, got, conf in ambiguous_results:
    print(f"    {name}: model chose {got} ({conf:.0%})")

print(f"\n{'='*65}\n")
