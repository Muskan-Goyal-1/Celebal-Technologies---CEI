"""
clean_data.py
-------------
Loads the raw CSVs, cleans them with pandas, validates referential
integrity across tables, and writes cleaned CSVs.

Cleaning performed:
  - customers : drop exact duplicates, dedupe on customer_id (keep first),
                trim/normalize whitespace & casing in names, drop rows with
                missing email, parse signup_date (drop unparsable rows),
                fill missing segment with "Regular"
  - products  : drop exact duplicates, dedupe on product_id, normalize
                category casing, drop/fix invalid prices (null or negative)
  - orders    : drop exact duplicates, dedupe on order_id, parse order_date
                (drop unparsable / future-dated rows), drop rows whose
                customer_id doesn't exist in cleaned customers table
  - order_items: dedupe on order_item_id, drop rows with invalid quantity
                (<=0) or missing unit_price, drop rows whose order_id/
                product_id don't exist in the cleaned orders/products tables

Usage:
    python clean_data.py [--raw-dir ../data/raw] [--out-dir ../data/cleaned]
"""

import argparse
import os

import pandas as pd


def log(msg: str) -> None:
    print(f"  {msg}")


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset="customer_id", keep="first")

    df["name"] = df["name"].astype(str).str.strip().str.title()
    df = df.dropna(subset=["email"])
    df = df.drop_duplicates(subset="email", keep="first")

    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")
    df = df.dropna(subset=["signup_date"])

    df["segment"] = df["segment"].fillna("Regular")

    log(f"customers: {before} -> {len(df)} rows after cleaning")
    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset="product_id", keep="first")

    df["category"] = df["category"].astype(str).str.strip().str.title()
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])
    df = df[df["price"] > 0]

    log(f"products: {before} -> {len(df)} rows after cleaning")
    return df


def clean_orders(df: pd.DataFrame, valid_customer_ids: set) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset="order_id", keep="first")

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df = df.dropna(subset=["order_date"])

    # drop future-dated orders (bad data / data-entry error)
    today = pd.Timestamp.now().normalize()
    df = df[df["order_date"] <= today]

    df = df.dropna(subset=["customer_id"])
    df["customer_id"] = df["customer_id"].astype(int)
    df = df[df["customer_id"].isin(valid_customer_ids)]

    log(f"orders: {before} -> {len(df)} rows after cleaning")
    return df


def clean_order_items(df: pd.DataFrame, valid_order_ids: set, valid_product_ids: set) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset="order_item_id", keep="first")

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df = df.dropna(subset=["quantity", "unit_price"])
    df = df[(df["quantity"] > 0) & (df["unit_price"] > 0)]
    df["quantity"] = df["quantity"].astype(int)

    df = df[df["order_id"].isin(valid_order_ids)]
    df = df[df["product_id"].isin(valid_product_ids)]

    log(f"order_items: {before} -> {len(df)} rows after cleaning")
    return df


def main():
    parser = argparse.ArgumentParser(description="Clean raw e-commerce datasets")
    parser.add_argument("--raw-dir", type=str, default="../data/raw")
    parser.add_argument("--out-dir", type=str, default="../data/cleaned")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    print("Loading raw CSVs...")
    customers = pd.read_csv(f"{args.raw_dir}/customers.csv")
    products = pd.read_csv(f"{args.raw_dir}/products.csv")
    orders = pd.read_csv(f"{args.raw_dir}/orders.csv")
    order_items = pd.read_csv(f"{args.raw_dir}/order_items.csv")

    print("Cleaning...")
    customers_clean = clean_customers(customers)
    products_clean = clean_products(products)
    orders_clean = clean_orders(orders, set(customers_clean["customer_id"]))
    order_items_clean = clean_order_items(
        order_items,
        set(orders_clean["order_id"]),
        set(products_clean["product_id"]),
    )

    # final referential-integrity check (should print 0 orphans on both)
    orphan_orders = (~orders_clean["customer_id"].isin(customers_clean["customer_id"])).sum()
    orphan_items = (
        (~order_items_clean["order_id"].isin(orders_clean["order_id"])).sum()
        + (~order_items_clean["product_id"].isin(products_clean["product_id"])).sum()
    )
    print(f"Referential integrity check -> orphan orders: {orphan_orders}, orphan order_items: {orphan_items}")
    assert orphan_orders == 0 and orphan_items == 0, "Referential integrity violated!"

    customers_clean.to_csv(f"{args.out_dir}/customers_clean.csv", index=False)
    products_clean.to_csv(f"{args.out_dir}/products_clean.csv", index=False)
    orders_clean.to_csv(f"{args.out_dir}/orders_clean.csv", index=False)
    order_items_clean.to_csv(f"{args.out_dir}/order_items_clean.csv", index=False)

    print("Cleaned data written to:", args.out_dir)


if __name__ == "__main__":
    main()
