"""
load_to_db.py
-------------
Creates the SQLite database from sql/schema.sql and loads the cleaned
CSVs into it. Prints row counts and a couple of relationship sanity
checks at the end.

Usage:
    python load_to_db.py [--db ../ecommerce.db] [--clean-dir ../data/cleaned] [--schema ../sql/schema.sql]
"""

import argparse
import os
import sqlite3

import pandas as pd


def main():
    parser = argparse.ArgumentParser(description="Load cleaned CSVs into SQLite")
    parser.add_argument("--db", type=str, default="../ecommerce.db")
    parser.add_argument("--clean-dir", type=str, default="../data/cleaned")
    parser.add_argument("--schema", type=str, default="../sql/schema.sql")
    args = parser.parse_args()

    if os.path.exists(args.db):
        os.remove(args.db)

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA foreign_keys = ON;")

    print("Creating schema...")
    with open(args.schema, "r") as f:
        conn.executescript(f.read())

    print("Loading cleaned CSVs...")
    tables = {
        "customers": "customers_clean.csv",
        "products": "products_clean.csv",
        "orders": "orders_clean.csv",
        "order_items": "order_items_clean.csv",
    }

    for table, filename in tables.items():
        df = pd.read_csv(f"{args.clean_dir}/{filename}")
        df.to_sql(table, conn, if_exists="append", index=False)
        print(f"  loaded {len(df):>6} rows -> {table}")

    print("\nRow counts in DB:")
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<15} {count}")

    print("\nRelationship sanity checks:")
    orphan_orders = conn.execute(
        "SELECT COUNT(*) FROM orders o LEFT JOIN customers c ON o.customer_id = c.customer_id WHERE c.customer_id IS NULL"
    ).fetchone()[0]
    orphan_items = conn.execute(
        "SELECT COUNT(*) FROM order_items oi "
        "LEFT JOIN orders o ON oi.order_id = o.order_id "
        "LEFT JOIN products p ON oi.product_id = p.product_id "
        "WHERE o.order_id IS NULL OR p.product_id IS NULL"
    ).fetchone()[0]
    print(f"  orphan orders (no matching customer): {orphan_orders}")
    print(f"  orphan order_items (no matching order/product): {orphan_items}")

    conn.commit()
    conn.close()
    print(f"\nDatabase written to {args.db}")


if __name__ == "__main__":
    main()
