# Week 2 Task 2 - E-Commerce Sales Database

## Section A — SQL Basics

### Q1. Write a query to display all columns and rows from the customer's table.

```sql
SELECT *
FROM customers;
```

### Q2. Retrieve only the first_name, last_name, and city of all customers.

```sql
SELECT first_name, last_name, city
FROM customers;
```

### Q3. List all unique categories available in the products table.

```sql
SELECT DISTINCT category
FROM products;
```

### Q4. Identify the Primary Key of each table in the schema. Explain why a Primary Key must be unique and NOT NULL.

| Table       | Primary Key |
| ----------- | ----------- |
| customers   | customer_id |
| products    | product_id  |
| orders      | order_id    |
| order_items | item_id     |

**Explanation:**
A Primary Key uniquely identifies each row in a table. It cannot contain NULL values and prevents duplicate records.

### Q5. What constraints are applied to the email column in the customers table? What would happen if you tried to insert a duplicate email?

```sql
email VARCHAR(100) UNIQUE NOT NULL
```

Attempting to insert a duplicate email will result in a UNIQUE constraint violation error.

### Q6. Try inserting a product with unit_price = -50. What happens and which constraint prevents it? Write both the INSERT statement and explain the error.

```sql
INSERT INTO products
VALUES (209, 'Test Product', 'Electronics', 'TestBrand', -50, 100);
```

**Result:**
The insertion fails because of "CHECK (unit_price > 0)" which prevents negative prices.

---

## Section B — Filtering & Optimization

### Q7. Retrieve all orders with status = 'Delivered'.

```sql
SELECT *
FROM orders
WHERE status = 'Delivered';
```

### Q8. Find all products in the 'Electronics' category with a unit_price greater than ₹2000. 

```sql
SELECT *
FROM products
WHERE category = 'Electronics' AND unit_price > 2000;
```

### Q9. List all customers who joined in the year 2024 and belong to the state 'Maharashtra'.

```sql
SELECT *
FROM customers
WHERE state = 'Maharashtra'
AND join_date BETWEEN '2024-01-01' AND '2024-12-31';
```

### Q10. Find all orders placed between '2024-08-10' and '2024-08-25' (inclusive) that are NOT cancelled.

```sql
SELECT *
FROM orders
WHERE order_date BETWEEN '2024-08-10' AND '2024-08-25' AND status <> 'Cancelled';
```

### Q11. Explain what the index idx_orders_date does. How would it improve the performance of a query that filters orders by order_date? Write a sample query that would benefit from this index.

```sql
CREATE INDEX idx_orders_date
ON orders(order_date);
```

This index improves query performance by reducing the number of rows scanned during date-based filtering.

Example:

```sql
SELECT *
FROM orders
WHERE order_date BETWEEN '2024-08-01' AND '2024-08-31';
```

### Q12. If you run: SELECT * FROM customers WHERE YEAR(join_date) = 2024; — would the index on join_date be used? Explain why or why not, and rewrite the query to be index-friendly (SARGable).

Not index-friendly:

```sql
SELECT *
FROM customers
WHERE YEAR(join_date) = 2024;
```

SARGable version:

```sql
SELECT *
FROM customers
WHERE join_date BETWEEN '2024-01-01' AND '2024-12-31';
```

---

## Section C — Aggregation

### Q13. Count the total number of orders in the orders table.

```sql
SELECT COUNT(*) AS total_orders
FROM orders;
```

### Q14. Find the total revenue (SUM of total_amount) from all 'Delivered' orders.

```sql
SELECT SUM(total_amount) AS total_revenue
FROM orders
WHERE status = 'Delivered';
```

### Q15. Calculate the average unit_price of products in each category.

```sql
SELECT category, AVG(unit_price) AS avg_price
FROM products
GROUP BY category;
```

### Q16. For each order status, find the count of orders and the total revenue. Sort the result by total revenue in descending order.

```sql
SELECT status, COUNT(*) AS order_count, SUM(total_amount) AS revenue
FROM orders
GROUP BY status
ORDER BY revenue DESC;
```

### Q17. Find the most expensive (MAX) and cheapest (MIN) product in each category.

```sql
SELECT category, MAX(unit_price) AS max_price, MIN(unit_price) AS min_price
FROM products
GROUP BY category;
```

### Q18. List all product categories where the average unit_price is greater than ₹2000. (Hint: Use HAVING clause) 

```sql
SELECT category, AVG(unit_price) AS avg_price
FROM products
GROUP BY category
HAVING AVG(unit_price) > 2000;
```

---

## Section D — Joins & Relationships

### Q19. Write an INNER JOIN query to display each order along with the customer's first_name and last_name. Show: order_id, order_date, first_name, last_name, total_amount.

```sql
SELECT o.order_id, o.order_date, c.first_name, c.last_name, o.total_amount
FROM orders o
INNER JOIN customers c
ON o.customer_id = c.customer_id;
```

### Q20. Using a LEFT JOIN, list ALL customers and their orders (if any). Customers with no orders should still appear with NULL values for order columns.

```sql
SELECT c.customer_id, c.first_name, c.last_name, o.order_id, o.order_date
FROM customers c
LEFT JOIN orders o
ON c.customer_id = o.customer_id;
```

### Q21. Write a query using JOINs across three tables (orders → order_items → products) to show: order_id, product_name, quantity, unit_price, and discount_pct for each order item. 

```sql
SELECT o.order_id, p.product_name, oi.quantity, oi.unit_price, oi.discount_pct
FROM orders o
JOIN order_items oi
ON o.order_id = oi.order_id
JOIN products p
ON oi.product_id = p.product_id;
```

### Q22. Explain the difference between LEFT JOIN and RIGHT JOIN with an example from this schema. When would you use a FULL OUTER JOIN?

**LEFT JOIN:** Returns all rows from the left table and matching rows from the right table.

**RIGHT JOIN:** Returns all rows from the right table and matching rows from the left table.

**FULL OUTER JOIN:** Returns all rows from both tables, including unmatched records.

### Q23. Identify all Foreign Key relationships in the schema. Explain what would happen if you tried to insert an order with customer_id = 999 (which doesn't exist in customers)

```text
orders.customer_id → customers.customer_id

order_items.order_id → orders.order_id

order_items.product_id → products.product_id
```

```sql
INSERT INTO orders
VALUES (2000, 999, '2024-09-01', 'Pending', 1000);
```

Attempting to insert the above will fail because customer_id 999 does not exist in the customers table.

---

## Section E — Advanced Concepts

### Q24. Write a query using CASE to classify products into price tiers: 
###  • 'Budget'    → unit_price < 1000 
###  • 'Mid-Range' → unit_price BETWEEN 1000 AND 3000 
###  • 'Premium'   → unit_price > 3000 
### Display: product_name, unit_price, price_tier. 

```sql
SELECT product_name, unit_price,
CASE
    WHEN unit_price < 1000 THEN 'Budget'
    WHEN unit_price BETWEEN 1000 AND 3000 THEN 'Mid-Range'
    ELSE 'Premium'
END AS price_tier
FROM products;
```

### Q25. Using a CASE statement inside an aggregate function, count how many orders are 'Delivered' vs 'Not Delivered' (all other statuses). Display the result in a single row.

```sql
SELECT SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) AS Delivered, SUM(CASE WHEN status <> 'Delivered' THEN 1 ELSE 0 END) AS Not_Delivered
FROM orders;
```

### Q26. Explain each letter of ACID. Give a real-world example (e.g., bank transfer) showing why each property is important. 

#### Atomicity

Ensures that all operations in a transaction succeed or none are applied.

#### Consistency

Ensures the database remains valid before and after a transaction.

#### Isolation

Ensures concurrent transactions do not interfere with each other.

#### Durability

Ensures committed transactions are permanently stored.

**Example:**
In a bank transfer, money must be deducted from one account and added to another. If any step fails, the entire transaction is rolled back to maintain consistency.

### Q27. Write a SQL transaction that does the following atomically: 
###  1. Insert a new order (order_id=1011, customer_id=102, today's date, 'Pending', 1598.00) 
###  2. Insert two order items for that order 
###  3. Update the stock_qty of the purchased products 
###  4. If any step fails, ROLLBACK the entire transaction. Otherwise, COMMIT. 
### Write the complete BEGIN...COMMIT/ROLLBACK block.

```sql
START TRANSACTION;

INSERT INTO orders
VALUES (1011, 102, CURDATE(), 'Pending', 1598.00);

INSERT INTO order_items
VALUES (5016, 1011, 206, 1, 1299.00, 0);

INSERT INTO order_items
VALUES (5017, 1011, 208, 1, 599.00, 0);

UPDATE products
SET stock_qty = stock_qty - 1
WHERE product_id = 206;

UPDATE products
SET stock_qty = stock_qty - 1
WHERE product_id = 208;

COMMIT;
```

If any statement fails "ROLLBACK;" is used to undo all changes and maintain data integrity.
