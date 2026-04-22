"""
Step 4 – Generate Analytics JSON for Dashboard
Reads all processed CSVs and bundles them into one JSON file.

Run: python scripts/visualization/build_analytics.py
"""

import csv, json, os
from collections import defaultdict

BASE = os.path.join(os.path.dirname(__file__), "..", "..")
SQL  = os.path.join(BASE, "data", "sql_outputs")
PROC = os.path.join(BASE, "data", "processed")
OUT  = os.path.join(BASE, "data", "processed")

def load(folder, name):
    with open(os.path.join(folder, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))

rfm       = load(PROC, "rfm_scored.csv")
segments  = load(PROC, "segments_summary.csv")
monthly   = load(SQL,  "monthly_trend.csv")
category  = load(SQL,  "category_revenue.csv")
country   = load(SQL,  "country_summary.csv")
dq        = load(SQL,  "data_quality.csv")[0]

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_rev   = sum(float(r["monetary"]) for r in rfm)
total_cust  = len(rfm)
avg_mon     = total_rev / total_cust
avg_freq    = sum(int(r["frequency"]) for r in rfm) / total_cust
avg_rec     = sum(int(r["recency_days"]) for r in rfm) / total_cust
champions   = len([r for r in rfm if r["segment"] == "Champion"])
at_risk     = len([r for r in rfm if r["segment"] in ["At Risk","Cannot Lose Them"]])

kpis = {
    "total_revenue":       round(total_rev, 2),
    "total_customers":     total_cust,
    "avg_order_value":     round(avg_mon / avg_freq, 2),
    "avg_frequency":       round(avg_freq, 1),
    "avg_recency_days":    round(avg_rec, 1),
    "champion_count":      champions,
    "at_risk_count":       at_risk,
    "at_risk_pct":         round(at_risk / total_cust * 100, 1),
    "data_quality_score":  round((1 - float(dq["null_customer_id"]) / float(dq["total_rows"])) * 100, 1),
}

# ── Segment chart data ────────────────────────────────────────────────────────
seg_chart = [{"segment": s["segment"],
              "count": int(s["customer_count"]),
              "pct": float(s["pct_of_customers"]),
              "avg_monetary": float(s["avg_monetary"]),
              "total_revenue": float(s["total_revenue"]),
              "recommendation": s["recommendation"]}
             for s in segments]

# ── RFM scatter (sample 200 for performance) ─────────────────────────────────
step = max(1, len(rfm) // 200)
scatter = [{"r": int(r["r_score"]), "f": int(r["f_score"]), "m": int(r["m_score"]),
            "segment": r["segment"], "monetary": float(r["monetary"]),
            "customer_id": r["customer_id"]}
           for r in rfm[::step]]

# ── Monthly trend ─────────────────────────────────────────────────────────────
monthly_chart = [{"month": r["month"],
                  "revenue": float(r["net_revenue"]),
                  "customers": int(r["active_customers"]),
                  "transactions": int(r["transactions"])}
                 for r in monthly]

# ── Category breakdown ────────────────────────────────────────────────────────
cat_chart = [{"category": r["category"],
              "revenue": float(r["gross_revenue"]),
              "share_pct": float(r["revenue_share_pct"]),
              "customers": int(r["unique_customers"])}
             for r in category]

# ── Country data ──────────────────────────────────────────────────────────────
country_chart = [{"country": r["country"],
                  "revenue": float(r["revenue"]),
                  "customers": int(r["customers"]),
                  "rev_per_customer": float(r["revenue_per_customer"])}
                 for r in country]

# ── Cluster summary ───────────────────────────────────────────────────────────
clusters = defaultdict(lambda: {"count": 0, "revenue": 0.0})
for r in rfm:
    cl = r["cluster_label"]
    clusters[cl]["count"]   += 1
    clusters[cl]["revenue"] += float(r["monetary"])
cluster_chart = [{"cluster": k, "count": v["count"], "revenue": round(v["revenue"], 2)}
                 for k, v in sorted(clusters.items(), key=lambda x: -x[1]["revenue"])]

# ── Bundle & save ─────────────────────────────────────────────────────────────
analytics = {
    "kpis":           kpis,
    "segments":       seg_chart,
    "rfm_scatter":    scatter,
    "monthly_trend":  monthly_chart,
    "category":       cat_chart,
    "country":        country_chart,
    "clusters":       cluster_chart,
}

out_path = os.path.join(OUT, "analytics.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(analytics, f, indent=2)

print(f"  analytics.json saved")
print(f"\n  KPI SUMMARY")
print(f"  {'Total Revenue':<25} {kpis['total_revenue']:>12,.2f}")
print(f"  {'Total Customers':<25} {kpis['total_customers']:>12,}")
print(f"  {'Avg Order Value':<25} {kpis['avg_order_value']:>12,.2f}")
print(f"  {'Avg Purchase Frequency':<25} {kpis['avg_frequency']:>12}")
print(f"  {'Champions':<25} {kpis['champion_count']:>12}")
print(f"  {'At Risk Customers':<25} {kpis['at_risk_count']:>12} ({kpis['at_risk_pct']}%)")
