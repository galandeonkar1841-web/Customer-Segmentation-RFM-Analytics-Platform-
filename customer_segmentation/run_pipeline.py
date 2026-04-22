"""
run_pipeline.py  -  ONE command to run the entire project end-to-end
Usage:  python run_pipeline.py
"""
import subprocess, sys, os

BASE = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ("STEP 1  Generate Raw Retail Data",
     [sys.executable, os.path.join(BASE,"scripts","ingestion","generate_data.py")]),
    ("STEP 2  SQL Analysis (RFM extraction + 4 business queries)",
     [sys.executable, os.path.join(BASE,"scripts","sql","sql_analysis.py")]),
    ("STEP 3  RFM Scoring + K-Means Segmentation",
     [sys.executable, os.path.join(BASE,"scripts","segmentation","rfm_segmentation.py")]),
    ("STEP 4  Build Analytics JSON",
     [sys.executable, os.path.join(BASE,"scripts","visualization","build_analytics.py")]),
    ("STEP 5  Build BI Dashboard",
     [sys.executable, os.path.join(BASE,"dashboard","build_dashboard.py")]),
]

print("=" * 62)
print("  CUSTOMER SEGMENTATION PIPELINE  -  FULL RUN")
print("=" * 62)

for name, cmd in STEPS:
    print(f"\n{'─'*62}\n  >> {name}\n{'─'*62}")
    r = subprocess.run(cmd, cwd=BASE)
    if r.returncode != 0:
        print(f"\n  FAILED at: {name}")
        sys.exit(1)

dashboard = os.path.join(BASE,"dashboard","customer_segmentation_dashboard.html")
print("\n" + "=" * 62)
print("  PIPELINE COMPLETE!")
print(f"\n  Open dashboard:")
print(f"  {dashboard}")
print("=" * 62)
