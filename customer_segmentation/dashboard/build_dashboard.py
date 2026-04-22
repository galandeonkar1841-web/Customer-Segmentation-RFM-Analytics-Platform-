"""
Step 5 – Build Dashboard HTML
Run: python dashboard/build_dashboard.py
"""
import json, os

BASE = os.path.dirname(__file__)
DATA = os.path.join(BASE, "..", "data", "processed", "analytics.json")
TMPL = os.path.join(BASE, "dashboard_template.html")
OUT  = os.path.join(BASE, "customer_segmentation_dashboard.html")

with open(DATA, encoding="utf-8") as f: analytics = json.load(f)
with open(TMPL, encoding="utf-8") as f: html      = f.read()

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html.replace("__ANALYTICS_JSON__", json.dumps(analytics, indent=2)))

print(f"  Dashboard built -> dashboard/customer_segmentation_dashboard.html")
print(f"  Open in your browser!")
