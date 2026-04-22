"""
Step 1 – Generate Raw Retail Dataset
Simulates a UK-style online retail dataset (similar to UCI Online Retail Dataset)
Produces: data/raw/transactions.csv, customers.csv, products.csv

Run: python scripts/ingestion/generate_data.py
"""

import csv
import random
import os
from datetime import datetime, timedelta

random.seed(42)
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
os.makedirs(BASE_DIR, exist_ok=True)

# ── Constants ─────────────────────────────────────────────────────────────────
COUNTRIES = ["United Kingdom", "Germany", "France", "Spain", "Netherlands",
             "Belgium", "Switzerland", "Portugal", "Australia", "USA"]

PRODUCT_CATALOG = [
    ("P001", "Ceramic Mug Set",           "Kitchenware",    4.50),
    ("P002", "Vintage Table Lamp",        "Home Decor",    18.99),
    ("P003", "Scented Candle Pack",       "Home Decor",     8.25),
    ("P004", "Linen Cushion Cover",       "Textiles",       6.75),
    ("P005", "Bamboo Cutting Board",      "Kitchenware",    9.99),
    ("P006", "Glass Storage Jars",        "Kitchenware",   12.50),
    ("P007", "Wall Art Print",            "Home Decor",    14.00),
    ("P008", "Cotton Throw Blanket",      "Textiles",      22.00),
    ("P009", "Herb Garden Kit",           "Garden",         7.50),
    ("P010", "Beeswax Food Wraps",        "Kitchenware",    5.99),
    ("P011", "Copper Measuring Cups",     "Kitchenware",   16.00),
    ("P012", "Handmade Soap Set",         "Bath & Body",    9.00),
    ("P013", "Wooden Serving Board",      "Kitchenware",   19.99),
    ("P014", "Knitted Tea Cosy",          "Textiles",       5.50),
    ("P015", "Botanical Print Set",       "Home Decor",    24.99),
    ("P016", "Cast Iron Trivet",          "Kitchenware",   11.00),
    ("P017", "Macrame Wall Hanging",      "Home Decor",    32.00),
    ("P018", "Lavender Bath Salts",       "Bath & Body",    7.25),
    ("P019", "Rattan Storage Basket",     "Storage",       15.99),
    ("P020", "Recycled Glass Vase",       "Home Decor",    13.50),
]

def random_date(start="2022-01-01", end="2024-12-31"):
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end,   "%Y-%m-%d")
    return s + timedelta(days=random.randint(0, (e - s).days))

# ── 1. customers.csv ──────────────────────────────────────────────────────────
NUM_CUSTOMERS = 600
customers = []
for i in range(1, NUM_CUSTOMERS + 1):
    signup = random_date("2020-01-01", "2022-12-31")
    customers.append({
        "customer_id":   f"C{i:04d}",
        "country":       random.choice(COUNTRIES),
        "signup_date":   signup.strftime("%Y-%m-%d"),
        "age_group":     random.choice(["18-24","25-34","35-44","45-54","55-64","65+"]),
        "gender":        random.choice(["M","F","Other"]),
        "email_opt_in":  random.choice([1, 1, 1, 0]),   # 75% opted in
    })

with open(os.path.join(BASE_DIR, "customers.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=customers[0].keys())
    w.writeheader(); w.writerows(customers)
print(f"  customers.csv    -> {len(customers)} rows")

# ── 2. products.csv ───────────────────────────────────────────────────────────
with open(os.path.join(BASE_DIR, "products.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["product_id","product_name","category","unit_price"])
    w.writeheader()
    for pid, name, cat, price in PRODUCT_CATALOG:
        w.writerow({"product_id": pid, "product_name": name,
                    "category": cat, "unit_price": price})
print(f"  products.csv     -> {len(PRODUCT_CATALOG)} rows")

# ── 3. transactions.csv ───────────────────────────────────────────────────────
# Simulate realistic buying behaviour:
#   Champions     (~15%) – high freq, high spend, recent
#   Loyal         (~20%) – regular, medium spend
#   At Risk       (~20%) – used to buy, now silent
#   Hibernating   (~15%) – low freq, old
#   New           (~15%) – just signed up
#   Potential     (~15%) – moderate recent activity

def assign_segment(i):
    r = i % 100
    if r < 15:  return "champion"
    if r < 35:  return "loyal"
    if r < 55:  return "at_risk"
    if r < 70:  return "hibernating"
    if r < 85:  return "new"
    return "potential"

transactions = []
tid = 1
for c in customers:
    seg = assign_segment(int(c["customer_id"][1:]))

    if seg == "champion":
        num_orders = random.randint(15, 30)
        date_range = ("2024-06-01", "2024-12-31")
        qty_range  = (3, 10)
    elif seg == "loyal":
        num_orders = random.randint(8, 15)
        date_range = ("2024-01-01", "2024-12-31")
        qty_range  = (2, 6)
    elif seg == "at_risk":
        num_orders = random.randint(5, 10)
        date_range = ("2022-06-01", "2023-06-30")
        qty_range  = (1, 4)
    elif seg == "hibernating":
        num_orders = random.randint(1, 4)
        date_range = ("2022-01-01", "2022-12-31")
        qty_range  = (1, 3)
    elif seg == "new":
        num_orders = random.randint(1, 3)
        date_range = ("2024-10-01", "2024-12-31")
        qty_range  = (1, 4)
    else:  # potential
        num_orders = random.randint(3, 7)
        date_range = ("2024-03-01", "2024-12-31")
        qty_range  = (1, 5)

    for _ in range(num_orders):
        product = random.choice(PRODUCT_CATALOG)
        qty     = random.randint(*qty_range)
        price   = product[3] * random.uniform(0.95, 1.05)

        # ~2% returns (negative qty)
        if random.random() < 0.02:
            qty = -qty

        transactions.append({
            "transaction_id": f"T{tid:06d}",
            "customer_id":    c["customer_id"],
            "product_id":     product[0],
            "transaction_date": random_date(*date_range).strftime("%Y-%m-%d"),
            "quantity":       qty,
            "unit_price":     round(price, 2),
            "revenue":        round(qty * price, 2),
            "country":        c["country"],
            "channel":        random.choice(["Online","Mobile","In-Store","Partner"]),
        })
        tid += 1

with open(os.path.join(BASE_DIR, "transactions.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=transactions[0].keys())
    w.writeheader(); w.writerows(transactions)

print(f"  transactions.csv -> {len(transactions)} rows")
print(f"\n  Raw data ready -> data/raw/")
