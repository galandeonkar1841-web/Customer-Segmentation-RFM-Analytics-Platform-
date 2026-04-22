"""
Step 2 – Load CSVs into SQLite and run optimised SQL queries
Produces:
  data/sql_outputs/rfm_raw.csv         – per-customer RFM metrics
  data/sql_outputs/category_revenue.csv
  data/sql_outputs/monthly_trend.csv
  data/sql_outputs/country_summary.csv
  data/sql_outputs/data_quality.csv

Run: python scripts/sql/sql_analysis.py
"""

import csv
import sqlite3
import os
from datetime import datetime

BASE    = os.path.join(os.path.dirname(__file__), "..", "..")
RAW     = os.path.join(BASE, "data", "raw")
SQL_OUT = os.path.join(BASE, "data", "sql_outputs")
DB_PATH = os.path.join(BASE, "data", "retail.db")
os.makedirs(SQL_OUT, exist_ok=True)

# ── Helper ────────────────────────────────────────────────────────────────────
def load_csv(name):
    with open(os.path.join(RAW, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))

def save_csv(rows, name):
    if not rows: return
    path = os.path.join(SQL_OUT, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)

def run_query(conn, sql, params=()):
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

# ── Connect & create tables ───────────────────────────────────────────────────
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("DROP TABLE IF EXISTS transactions")
conn.execute("DROP TABLE IF EXISTS customers")
conn.execute("DROP TABLE IF EXISTS products")

conn.execute("""
CREATE TABLE transactions (
    transaction_id   TEXT PRIMARY KEY,
    customer_id      TEXT,
    product_id       TEXT,
    transaction_date TEXT,
    quantity         INTEGER,
    unit_price       REAL,
    revenue          REAL,
    country          TEXT,
    channel          TEXT
)""")
conn.execute("""
CREATE TABLE customers (
    customer_id  TEXT PRIMARY KEY,
    country      TEXT,
    signup_date  TEXT,
    age_group    TEXT,
    gender       TEXT,
    email_opt_in INTEGER
)""")
conn.execute("""
CREATE TABLE products (
    product_id   TEXT PRIMARY KEY,
    product_name TEXT,
    category     TEXT,
    unit_price   REAL
)""")

# ── Load data ─────────────────────────────────────────────────────────────────
txns  = load_csv("transactions.csv")
custs = load_csv("customers.csv")
prods = load_csv("products.csv")

conn.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?)",
    [(r["transaction_id"],r["customer_id"],r["product_id"],r["transaction_date"],
      int(r["quantity"]),float(r["unit_price"]),float(r["revenue"]),
      r["country"],r["channel"]) for r in txns])
conn.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?)",
    [(r["customer_id"],r["country"],r["signup_date"],r["age_group"],
      r["gender"],int(r["email_opt_in"])) for r in custs])
conn.executemany("INSERT INTO products VALUES (?,?,?,?)",
    [(r["product_id"],r["product_name"],r["category"],float(r["unit_price"]))
     for r in prods])

# Create indexes for performance
conn.execute("CREATE INDEX idx_txn_customer ON transactions(customer_id)")
conn.execute("CREATE INDEX idx_txn_date     ON transactions(transaction_date)")
conn.execute("CREATE INDEX idx_txn_product  ON transactions(product_id)")
conn.commit()
print(f"  DB loaded: {len(txns)} transactions, {len(custs)} customers, {len(prods)} products")

# ── SQL QUERY 1: RFM Metrics ──────────────────────────────────────────────────
# Recency  = days since last purchase (lower = better)
# Frequency = number of distinct orders
# Monetary  = total net revenue (positive transactions only)
rfm_sql = """
SELECT
    t.customer_id,
    c.country,
    c.age_group,
    c.email_opt_in,
    -- Recency: days since last purchase from reference date 2025-01-01
    CAST(julianday('2025-01-01') - julianday(MAX(t.transaction_date)) AS INTEGER) AS recency_days,
    -- Frequency: number of transactions (excluding returns)
    COUNT(CASE WHEN t.quantity > 0 THEN 1 END)                                   AS frequency,
    -- Monetary: total revenue from completed sales
    ROUND(SUM(CASE WHEN t.quantity > 0 THEN t.revenue ELSE 0 END), 2)            AS monetary,
    -- Avg order value
    ROUND(SUM(CASE WHEN t.quantity > 0 THEN t.revenue ELSE 0 END)
          / NULLIF(COUNT(CASE WHEN t.quantity > 0 THEN 1 END), 0), 2)            AS avg_order_value,
    -- Return rate
    ROUND(
        CAST(COUNT(CASE WHEN t.quantity < 0 THEN 1 END) AS REAL)
        / NULLIF(COUNT(*), 0) * 100, 1)                                           AS return_rate_pct,
    MAX(t.transaction_date)                                                        AS last_purchase_date,
    MIN(t.transaction_date)                                                        AS first_purchase_date
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.quantity != 0
GROUP BY t.customer_id, c.country, c.age_group, c.email_opt_in
HAVING frequency > 0
ORDER BY monetary DESC
"""
rfm_rows = run_query(conn, rfm_sql)
save_csv(rfm_rows, "rfm_raw.csv")
print(f"  rfm_raw.csv           -> {len(rfm_rows)} customers")

# ── SQL QUERY 2: Category Revenue ────────────────────────────────────────────
cat_sql = """
SELECT
    p.category,
    COUNT(DISTINCT t.customer_id)                                    AS unique_customers,
    COUNT(*)                                                          AS total_transactions,
    ROUND(SUM(CASE WHEN t.quantity > 0 THEN t.revenue ELSE 0 END),2) AS gross_revenue,
    ROUND(AVG(CASE WHEN t.quantity > 0 THEN t.unit_price END), 2)    AS avg_unit_price,
    ROUND(SUM(CASE WHEN t.quantity > 0 THEN t.revenue ELSE 0 END)
        / (SELECT SUM(CASE WHEN quantity > 0 THEN revenue ELSE 0 END)
           FROM transactions) * 100, 1)                               AS revenue_share_pct
FROM transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY p.category
ORDER BY gross_revenue DESC
"""
cat_rows = run_query(conn, cat_sql)
save_csv(cat_rows, "category_revenue.csv")
print(f"  category_revenue.csv  -> {len(cat_rows)} categories")

# ── SQL QUERY 3: Monthly Revenue Trend ───────────────────────────────────────
trend_sql = """
SELECT
    substr(transaction_date, 1, 7)                                    AS month,
    COUNT(DISTINCT customer_id)                                        AS active_customers,
    COUNT(*)                                                           AS transactions,
    ROUND(SUM(CASE WHEN quantity > 0 THEN revenue ELSE 0 END), 2)     AS net_revenue,
    ROUND(AVG(CASE WHEN quantity > 0 THEN revenue ELSE 0 END), 2)     AS avg_transaction_value
FROM transactions
GROUP BY substr(transaction_date, 1, 7)
ORDER BY month
"""
trend_rows = run_query(conn, trend_sql)
save_csv(trend_rows, "monthly_trend.csv")
print(f"  monthly_trend.csv     -> {len(trend_rows)} months")

# ── SQL QUERY 4: Country Summary ─────────────────────────────────────────────
country_sql = """
SELECT
    t.country,
    COUNT(DISTINCT t.customer_id)                                     AS customers,
    COUNT(*)                                                           AS transactions,
    ROUND(SUM(CASE WHEN t.quantity > 0 THEN t.revenue ELSE 0 END),2) AS revenue,
    ROUND(SUM(CASE WHEN t.quantity > 0 THEN t.revenue ELSE 0 END)
          / COUNT(DISTINCT t.customer_id), 2)                          AS revenue_per_customer
FROM transactions t
GROUP BY t.country
ORDER BY revenue DESC
"""
country_rows = run_query(conn, country_sql)
save_csv(country_rows, "country_summary.csv")
print(f"  country_summary.csv   -> {len(country_rows)} countries")

# ── SQL QUERY 5: Data Quality Check ──────────────────────────────────────────
dq_sql = """
SELECT
    'transactions'                                                         AS table_name,
    COUNT(*)                                                               AS total_rows,
    COUNT(CASE WHEN customer_id IS NULL OR customer_id = '' THEN 1 END)   AS null_customer_id,
    COUNT(CASE WHEN transaction_date IS NULL THEN 1 END)                   AS null_dates,
    COUNT(CASE WHEN unit_price <= 0 THEN 1 END)                            AS bad_prices,
    COUNT(CASE WHEN quantity < 0 THEN 1 END)                               AS returns,
    ROUND(COUNT(CASE WHEN quantity < 0 THEN 1 END) * 100.0 / COUNT(*), 1) AS return_rate_pct
FROM transactions
"""
dq_rows = run_query(conn, dq_sql)
save_csv(dq_rows, "data_quality.csv")
print(f"  data_quality.csv      -> quality report saved")

conn.close()

# ── Print summary ─────────────────────────────────────────────────────────────
print("\n  SQL ANALYSIS SUMMARY")
print("  " + "="*45)
total_rev = sum(float(r["monetary"]) for r in rfm_rows)
print(f"  Total customers analysed : {len(rfm_rows)}")
print(f"  Total net revenue        : {total_rev:,.2f}")
print(f"  Avg monetary value       : {total_rev/len(rfm_rows):,.2f}")
print(f"\n  Top 3 categories:")
for r in cat_rows[:3]:
    print(f"    {r['category']:<20} Revenue share: {r['revenue_share_pct']}%")
print(f"\n  SQL outputs saved -> data/sql_outputs/")
