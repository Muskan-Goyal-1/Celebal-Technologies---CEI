"""
generate_data.py
-----------------
Generates realistic (and intentionally messy) e-commerce datasets:
customers, products, orders, order_items.

Messiness injected on purpose so the cleaning step (clean_data.py) has
real work to do:
  - null values in optional/required-looking fields
  - duplicate rows / duplicate primary keys
  - mismatched foreign keys (orders referencing non-existent customers,
    order_items referencing non-existent orders/products)
  - invalid / malformed dates
  - inconsistent casing & whitespace in text fields
  - negative or zero quantities/prices

Usage:
    python generate_data.py [--seed 42] [--out-dir ../data/raw]
"""

import argparse
import csv
import random
from datetime import datetime, timedelta

from faker import Faker

# ---------------------------------------------------------------- config ---

N_CUSTOMERS = 500
N_PRODUCTS = 120
N_ORDERS = 3000
MAX_ITEMS_PER_ORDER = 5

CATEGORIES = [
    "Electronics", "Home & Kitchen", "Books", "Clothing",
    "Sports & Outdoors", "Beauty", "Toys", "Grocery",
]

ORDER_STATUSES = ["completed", "pending", "cancelled", "returned", "shipped"]


def make_faker(seed: int) -> Faker:
    fake = Faker()
    Faker.seed(seed)
    random.seed(seed)
    return fake


# ------------------------------------------------------------ customers ---

def generate_customers(fake: Faker, n: int) -> list[dict]:
    rows = []
    start = datetime(2022, 1, 1)
    end = datetime(2026, 6, 30)

    for i in range(1, n + 1):
        customer_id = i
        name = fake.name()
        email = fake.email()
        signup_date = fake.date_time_between(start_date=start, end_date=end)
        segment = random.choice(["Regular", "Premium", "VIP", None])
        country = fake.country()

        # --- inject messiness -------------------------------------------
        if random.random() < 0.03:
            email = None  # missing email
        if random.random() < 0.02:
            name = f"  {name.upper()}  "  # whitespace / casing issue
        if random.random() < 0.015:
            signup_date = "not-a-date"  # invalid date string

        rows.append({
            "customer_id": customer_id,
            "name": name,
            "email": email,
            "signup_date": signup_date if isinstance(signup_date, str) else signup_date.strftime("%Y-%m-%d"),
            "segment": segment,
            "country": country,
        })

    # duplicate a handful of rows (exact duplicates)
    dupes = random.sample(rows, k=max(1, n // 100))
    rows.extend(dupes)

    # duplicate PK but different data (data integrity issue)
    for _ in range(3):
        base = random.choice(rows).copy()
        base["email"] = fake.email()
        rows.append(base)

    random.shuffle(rows)
    return rows


# ------------------------------------------------------------- products ---

def generate_products(fake: Faker, n: int) -> list[dict]:
    rows = []
    for i in range(1, n + 1):
        product_id = i
        name = fake.catch_phrase()
        category = random.choice(CATEGORIES)
        price = round(random.uniform(3, 500), 2)

        # --- inject messiness -------------------------------------------
        if random.random() < 0.02:
            price = -abs(price)  # negative price
        if random.random() < 0.02:
            price = None  # missing price
        if random.random() < 0.03:
            category = category.lower()  # inconsistent casing

        rows.append({
            "product_id": product_id,
            "product_name": name,
            "category": category,
            "price": price,
        })

    dupes = random.sample(rows, k=max(1, n // 40))
    rows.extend(dupes)
    random.shuffle(rows)
    return rows


# --------------------------------------------------------------- orders ---

def generate_orders(fake: Faker, n: int, n_customers: int) -> list[dict]:
    rows = []
    start = datetime(2023, 1, 1)
    end = datetime(2026, 6, 30)

    for i in range(1, n + 1):
        order_id = i
        # 2% of orders reference a non-existent customer (bad FK)
        if random.random() < 0.02:
            customer_id = n_customers + random.randint(1, 50)
        else:
            customer_id = random.randint(1, n_customers)

        order_date = fake.date_time_between(start_date=start, end_date=end)
        status = random.choice(ORDER_STATUSES)

        # --- inject messiness -------------------------------------------
        date_str = order_date.strftime("%Y-%m-%d")
        if random.random() < 0.01:
            date_str = "2026-13-45"  # invalid date
        if random.random() < 0.01:
            date_str = (datetime(2027, 1, 1) + timedelta(days=random.randint(1, 300))).strftime("%Y-%m-%d")  # future date
        if random.random() < 0.02:
            customer_id = None  # missing FK

        rows.append({
            "order_id": order_id,
            "customer_id": customer_id,
            "order_date": date_str,
            "status": status,
        })

    dupes = random.sample(rows, k=max(1, n // 150))
    rows.extend(dupes)
    random.shuffle(rows)
    return rows


# ---------------------------------------------------------- order_items ---

def generate_order_items(n_orders: int, n_products: int) -> list[dict]:
    rows = []
    item_id = 1
    for order_id in range(1, n_orders + 1):
        n_items = random.randint(1, MAX_ITEMS_PER_ORDER)
        for _ in range(n_items):
            # 1.5% reference a non-existent product (bad FK)
            if random.random() < 0.015:
                product_id = n_products + random.randint(1, 30)
            else:
                product_id = random.randint(1, n_products)

            # 1% reference a non-existent order (bad FK)
            oid = order_id
            if random.random() < 0.01:
                oid = n_orders + random.randint(1, 50)

            quantity = random.randint(1, 6)
            unit_price = round(random.uniform(3, 500), 2)

            # --- inject messiness ----------------------------------------
            if random.random() < 0.02:
                quantity = 0  # invalid quantity
            if random.random() < 0.01:
                quantity = -quantity  # negative quantity
            if random.random() < 0.02:
                unit_price = None

            rows.append({
                "order_item_id": item_id,
                "order_id": oid,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
            })
            item_id += 1

    random.shuffle(rows)
    return rows


# ------------------------------------------------------------------- io ---

def write_csv(path: str, rows: list[dict], fieldnames: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {len(rows):>6} rows -> {path}")


def main():
    parser = argparse.ArgumentParser(description="Generate raw e-commerce datasets")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", type=str, default="../data/raw")
    args = parser.parse_args()

    fake = make_faker(args.seed)

    print("Generating datasets...")
    customers = generate_customers(fake, N_CUSTOMERS)
    products = generate_products(fake, N_PRODUCTS)
    orders = generate_orders(fake, N_ORDERS, N_CUSTOMERS)
    order_items = generate_order_items(N_ORDERS, N_PRODUCTS)

    import os
    os.makedirs(args.out_dir, exist_ok=True)

    write_csv(f"{args.out_dir}/customers.csv", customers,
              ["customer_id", "name", "email", "signup_date", "segment", "country"])
    write_csv(f"{args.out_dir}/products.csv", products,
              ["product_id", "product_name", "category", "price"])
    write_csv(f"{args.out_dir}/orders.csv", orders,
              ["order_id", "customer_id", "order_date", "status"])
    write_csv(f"{args.out_dir}/order_items.csv", order_items,
              ["order_item_id", "order_id", "product_id", "quantity", "unit_price"])

    print("Done. Raw (intentionally dirty) data written to:", args.out_dir)


if __name__ == "__main__":
    main()
