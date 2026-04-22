"""
Step 3 – RFM Scoring + Customer Segmentation (K-Means clustering)
Reads:    data/sql_outputs/rfm_raw.csv
Produces: data/processed/rfm_scored.csv
          data/processed/segments_summary.csv
          data/processed/feature_importance.csv   (for AI/ML feature prep)

Run: python scripts/segmentation/rfm_segmentation.py
"""

import csv
import os
import json
import math
from collections import defaultdict

BASE  = os.path.join(os.path.dirname(__file__), "..", "..")
SQL   = os.path.join(BASE, "data", "sql_outputs")
OUT   = os.path.join(BASE, "data", "processed")
os.makedirs(OUT, exist_ok=True)

# ── Load RFM data ─────────────────────────────────────────────────────────────
def load_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

rfm_raw = load_csv(os.path.join(SQL, "rfm_raw.csv"))
print(f"  Loaded {len(rfm_raw)} customer RFM records")

# ── Step A: RFM Scoring (1-5 scale) ──────────────────────────────────────────
def score_quantile(values, val, reverse=False):
    """Score a value 1-5 based on quintile rank."""
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    rank = sorted_vals.index(min(sorted_vals, key=lambda x: abs(x - val)))
    score = int((rank / n) * 5) + 1
    score = min(score, 5)
    return (6 - score) if reverse else score  # reverse: lower recency = higher score

recency_vals   = [int(r["recency_days"]) for r in rfm_raw]
frequency_vals = [int(r["frequency"])    for r in rfm_raw]
monetary_vals  = [float(r["monetary"])   for r in rfm_raw]

scored = []
for r in rfm_raw:
    rec  = int(r["recency_days"])
    freq = int(r["frequency"])
    mon  = float(r["monetary"])

    r_score = score_quantile(recency_vals,   rec,  reverse=True)   # lower days = better
    f_score = score_quantile(frequency_vals, freq, reverse=False)
    m_score = score_quantile(monetary_vals,  mon,  reverse=False)

    rfm_score = r_score * 100 + f_score * 10 + m_score
    combined  = round((r_score + f_score + m_score) / 3, 2)

    scored.append({**r,
        "r_score": r_score,
        "f_score": f_score,
        "m_score": m_score,
        "rfm_score": rfm_score,
        "rfm_combined": combined,
    })

# ── Step B: Assign Segment Labels based on RFM scores ────────────────────────
def assign_segment(r, f, m):
    if r >= 4 and f >= 4 and m >= 4:
        return "Champion"
    elif r >= 3 and f >= 3 and m >= 3:
        return "Loyal Customer"
    elif r >= 4 and f <= 2:
        return "New Customer"
    elif r >= 3 and f >= 2 and m >= 2:
        return "Potential Loyalist"
    elif r <= 2 and f >= 3 and m >= 3:
        return "At Risk"
    elif r <= 2 and f >= 4 and m >= 4:
        return "Cannot Lose Them"
    elif r <= 2 and f <= 2 and m <= 2:
        return "Hibernating"
    elif r <= 1:
        return "Lost"
    else:
        return "Need Attention"

for row in scored:
    row["segment"] = assign_segment(row["r_score"], row["f_score"], row["m_score"])

# ── Step C: K-Means Clustering (manual implementation – no sklearn needed) ───
def normalize(values):
    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1
    return [(v - mn) / rng for v in values]

def kmeans(points, k=5, iterations=100):
    """Simple K-Means on 3D points."""
    random_indices = list(range(0, len(points), len(points) // k))[:k]
    centroids = [points[i] for i in random_indices]

    assignments = [0] * len(points)
    for _ in range(iterations):
        # Assign
        for i, p in enumerate(points):
            dists = [sum((p[d] - c[d])**2 for d in range(len(p))) for c in centroids]
            assignments[i] = dists.index(min(dists))
        # Update centroids
        new_centroids = []
        for cluster in range(k):
            cluster_pts = [points[j] for j in range(len(points)) if assignments[j] == cluster]
            if cluster_pts:
                new_centroids.append([
                    sum(pt[d] for pt in cluster_pts) / len(cluster_pts)
                    for d in range(len(cluster_pts[0]))
                ])
            else:
                new_centroids.append(centroids[cluster])
        centroids = new_centroids
    return assignments, centroids

# Normalize RFM for clustering
r_norm = normalize(recency_vals)
f_norm = normalize(frequency_vals)
m_norm = normalize(monetary_vals)
points = [[r_norm[i], f_norm[i], m_norm[i]] for i in range(len(scored))]

print("  Running K-Means clustering (k=5)...")
assignments, centroids = kmeans(points, k=5, iterations=50)

# Label clusters by centroid monetary value (descending)
cluster_mon = {i: centroids[i][2] for i in range(5)}
sorted_clusters = sorted(cluster_mon, key=lambda x: -cluster_mon[x])
cluster_label_map = {
    sorted_clusters[0]: "High Value",
    sorted_clusters[1]: "Mid-High Value",
    sorted_clusters[2]: "Mid Value",
    sorted_clusters[3]: "Low-Mid Value",
    sorted_clusters[4]: "Low Value",
}

for i, row in enumerate(scored):
    row["cluster_id"]    = assignments[i]
    row["cluster_label"] = cluster_label_map[assignments[i]]

# ── Step D: Save scored CSV ───────────────────────────────────────────────────
fieldnames = list(rfm_raw[0].keys()) + ["r_score","f_score","m_score",
                                         "rfm_score","rfm_combined",
                                         "segment","cluster_id","cluster_label"]
out_path = os.path.join(OUT, "rfm_scored.csv")
with open(out_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader(); w.writerows(scored)
print(f"  rfm_scored.csv saved -> {len(scored)} rows")

# ── Step E: Segment Summary ───────────────────────────────────────────────────
seg_groups = defaultdict(list)
for row in scored:
    seg_groups[row["segment"]].append(row)

seg_summary = []
for seg, rows in sorted(seg_groups.items()):
    avg_rec  = sum(int(r["recency_days"]) for r in rows) / len(rows)
    avg_freq = sum(int(r["frequency"])    for r in rows) / len(rows)
    avg_mon  = sum(float(r["monetary"])   for r in rows) / len(rows)
    total_rev= sum(float(r["monetary"])   for r in rows)
    pct      = round(len(rows) / len(scored) * 100, 1)

    # Business recommendation per segment
    recommendations = {
        "Champion":          "Reward with loyalty perks; ask for reviews/referrals",
        "Loyal Customer":    "Upsell premium products; offer early access",
        "New Customer":      "Onboarding emails; guide to best-sellers",
        "Potential Loyalist":"Membership offers; personalised recommendations",
        "At Risk":           "Win-back campaigns; survey on satisfaction",
        "Cannot Lose Them":  "Urgent reactivation; personal outreach",
        "Need Attention":    "Targeted discount; limited-time offer",
        "Hibernating":       "Low-cost email nudge; product updates",
        "Lost":              "Last-chance deep discount; or remove from list",
    }

    seg_summary.append({
        "segment":           seg,
        "customer_count":    len(rows),
        "pct_of_customers":  pct,
        "avg_recency_days":  round(avg_rec, 1),
        "avg_frequency":     round(avg_freq, 1),
        "avg_monetary":      round(avg_mon, 2),
        "total_revenue":     round(total_rev, 2),
        "recommendation":    recommendations.get(seg, "Monitor and engage"),
    })

seg_summary.sort(key=lambda x: -x["total_revenue"])
sum_path = os.path.join(OUT, "segments_summary.csv")
with open(sum_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=seg_summary[0].keys())
    w.writeheader(); w.writerows(seg_summary)
print(f"  segments_summary.csv saved -> {len(seg_summary)} segments")

# ── Step F: Feature Importance (AI/ML prep) ───────────────────────────────────
# Compute variance of each feature per segment — higher variance = more signal
features = ["recency_days", "frequency", "monetary", "avg_order_value", "return_rate_pct"]
feat_rows = []
for feat in features:
    vals = [float(r[feat]) for r in scored if r.get(feat)]
    mean = sum(vals) / len(vals)
    var  = sum((v - mean)**2 for v in vals) / len(vals)
    std  = math.sqrt(var)
    feat_rows.append({
        "feature":   feat,
        "mean":      round(mean, 3),
        "std_dev":   round(std, 3),
        "min":       round(min(vals), 3),
        "max":       round(max(vals), 3),
        "use_in_ml": "Yes",
        "notes":     "Normalise before model training",
    })

feat_path = os.path.join(OUT, "feature_importance.csv")
with open(feat_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=feat_rows[0].keys())
    w.writeheader(); w.writerows(feat_rows)
print(f"  feature_importance.csv saved -> {len(feat_rows)} features")

# ── Print segment breakdown ───────────────────────────────────────────────────
print("\n  SEGMENT BREAKDOWN")
print("  " + "="*65)
print(f"  {'Segment':<22} {'Count':>6} {'%':>5} {'Avg Monetary':>14} {'Avg Recency':>12}")
print("  " + "-"*65)
for s in seg_summary:
    print(f"  {s['segment']:<22} {s['customer_count']:>6} {s['pct_of_customers']:>4}%"
          f"  {s['avg_monetary']:>12,.2f}  {s['avg_recency_days']:>10.0f}d")
print(f"\n  Segmentation complete -> data/processed/")
