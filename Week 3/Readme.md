# Superstore Sales Analysis — SQL Task
**Submitted by:** Muskan Goyal
**Week:** SQL Advanced Concepts — Subqueries, CTEs & Window Functions
**Dataset:** [Superstore Dataset Final](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final) · via Kaggle

---

## Objective

Analyze sales data from the Superstore dataset using advanced SQL concepts:
- **Subqueries** (scalar and correlated)
- **CTEs** (Common Table Expressions)
- **Window Functions** (`RANK`, `DENSE_RANK`, `ROW_NUMBER`, `PARTITION BY`)

---

## Environment

| Tool | Details |
|---|---|
| Platform | Kaggle Notebook |
| Language | Python 3.12 |
| Database | SQLite (in-memory via `sqlite3`) |
| Data Loader | `kagglehub.dataset_load()` with `KaggleDatasetAdapter.PANDAS` |
| Key Libraries | `pandas`, `kagglehub`, `sqlite3`, `IPython.display` |

---

## Project Structure

```
Superstore SQL Task/
│
├── README.md                   ← this file
└── superstore_analysis.sql     ← complete SQL query reference
```

---

## Step 1 — Data Setup

The dataset was loaded directly from Kaggle using `kagglehub` and pushed into an in-memory SQLite database as `superstore_raw` (9,994 rows × 21 columns).

Three normalised tables were created from it using `SELECT DISTINCT`:

| Table | Key Columns |
|---|---|
| `customers` | customer_id, customer_name, segment, city, state, region |
| `orders` | order_id, order_date, ship_mode, customer_id, product_id, sales, quantity, discount, profit |
| `products` | product_id, product_name, category, sub_category |

---

## Step 2 — Queries Performed

### Subqueries
| # | Query | Technique |
|---|---|---|
| Q1 | Orders where sales > average sales | Scalar subquery in `WHERE` |
| Q2 | Highest-sales order per customer | Correlated subquery |

### CTEs
| # | Query | Technique |
|---|---|---|
| Q3 | Total sales per customer | Simple CTE |
| Q4 | Customers with above-average total sales | CTE + Scalar subquery |

### Window Functions
| # | Query | Technique |
|---|---|---|
| Q5 | Rank all customers by total sales | `RANK()` + `DENSE_RANK()` |
| Q6 | Row number per order within each customer | `ROW_NUMBER()` + `PARTITION BY` |
| Q7 | Top 3 customers by total sales | `DENSE_RANK()` with filter |

---

##  Step 3 — Final Combined Query

A single query combining **JOIN + CTE + Window Function** to display:

| Output Column | Source |
|---|---|
| `customer_name` | `customers` table via JOIN |
| `total_sales` | Aggregated in CTE |
| `rank` | `RANK()` window function |

---

##  Mini Project — Customer Sales Insights

Five business questions answered using SQL:

| # | Question | Technique Used |
|---|---|---|
| 1 | Who are the top 5 customers? | CTE + `DENSE_RANK()` DESC |
| 2 | Who are the bottom 5 customers? | CTE + `DENSE_RANK()` ASC |
| 3 | Which customers made only one order? | `HAVING COUNT(DISTINCT order_id) = 1` |
| 4 | Which customers have above-average sales? | CTE + Subquery |
| 5 | What is the highest order value per customer? | Correlated subquery |

---

## Key Concepts Demonstrated

**Subquery** — A query nested inside another query. Used to compute aggregates (like `AVG`) or find matching rows (like `MAX` per group) dynamically.

**CTE (Common Table Expression)** — A named temporary result set defined with `WITH`. Makes complex queries readable and reusable within the same statement.

**Window Function** — Performs a calculation across a set of rows related to the current row without collapsing them into a single output row (unlike `GROUP BY`). Key functions used:
- `RANK()` — assigns rank with gaps on ties
- `DENSE_RANK()` — assigns rank without gaps on ties
- `ROW_NUMBER()` — unique sequential number per partition

---

*Submitted by Muskan Goyal*
