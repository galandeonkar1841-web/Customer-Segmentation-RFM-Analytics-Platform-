# Customer Segmentation with Python + SQL + BI
### Resume Project | Data Analytics Role
> **Tech Stack:** Python · SQLite (SQL) · RFM Analysis · K-Means Clustering · Chart.js Dashboard

---

## Folder Structure

```
customer_segmentation/
│
├── run_pipeline.py                         <- ONE command runs everything
├── requirements.txt
├── README.md
│
├── scripts/
│   ├── ingestion/
│   │   └── generate_data.py               STEP 1 - Generate raw retail dataset
│   ├── sql/
│   │   └── sql_analysis.py                STEP 2 - Load into SQLite, run SQL queries
│   ├── segmentation/
│   │   └── rfm_segmentation.py            STEP 3 - RFM scoring + K-Means clustering
│   └── visualization/
│       └── build_analytics.py             STEP 4 - Build analytics JSON
│
├── dashboard/
│   ├── dashboard_template.html
│   ├── build_dashboard.py                 STEP 5 - Build HTML dashboard
│   └── customer_segmentation_dashboard.html   <- Open this in browser
│
└── data/
    ├── raw/
    │   ├── transactions.csv               ~5,000 retail transactions
    │   ├── customers.csv                  600 customers
    │   └── products.csv                  20 products across 6 categories
    ├── sql_outputs/
    │   ├── rfm_raw.csv                   Per-customer RFM metrics from SQL
    │   ├── category_revenue.csv
    │   ├── monthly_trend.csv
    │   ├── country_summary.csv
    │   └── data_quality.csv
    ├── processed/
    │   ├── rfm_scored.csv                RFM scores + segment + cluster labels
    │   ├── segments_summary.csv          Segment breakdown + recommendations
    │   ├── feature_importance.csv        ML feature prep report
    │   └── analytics.json               Dashboard data bundle
    └── retail.db                         SQLite database
```

---

## How to Run

### Requirements
- Python 3.8 or higher
- No pip installs needed - uses standard library only

---

### Option A - Run everything at once (Recommended)

**Windows (PowerShell / CMD):**
```
cd customer_segmentation
python run_pipeline.py
```

**Mac / Linux:**
```bash
cd customer_segmentation
python3 run_pipeline.py
```

Then open the dashboard:
- **Windows:** `start dashboard\customer_segmentation_dashboard.html`
- **Mac:**     `open dashboard/customer_segmentation_dashboard.html`
- Or just double-click the file in File Explorer / Finder

---

### Option B - Run each step individually

```bash
# Step 1 - Generate 600 customers + 5,000 transactions
python scripts/ingestion/generate_data.py

# Step 2 - Load into SQLite, run 5 optimised SQL queries
python scripts/sql/sql_analysis.py

# Step 3 - RFM scoring (1-5 scale) + K-Means clustering (k=5)
python scripts/segmentation/rfm_segmentation.py

# Step 4 - Aggregate all metrics into analytics.json
python scripts/visualization/build_analytics.py

# Step 5 - Inject JSON into HTML dashboard
python dashboard/build_dashboard.py
```

---

## What Each Step Produces

| Step | Script | Output |
|------|--------|--------|
| 1 | generate_data.py | 600 customers, 5K transactions with realistic buying patterns |
| 2 | sql_analysis.py | RFM metrics via SQL, category/country/trend reports, SQLite DB |
| 3 | rfm_segmentation.py | RFM scores 1-5, 9 segment labels, K-Means clusters, ML features |
| 4 | build_analytics.py | analytics.json with all KPIs and chart data |
| 5 | build_dashboard.py | Interactive HTML dashboard - open in any browser |

---

## Dashboard Panels

| Panel | Insight |
|-------|---------|
| KPI Cards | Total Revenue, Customers, Avg Order Value, Champions, At-Risk % |
| Segment Donut | Distribution across 9 RFM segments |
| Monthly Trend | Revenue + active customers over time |
| Category Revenue | Horizontal bar by product category |
| K-Means Clusters | 5 value-based customer clusters |
| Country Revenue | Top 7 countries by revenue |
| RFM Scatter | Bubble chart: Recency vs Monetary by segment |
| Segment Table | Full breakdown with business recommendations per segment |

---

## Connect to Power BI or Tableau

1. Run the pipeline to generate all CSVs
2. Open **Power BI Desktop** or **Tableau Public**
3. Import `data/processed/rfm_scored.csv`
4. Build visuals using: `segment`, `r_score`, `f_score`, `m_score`, `monetary`

---

## RFM Segment Definitions

| Segment | Recency | Frequency | Monetary | Action |
|---------|---------|-----------|----------|--------|
| Champion | High | High | High | Reward + referrals |
| Loyal Customer | Medium-High | Medium-High | Medium-High | Upsell |
| New Customer | High | Low | Low | Onboarding emails |
| Potential Loyalist | Medium | Medium | Medium | Membership offer |
| At Risk | Low | Medium-High | Medium-High | Win-back campaign |
| Cannot Lose Them | Low | High | High | Personal outreach |
| Need Attention | Medium-Low | Medium | Medium | Discount nudge |
| Hibernating | Low | Low | Low | Low-cost nudge |
| Lost | Very Low | Any | Any | Last-chance offer |

---

## Resume Bullet Points

- Built a **retail customer segmentation pipeline** using Python and SQL (SQLite) on 5,000+ transactions; designed 5 optimised SQL queries extracting RFM metrics, category revenue, and monthly trends with a data quality validation check
- Implemented **RFM scoring (1-5 quintile scale)** and **K-Means clustering (k=5)** to classify 600 customers into 9 actionable segments including Champions, At-Risk, and Hibernating cohorts — generating targeted reactivation recommendations per segment
- Engineered 5 ML-ready features (recency, frequency, monetary, AOV, return rate) with normalisation and variance analysis, documented as an AI/ML feature preparation report for downstream model training
- Developed an **interactive BI dashboard** in HTML/Chart.js with segment donut, RFM scatter plots, monthly trend, and country breakdown — directly importable into Power BI or Tableau via CSV exports
