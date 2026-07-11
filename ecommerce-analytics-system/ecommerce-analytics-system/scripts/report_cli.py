"""
report_cli.py
-------------
Command-line reporting tool for the e-commerce analytics database.

Usage:
    python report_cli.py --report revenue
    python report_cli.py --report revenue_by_month
    python report_cli.py --report revenue_by_category
    python report_cli.py --report top_customers --limit 10
    python report_cli.py --report top_products --limit 10 --order-by revenue
    python report_cli.py --report aov_by_segment
    python report_cli.py --report retention
    python report_cli.py --report segmentation
    python report_cli.py --report rfm --limit 20
    python report_cli.py --list                # list available reports

Options:
    --db PATH        path to the sqlite database (default: ../ecommerce.db)
    --limit N         limit rows returned where applicable (default: 20)
    --order-by FIELD  for top_products: 'revenue' or 'quantity' (default: revenue)
    --format FORMAT   'table' (default) or 'csv'
"""

import argparse
import os
import sqlite3
import sys

try:
    from tabulate import tabulate
    HAVE_TABULATE = True
except ImportError:
    HAVE_TABULATE = False


# --------------------------------------------------------------- queries ---

QUERIES = {
    "revenue": """
        SELECT
            c.customer_id,
            c.name,
            c.segment,
            ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue,
            COUNT(DISTINCT o.order_id)                 AS order_count
        FROM customers c
        JOIN orders o       ON o.customer_id = c.customer_id
        JOIN order_items oi ON oi.order_id   = o.order_id
        WHERE o.status IN ('completed', 'shipped')
        GROUP BY c.customer_id, c.name, c.segment
        ORDER BY total_revenue DESC
        LIMIT ?;
    """,
    "revenue_by_month": """
        SELECT
            strftime('%Y-%m', o.order_date) AS month,
            ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue,
            COUNT(DISTINCT o.order_id)                 AS order_count
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status IN ('completed', 'shipped')
        GROUP BY month
        ORDER BY month
        LIMIT ?;
    """,
    "revenue_by_category": """
        SELECT
            p.category,
            ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue,
            SUM(oi.quantity)                            AS units_sold
        FROM order_items oi
        JOIN products p ON p.product_id = oi.product_id
        JOIN orders o    ON o.order_id  = oi.order_id
        WHERE o.status IN ('completed', 'shipped')
        GROUP BY p.category
        ORDER BY total_revenue DESC
        LIMIT ?;
    """,
    "top_customers": """
        WITH customer_ltv AS (
            SELECT
                c.customer_id,
                c.name,
                c.segment,
                ROUND(SUM(oi.quantity * oi.unit_price), 2) AS lifetime_value
            FROM customers c
            JOIN orders o        ON o.customer_id = c.customer_id
            JOIN order_items oi  ON oi.order_id   = o.order_id
            WHERE o.status IN ('completed', 'shipped')
            GROUP BY c.customer_id, c.name, c.segment
        )
        SELECT
            customer_id, name, segment, lifetime_value,
            RANK() OVER (ORDER BY lifetime_value DESC) AS ltv_rank
        FROM customer_ltv
        ORDER BY lifetime_value DESC
        LIMIT ?;
    """,
    "top_products_revenue": """
        SELECT
            p.product_id, p.product_name, p.category,
            SUM(oi.quantity)                           AS total_quantity_sold,
            ROUND(SUM(oi.quantity * oi.unit_price), 2)  AS total_revenue
        FROM order_items oi
        JOIN products p ON p.product_id = oi.product_id
        JOIN orders o    ON o.order_id  = oi.order_id
        WHERE o.status IN ('completed', 'shipped')
        GROUP BY p.product_id, p.product_name, p.category
        ORDER BY total_revenue DESC
        LIMIT ?;
    """,
    "top_products_quantity": """
        SELECT
            p.product_id, p.product_name, p.category,
            SUM(oi.quantity)                           AS total_quantity_sold,
            ROUND(SUM(oi.quantity * oi.unit_price), 2)  AS total_revenue
        FROM order_items oi
        JOIN products p ON p.product_id = oi.product_id
        JOIN orders o    ON o.order_id  = oi.order_id
        WHERE o.status IN ('completed', 'shipped')
        GROUP BY p.product_id, p.product_name, p.category
        ORDER BY total_quantity_sold DESC
        LIMIT ?;
    """,
    "aov_by_segment": """
        WITH order_totals AS (
            SELECT o.order_id, o.customer_id, SUM(oi.quantity * oi.unit_price) AS order_value
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            WHERE o.status IN ('completed', 'shipped')
            GROUP BY o.order_id, o.customer_id
        )
        SELECT
            c.segment,
            COUNT(ot.order_id)            AS num_orders,
            ROUND(AVG(ot.order_value), 2) AS avg_order_value
        FROM order_totals ot
        JOIN customers c ON c.customer_id = ot.customer_id
        GROUP BY c.segment
        ORDER BY avg_order_value DESC
        LIMIT ?;
    """,
    "retention": """
        WITH first_purchase AS (
            SELECT customer_id, MIN(strftime('%Y-%m', order_date)) AS cohort_month
            FROM orders WHERE status IN ('completed', 'shipped')
            GROUP BY customer_id
        ),
        activity AS (
            SELECT DISTINCT customer_id, strftime('%Y-%m', order_date) AS active_month
            FROM orders WHERE status IN ('completed', 'shipped')
        ),
        cohort_activity AS (
            SELECT
                fp.cohort_month, fp.customer_id, a.active_month,
                (CAST(strftime('%Y', a.active_month || '-01') AS INTEGER) - CAST(strftime('%Y', fp.cohort_month || '-01') AS INTEGER)) * 12
                + (CAST(strftime('%m', a.active_month || '-01') AS INTEGER) - CAST(strftime('%m', fp.cohort_month || '-01') AS INTEGER)) AS month_number
            FROM first_purchase fp JOIN activity a ON a.customer_id = fp.customer_id
        ),
        cohort_sizes AS (
            SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
            FROM first_purchase GROUP BY cohort_month
        )
        SELECT
            ca.cohort_month, ca.month_number,
            COUNT(DISTINCT ca.customer_id) AS active_customers,
            cs.cohort_size,
            ROUND(100.0 * COUNT(DISTINCT ca.customer_id) / cs.cohort_size, 1) AS retention_pct
        FROM cohort_activity ca
        JOIN cohort_sizes cs ON cs.cohort_month = ca.cohort_month
        GROUP BY ca.cohort_month, ca.month_number
        ORDER BY ca.cohort_month, ca.month_number
        LIMIT ?;
    """,
    "segmentation": """
        WITH customer_orders AS (
            SELECT o.customer_id,
                   COUNT(DISTINCT o.order_id) AS frequency,
                   SUM(oi.quantity * oi.unit_price) AS monetary
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            WHERE o.status IN ('completed', 'shipped')
            GROUP BY o.customer_id
        )
        SELECT
            customer_id, frequency, ROUND(monetary, 2) AS monetary,
            CASE
                WHEN frequency = 1 THEN 'one-time'
                WHEN frequency BETWEEN 2 AND 4 THEN 'occasional'
                ELSE 'loyal'
            END AS frequency_tier,
            CASE
                WHEN monetary < 100 THEN 'low'
                WHEN monetary < 500 THEN 'medium'
                ELSE 'high'
            END AS spend_tier
        FROM customer_orders
        ORDER BY monetary DESC
        LIMIT ?;
    """,
    "rfm": """
        WITH customer_orders AS (
            SELECT o.customer_id,
                   COUNT(DISTINCT o.order_id) AS frequency,
                   SUM(oi.quantity * oi.unit_price) AS monetary,
                   MAX(o.order_date) AS last_order_date
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            WHERE o.status IN ('completed', 'shipped')
            GROUP BY o.customer_id
        ),
        dataset_max_date AS (SELECT MAX(order_date) AS max_date FROM orders),
        rfm_base AS (
            SELECT
                co.customer_id,
                CAST(julianday((SELECT max_date FROM dataset_max_date)) - julianday(co.last_order_date) AS INTEGER) AS recency_days,
                co.frequency, ROUND(co.monetary, 2) AS monetary
            FROM customer_orders co
        ),
        rfm_scored AS (
            SELECT customer_id, recency_days, frequency, monetary,
                   NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,
                   NTILE(4) OVER (ORDER BY frequency DESC)   AS f_score,
                   NTILE(4) OVER (ORDER BY monetary DESC)    AS m_score
            FROM rfm_base
        )
        SELECT customer_id, recency_days, frequency, monetary,
               r_score, f_score, m_score, (r_score + f_score + m_score) AS rfm_total_score
        FROM rfm_scored
        ORDER BY rfm_total_score DESC
        LIMIT ?;
    """,
}

REPORT_DESCRIPTIONS = {
    "revenue": "Total revenue per customer",
    "revenue_by_month": "Total revenue per month",
    "revenue_by_category": "Total revenue per product category",
    "top_customers": "Customers ranked by lifetime value",
    "top_products_revenue": "Top products by revenue",
    "top_products_quantity": "Top products by quantity sold",
    "aov_by_segment": "Average order value by customer segment",
    "retention": "Monthly retention rate per acquisition cohort",
    "segmentation": "Customers segmented by frequency & spend tier",
    "rfm": "RFM (Recency, Frequency, Monetary) scoring per customer",
}


# ------------------------------------------------------------------ core ---

def get_connection(db_path: str) -> sqlite3.Connection:
    if not os.path.exists(db_path):
        print(f"Error: database not found at '{db_path}'.")
        print("Run load_to_db.py first to create it.")
        sys.exit(1)
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1;")  # sanity ping
        return conn
    except sqlite3.Error as e:
        print(f"Error: could not connect to database '{db_path}': {e}")
        sys.exit(1)


def run_report(conn: sqlite3.Connection, report: str, limit: int, order_by: str) -> tuple[list[str], list[tuple]]:
    key = report
    if report == "top_products":
        key = "top_products_revenue" if order_by == "revenue" else "top_products_quantity"

    if key not in QUERIES:
        print(f"Error: unknown report '{report}'.")
        print("Use --list to see available reports.")
        sys.exit(1)

    cur = conn.cursor()
    try:
        cur.execute(QUERIES[key], (limit,))
    except sqlite3.Error as e:
        print(f"Error running report '{report}': {e}")
        sys.exit(1)

    columns = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return columns, rows


def print_results(columns: list[str], rows: list[tuple], fmt: str) -> None:
    if not rows:
        print("(no results found for this report / filter combination)")
        return

    if fmt == "csv":
        print(",".join(columns))
        for row in rows:
            print(",".join(str(v) for v in row))
        return

    if HAVE_TABULATE:
        print(tabulate(rows, headers=columns, tablefmt="psql", floatfmt=".2f"))
    else:
        # graceful fallback if tabulate isn't installed
        widths = [max(len(str(c)), *(len(str(r[i])) for r in rows)) for i, c in enumerate(columns)]
        header = " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(columns))
        print(header)
        print("-" * len(header))
        for row in rows:
            print(" | ".join(str(v).ljust(widths[i]) for i, v in enumerate(row)))


def list_reports() -> None:
    print("Available reports:\n")
    seen = set()
    for name, desc in REPORT_DESCRIPTIONS.items():
        display = "top_products" if name.startswith("top_products") else name
        if display in seen:
            continue
        seen.add(display)
        shown_desc = "Top products by revenue or quantity sold" if display == "top_products" else desc
        print(f"  {display:<22} {shown_desc}")
    print("\n(top_products supports --order-by revenue|quantity)")


# ------------------------------------------------------------------ main ---

def main():
    parser = argparse.ArgumentParser(
        description="E-commerce analytics CLI reporting tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--report", type=str, help="report to run (see --list)")
    parser.add_argument("--db", type=str, default="../ecommerce.db", help="path to sqlite db")
    parser.add_argument("--limit", type=int, default=20, help="max rows to return")
    parser.add_argument("--order-by", type=str, default="revenue", choices=["revenue", "quantity"],
                         help="for top_products: sort by revenue or quantity")
    parser.add_argument("--format", type=str, default="table", choices=["table", "csv"], help="output format")
    parser.add_argument("--list", action="store_true", help="list available reports and exit")
    args = parser.parse_args()

    if args.list:
        list_reports()
        return

    if not args.report:
        parser.print_help()
        print("\nError: --report is required (or use --list to see options).")
        sys.exit(1)

    if args.limit <= 0:
        print("Error: --limit must be a positive integer.")
        sys.exit(1)

    conn = get_connection(args.db)
    try:
        columns, rows = run_report(conn, args.report, args.limit, args.order_by)
        print(f"\n=== Report: {args.report} (limit={args.limit}) ===\n")
        print_results(columns, rows, args.format)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
