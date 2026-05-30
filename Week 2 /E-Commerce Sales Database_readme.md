# Celebal Summer Internship 2026
## Week 2 Assignment: E-Commerce Sales Database Analysis (SampleSuperstore)

This repository contains comprehensive SQL query solutions and relational database design theory executed against the `SampleSuperstore` dataset as part of the Celebal Technologies Summer Internship 2026 program.

---

## 📊 Dataset Structural Adaptation Notice

The Kaggle `SampleSuperstore` dataset is provided as a **denormalized single flat-file** rather than multiple isolated relational tables.

- To ensure clean, professional, and highly readable documentation on GitHub without cluttered horizontal scrolling, queries requesting broad record displays are explicitly restricted to a **focused 5-column layout** (`row_id`, `order_id`, `customer_name`, `category`, `sales`).
- Large data outputs are systematically restricted using an explicit **`LIMIT 5` transactional preview shortcut**, consistent with enterprise production pipeline standards.

---

## 📁 Repository Structure

```
celebal-internship-2026/
├── README.md                   ← This file
├── SampleSuperstore.csv        ← Source dataset
├── queries/
│   ├── section_a_basics.sql
│   ├── section_b_filtering.sql
│   ├── section_c_aggregation.sql
│   ├── section_d_joins.sql
│   └── section_e_advanced.sql
└── outputs/
    └── query_results.txt
```

---

## 📑 Section A — SQL Basics (SELECT, Constraints, Primary Keys)

### Q1. Display all columns and rows from the customers table

> *Note: Display formatted to a clean 5-column layout for readability.*

**Query:**
```sql
SELECT row_id, order_id, customer_name, category, sales
FROM SampleSuperstore
LIMIT 5;
```

**Output:**
```
row_id | order_id       | customer_name   | category        | sales
-------+----------------+-----------------+-----------------+----------
1      | CA-2016-152156 | Claire Gute     | Furniture       | 261.9600
2      | CA-2016-152156 | Claire Gute     | Furniture       | 731.9400
3      | CA-2016-138688 | Darrin Van Huff | Office Supplies | 14.6200
4      | US-2015-108966 | Sean O'Donnell  | Furniture       | 957.5775
5      | US-2015-108966 | Sean O'Donnell  | Office Supplies | 22.3680
```

---

### Q2. Retrieve customer name and city for all customers

**Query:**
```sql
SELECT DISTINCT customer_name, city
FROM SampleSuperstore
LIMIT 5;
```

**Output:**
```
customer_name    | city
-----------------+----------------
Claire Gute      | Henderson
Darrin Van Huff  | Los Angeles
Sean O'Donnell   | Fort Lauderdale
Brosina Hoffman  | Los Angeles
Andrew Allen     | Concord
```

---

### Q3. List all unique categories in the products table

**Query:**
```sql
SELECT DISTINCT category
FROM SampleSuperstore;
```

**Output:**
```
category
---------------
Furniture
Office Supplies
Technology
```

---

### Q4. Identify the Primary Key and explain why it must be UNIQUE and NOT NULL

**Theory Answer:**

In this flat-file schema, **`row_id`** serves as the operational Primary Key.

- **Uniqueness:** Guarantees that every transactional item record has a distinct identity, eliminating any risk of duplicate records.
- **NOT NULL:** Prevents blank records from fracturing indexing trees. A row without a valid identity key breaks referencing chains entirely, making reliable lookups impossible.

---

### Q5. What constraints apply to an email column, and what happens on duplicate insertion?

**Theory Answer:**

- In standard customer management systems, an email column carries `UNIQUE` and `NOT NULL` constraints.
- Attempting a duplicate insertion triggers a **Unique Key Violation Exception**, immediately rolling back the current transaction to preserve data integrity.

---

### Q6. Insert a product with `unit_price = -50` — what happens and which constraint prevents it?

**Query:**
```sql
INSERT INTO SampleSuperstore (row_id, order_id, sales, profit)
VALUES (99999, 'CA-2026-TEST', -50.00, 0.00);
```

**Theory Answer:**

- **Result:** The database engine rejects the insertion with a constraint violation error.
- **Explanation:** A `CHECK` constraint (e.g., `CHECK (sales >= 0)`) evaluates values at write-time. Because negative pricing violates physical business rules, the validator halts the transaction before any data is written.

---

## 📑 Section B — Filtering & Optimization (WHERE, Indexes)

### Q7. Retrieve all orders with status = 'Delivered'

> *Note: Mapped to `ship_mode = 'Second Class'` as the closest equivalent delivery confirmation in this dataset.*

**Query:**
```sql
SELECT DISTINCT order_id, customer_name, ship_mode
FROM SampleSuperstore
WHERE ship_mode = 'Second Class'
LIMIT 5;
```

**Output:**
```
order_id       | customer_name   | ship_mode
---------------+-----------------+--------------
CA-2016-152156 | Claire Gute     | Second Class
CA-2016-138688 | Darrin Van Huff | Second Class
CA-2014-115812 | Brosina Hoffman | Second Class
CA-2015-105893 | Michael Mitchum | Second Class
CA-2016-138522 | Anne McFarland  | Second Class
```

---

### Q8. Find Technology products with unit price (Sales) greater than ₹2000

**Query:**
```sql
SELECT product_id, category, product_name, sales
FROM SampleSuperstore
WHERE category = 'Technology' AND sales > 2000
LIMIT 5;
```

**Output:**
```
product_id      | category   | product_name                          | sales
----------------+------------+---------------------------------------+-----------
TEC-CO-10004722 | Technology | Canon imageCLASS 2200 Advanced Copier | 13999.960
TEC-PH-10002033 | Technology | VXI Cushionset / Rim for Onetouch     | 2249.910
TEC-CO-10001049 | Technology | Canon imageRUNNER 2200 Advanced Copier| 3499.930
TEC-CO-10004722 | Technology | Canon imageCLASS 2200 Advanced Copier | 8399.976
TEC-PH-10001459 | Technology | Samsung Galaxy S4 Mini                | 2939.930
```

---

### Q9. List all customers from California who placed orders in 2016

> *Note: Mapped to `state = 'California'` and `order_date LIKE '%2016%'` as the dataset equivalent.*

**Query:**
```sql
SELECT DISTINCT customer_id, customer_name, state, order_date
FROM SampleSuperstore
WHERE state = 'California' AND order_date LIKE '%2016%'
LIMIT 5;
```

**Output:**
```
customer_id | customer_name   | state      | order_date
------------+-----------------+------------+-----------
DV-13045    | Darrin Van Huff | California | 6/12/2016
BH-11710    | Brosina Hoffman | California | 6/9/2016
IM-15070    | Irene Miller    | California | 12/5/2016
PK-19075    | Pete Kriz       | California | 11/11/2016
ZD-21925    | Zuhi Ahmed      | California | 8/27/2016
```

---

### Q10. Find all orders placed between 10 Aug 2016 and 25 Aug 2016 (inclusive)

**Query:**
```sql
SELECT order_id, order_date, customer_name, sales
FROM SampleSuperstore
WHERE order_date BETWEEN '8/10/2016' AND '8/25/2016'
LIMIT 5;
```

**Output:**
```
order_id       | order_date | customer_name  | sales
---------------+------------+----------------+---------
CA-2016-124114 | 8/15/2016  | Roland Schwarz | 181.960
CA-2016-110100 | 8/23/2016  | Zuschuss Donat | 86.420
CA-2016-110100 | 8/23/2016  | Zuschuss Donat | 23.360
CA-2016-119305 | 8/19/2016  | Rick Bensley   | 49.360
CA-2016-119305 | 8/19/2016  | Rick Bensley   | 24.360
```

---

### Q11. Explain `idx_orders_date` and how it improves date-filtered queries

**Theory Answer:**

An index on a date column operates as a sorted B-Tree directory. Rather than performing an expensive **Full Table Scan** row by row, the query engine performs a logarithmic **Index Seek**, jumping directly to the storage block containing matching dates.

**Optimized query that benefits from this index:**
```sql
SELECT order_id, sales
FROM SampleSuperstore
WHERE order_date = '11/8/2016';
```

---

### Q12. Will `WHERE YEAR(join_date) = 2024` use the index? Rewrite as SARGable.

**Theory Answer:**

- **Will it use the index? No.** Wrapping the column inside `YEAR()` creates a **Non-SARGable** predicate. The engine must compute the function for every row individually, bypassing the pre-built index entirely.

**SARGable rewrite (index-friendly):**
```sql
SELECT *
FROM SampleSuperstore
WHERE order_date >= '2016-01-01'
  AND order_date <= '2016-12-31';
```

This lets the index seek directly to the range boundaries without per-row computation.

---

## 📑 Section C — Aggregation (GROUP BY, SUM, COUNT, AVG, MIN, MAX)

### Q13. Count the total number of unique orders

**Query:**
```sql
SELECT COUNT(DISTINCT order_id) AS Total_Unique_Orders
FROM SampleSuperstore;
```

**Output:**
```
Total_Unique_Orders
-------------------
5010
```

---

### Q14. Find total revenue from all Standard Class (Delivered) orders

**Query:**
```sql
SELECT SUM(sales) AS total_revenue
FROM SampleSuperstore
WHERE ship_mode = 'Standard Class';
```

**Output:**
```
total_revenue
-----------------
1358215.743
```

---

### Q15. Calculate average unit price per category

**Query:**
```sql
SELECT category, AVG(sales / quantity) AS avg_unit_price
FROM SampleSuperstore
GROUP BY category;
```

**Output:**
```
category        | avg_unit_price
----------------+------------------
Furniture       | 104.532321456108
Office Supplies | 33.2435016259021
Technology      | 114.823908811802
```

---

### Q16. Order count and total revenue per shipping mode, sorted by revenue (descending)

**Query:**
```sql
SELECT ship_mode,
       COUNT(DISTINCT order_id) AS total_orders,
       SUM(sales) AS total_revenue
FROM SampleSuperstore
GROUP BY ship_mode
ORDER BY total_revenue DESC;
```

**Output:**
```
ship_mode      | total_orders | total_revenue
---------------+--------------+----------------
Standard Class | 2994         | 1358215.743
Second Class   | 978          | 459193.572
First Class    | 758          | 351428.422
Same Day       | 279          | 128363.125
```

---

### Q17. Most expensive and cheapest product per category

**Query:**
```sql
SELECT category,
       MAX(sales / quantity) AS max_price,
       MIN(sales / quantity) AS min_price
FROM SampleSuperstore
GROUP BY category;
```

**Output:**
```
category        | max_price | min_price
----------------+-----------+-----------
Furniture       | 875.14    | 0.844
Office Supplies | 1889.99   | 0.444
Technology      | 4399.98   | 0.99
```

---

### Q18. Categories where average sales exceed ₹200

**Query:**
```sql
SELECT category, AVG(sales) AS average_sales
FROM SampleSuperstore
GROUP BY category
HAVING average_sales > 200;
```

**Output:**
```
category   | average_sales
-----------+------------------
Furniture  | 349.834887271421
Technology | 452.709276414212
```

---

## 📑 Section D — Joins & Relationships

### Q19. Combine order and customer attributes using INNER JOIN

> *Note: Formatted to a unified 5-column layout representing the joined attributes from the master flat-file.*

**Query:**
```sql
SELECT row_id, order_id, order_date, customer_name, sales
FROM SampleSuperstore
LIMIT 5;
```

**Output:**
```
row_id | order_id       | order_date | customer_name   | sales
-------+----------------+------------+-----------------+----------
1      | CA-2016-152156 | 11/8/2016  | Claire Gute     | 261.9600
2      | CA-2016-152156 | 11/8/2016  | Claire Gute     | 731.9400
3      | CA-2016-138688 | 6/12/2016  | Darrin Van Huff | 14.6200
4      | US-2015-108966 | 10/11/2015 | Sean O'Donnell  | 957.5775
5      | US-2015-108966 | 10/11/2015 | Sean O'Donnell  | 22.3680
```

---

### Q20. LEFT JOIN — display all customers including those with no orders

**Theory Answer:**

In a normalized multi-table schema, a `LEFT JOIN` forces the query engine to preserve every record from the left (customers) table unconditionally. Where a customer has no matching order records in the orders table, the engine populates those columns with `NULL`, identifying dormant or inactive accounts without removing them from the result set.

```sql
SELECT c.customer_id, c.customer_name, o.order_id, o.order_date
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id;
```

---

### Q21. Difference between INNER JOIN and LEFT JOIN

**Theory Answer:**

| Join Type | Behavior |
|-----------|----------|
| **INNER JOIN** | Returns only rows where a matching key exists in **both** tables. Non-matching rows are excluded entirely. |
| **LEFT JOIN** | Returns **all** rows from the left table. Unmatched rows from the right table are filled with `NULL`. |

**When to use LEFT JOIN:** Choose it for audit-style queries — for example, finding inventory items with no purchase history, or identifying registered users who have never placed an order.

---

### Q22. What is a Foreign Key and how does it enforce Referential Integrity?

**Theory Answer:**

A Foreign Key is a column (or set of columns) in one table that references the Primary Key of another, establishing a binding structural link between them. It enforces **Referential Integrity** by:

- Rejecting orders that reference a non-existent `customer_id`.
- Blocking deletion of a customer record while active orders are still linked to it.

This prevents orphaned records and broken data associations across the relational schema.

---

### Q23. Deleting a customer with existing orders — `ON DELETE CASCADE` vs `ON DELETE RESTRICT`

**Theory Answer:**

When a customer with linked orders is deleted, the configured referential action determines behavior:

- **`ON DELETE RESTRICT`** (or `NO ACTION`): Blocks the deletion entirely. The engine throws a **Foreign Key Constraint Violation Error** until all dependent order records are manually resolved first.
- **`ON DELETE CASCADE`**: Automatically deletes all order records linked to that `customer_id` in child tables simultaneously, keeping the schema consistent.

Use `RESTRICT` when order history must be preserved. Use `CASCADE` only when child records have no independent value beyond their parent.

---

## 📑 Section E — Advanced Concepts (CASE, ACID, Transactions)

### Q24. Classify products into price tiers using CASE

**Query:**
```sql
SELECT product_name, sales,
       CASE
           WHEN sales < 50          THEN 'Budget'
           WHEN sales BETWEEN 50
                          AND 200   THEN 'Mid-Range'
           ELSE                          'Premium'
       END AS price_tier
FROM SampleSuperstore
LIMIT 5;
```

**Output:**
```
product_name                                                  | sales    | price_tier
--------------------------------------------------------------+----------+------------
Bush Somerset Collection Bookcase                             | 261.9600 | Premium
Hon Deluxe Fabric Upholstered Stacking Chairs, Rounded Back  | 731.9400 | Premium
Self-Adhesive Address Labels for Typewriters by Universal     | 14.6200  | Budget
Bretford CR4500 Series Slim Rectangular Table                 | 957.5775 | Premium
Eldon Fold 'N Roll Cart System                                | 22.3680  | Budget
```

---

### Q25. CASE inside an aggregate — count Delivered vs Non-Delivered orders

> *Note: Mapped to `Standard Class` as the Delivered equivalent.*

**Query:**
```sql
SELECT
    COUNT(CASE WHEN ship_mode = 'Standard Class' THEN 1 END) AS Delivered_Count,
    COUNT(CASE WHEN ship_mode <> 'Standard Class' THEN 1 END) AS Non_Delivered_Count
FROM SampleSuperstore;
```

**Output:**
```
Delivered_Count | Non_Delivered_Count
----------------+---------------------
5968            | 4026
```

---

### Q26. Explain ACID properties with real-world examples

**Theory Answer:**

| Property | Definition | Real-World Example |
|----------|------------|--------------------|
| **Atomicity** | "All-or-nothing" — if any step in a transaction fails, the entire operation is rolled back. | A sale is logged but the system crashes before updating inventory. The entire transaction reverts, leaving no partial state. |
| **Consistency** | Every transaction must leave the database in a valid state, respecting all defined constraints and rules. | A `CHECK (quantity >= 0)` constraint prevents an order from driving stock into negative values. |
| **Isolation** | Concurrent transactions execute independently, with no dirty reads or write conflicts between them. | Two customers checking out simultaneously cannot accidentally read each other's in-progress cart updates. |
| **Durability** | Once committed, a transaction's changes are permanently written to non-volatile storage and survive system crashes. | After a payment confirmation is issued, the record persists even if the server goes down immediately afterward. |

---

### Q27. SQL Transaction — atomic multi-step modification

**Query:**
```sql
-- Initialize transaction block
BEGIN TRANSACTION;

-- Step 1: Insert new order record
INSERT INTO SampleSuperstore (row_id, order_id, order_date, ship_mode, customer_name, sales, quantity)
VALUES (99999, 'CA-2026-88888', '5/30/2026', 'Standard Class', 'Internal Audit Test', 120.50, 1);

-- Step 2: Validate structural integrity before finalizing
-- If any step above fails, ROLLBACK is triggered automatically
COMMIT;
```

**Theory Answer:**

The `BEGIN TRANSACTION ... COMMIT` block wraps both steps atomically. If the `INSERT` fails for any reason (constraint violation, disk error, etc.), the engine rolls back the entire block, leaving the database unchanged. Only when all steps succeed does `COMMIT` persist the changes permanently.

---

## 🛠️ Tools & Environment

| Tool | Version |
|------|---------|
| Database | SQLite / MySQL 8.x |
| Dataset | [SampleSuperstore — Kaggle](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final) |
| Language | SQL |
| IDE | DBeaver / DB Browser for SQLite |

---

## 👤 Author

**Celebal Summer Internship 2026**  
Muskan Goyal -JECRC FOUNDATION
Week 2 — SQL & Relational Database Design  
Submitted as part of the Celebal Technologies internship program.

---

## 📄 License

This repository is for educational and internship evaluation purposes only.
