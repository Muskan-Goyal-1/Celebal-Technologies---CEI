# E-Commerce Order Analytics System

An end-to-end analytics pipeline: synthetic (intentionally messy) e-commerce
data → pandas cleaning → SQLite warehouse → SQL analytics (joins,
aggregations, window functions, CTEs, cohort/retention, RFM segmentation) →
a CLI reporting tool.

## 1. Architecture

```
generate_data.py  →  data/raw/*.csv        (dirty, realistic data)
        │
        ▼
clean_data.py     →  data/cleaned/*.csv    (validated, referentially clean)
        │
        ▼
load_to_db.py     →  ecommerce.db (SQLite) (schema.sql defines PK/FK/CHECK)
        │
        ▼
sql/*.sql          ─  ad-hoc analytics queries you can run directly
        │
        ▼
report_cli.py     →  formatted terminal reports (tabulate)
```

**Tables**

| Table         | Key columns                                              |
|---------------|-----------------------------------------------------------|
| `customers`   | `customer_id` PK, `email` UNIQUE, `signup_date`, `segment` |
| `products`    | `product_id` PK, `category`, `price` (CHECK > 0)          |
| `orders`      | `order_id` PK, `customer_id` FK → customers, `status`      |
| `order_items` | `order_item_id` PK, `order_id` FK, `product_id` FK, `quantity`/`unit_price` (CHECK > 0) |

## 2. Data quality: what's injected, and how it's fixed

`generate_data.py` deliberately injects: null emails/prices, duplicate rows,
duplicate primary keys, orders/order_items pointing at non-existent
customers/orders/products, unparsable and future-dated timestamps,
negative/zero prices and quantities, and inconsistent text casing/whitespace.

`clean_data.py` (pandas) then:
- drops exact duplicates and de-dupes on primary key (`keep="first"`)
- coerces dates/numbers with `errors="coerce"` and drops rows that fail to parse
- drops rows with nulls in required fields (email, price, quantity, unit_price)
- drops negative/zero prices and quantities
- **enforces referential integrity** top-down: customers → orders → order_items,
  filtering out any child row whose foreign key has no matching parent
- asserts zero orphan rows before writing cleaned CSVs

## 3. Setup & how to run

```bash
cd scripts
pip install faker pandas tabulate

# 1. Generate raw (messy) data
python generate_data.py --seed 42 --out-dir ../data/raw

# 2. Clean it with pandas
python clean_data.py --raw-dir ../data/raw --out-dir ../data/cleaned

# 3. Load into SQLite (creates ecommerce.db in project root)
python load_to_db.py --db ../ecommerce.db --clean-dir ../data/cleaned --schema ../sql/schema.sql

# 4. Explore with raw SQL (optional)
sqlite3 ../ecommerce.db < ../sql/aggregations.sql

# 5. Run reports via the CLI
python report_cli.py --list
python report_cli.py --report revenue --limit 10
python report_cli.py --report top_products --order-by quantity --limit 10
python report_cli.py --report retention
python report_cli.py --report rfm --format csv
```

## 4. CLI reference

```
python report_cli.py --report <name> [--db PATH] [--limit N] [--order-by revenue|quantity] [--format table|csv]
```

| Report                 | Description                                             |
|-------------------------|----------------------------------------------------------|
| `revenue`               | Total revenue per customer                                |
| `revenue_by_month`      | Total revenue per month                                   |
| `revenue_by_category`   | Total revenue per product category                        |
| `top_customers`         | Customers ranked by lifetime value (`RANK()`)              |
| `top_products`          | Top products, sortable by `--order-by revenue\|quantity`  |
| `aov_by_segment`        | Average order value by customer segment                    |
| `retention`             | Monthly retention % per acquisition cohort                 |
| `segmentation`          | Frequency tier (one-time/occasional/loyal) + spend tier     |
| `rfm`                   | Recency/Frequency/Monetary scores (`NTILE(4)`) per customer |

Edge-case handling: missing database → clear error + exit code 1; unknown
report name → error + suggests `--list`; empty result sets → a friendly
message instead of a blank/broken table; non-positive `--limit` → validation
error before hitting the database.

## 5. SQL highlights

- **`sql/aggregations.sql`** – revenue by customer/category/month, top
  products, AOV by segment, all via multi-table `JOIN`s.
- **`sql/window_functions.sql`** – `RANK()`/`DENSE_RANK()` for LTV leaderboard,
  `SUM() OVER` running totals, `AVG() OVER (... ROWS BETWEEN 2 PRECEDING ...)`
  moving average, `LAG()`-based month-over-month growth rate via chained CTEs.
- **`sql/cohort_analysis.sql`** – cohort assignment by first-purchase month,
  a month-number retention matrix, churned-vs-repeat classification, and a
  combined frequency-tier / spend-tier / RFM (`NTILE(4)`) segmentation.

## 6. Sample output

See `output/sample_reports/` for captured CLI output (`--limit 10-15`) of
every report type, generated from the seeded dataset — e.g.
`output/sample_reports/revenue.txt`, `output/sample_reports/rfm.txt`,
`output/sample_reports/retention.txt`.

## 7. Notes & assumptions

- Only orders with `status IN ('completed', 'shipped')` count toward revenue
  figures — `pending`/`cancelled`/`returned` orders are excluded from money
  metrics but still exist in the `orders` table for status reporting.
- "Churned" is defined as a single-order customer whose last order was more
  than 90 days before the most recent order date in the dataset (see
  `sql/cohort_analysis.sql` §3) — an adjustable heuristic, not a hard rule.
- The dataset is synthetic and reproducible via `--seed`; re-running
  `generate_data.py` with the same seed produces identical raw data.
