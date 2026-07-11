-- window_functions.sql
-- Step 5: Window Functions & CTEs

-- ---------------------------------------------------------------------
-- 1. Rank customers by lifetime value (RANK / DENSE_RANK)
-- ---------------------------------------------------------------------
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
    customer_id,
    name,
    segment,
    lifetime_value,
    RANK()       OVER (ORDER BY lifetime_value DESC) AS ltv_rank,
    DENSE_RANK() OVER (ORDER BY lifetime_value DESC) AS ltv_dense_rank
FROM customer_ltv
ORDER BY lifetime_value DESC
LIMIT 20;


-- ---------------------------------------------------------------------
-- 2. Running total & moving average of monthly revenue
-- ---------------------------------------------------------------------
WITH monthly_revenue AS (
    SELECT
        strftime('%Y-%m', o.order_date)            AS month,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status IN ('completed', 'shipped')
    GROUP BY month
)
SELECT
    month,
    revenue,
    ROUND(SUM(revenue) OVER (ORDER BY month), 2)                                   AS running_total,
    ROUND(AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3mo
FROM monthly_revenue
ORDER BY month;


-- ---------------------------------------------------------------------
-- 3. Monthly revenue growth rate (CTE chaining)
-- ---------------------------------------------------------------------
WITH monthly_revenue AS (
    SELECT
        strftime('%Y-%m', o.order_date)            AS month,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status IN ('completed', 'shipped')
    GROUP BY month
),
revenue_with_prev AS (
    SELECT
        month,
        revenue,
        LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue
    FROM monthly_revenue
)
SELECT
    month,
    revenue,
    prev_month_revenue,
    CASE
        WHEN prev_month_revenue IS NULL OR prev_month_revenue = 0 THEN NULL
        ELSE ROUND(100.0 * (revenue - prev_month_revenue) / prev_month_revenue, 2)
    END AS mom_growth_pct
FROM revenue_with_prev
ORDER BY month;


-- ---------------------------------------------------------------------
-- 4. Each customer's orders with a running spend total (per customer)
-- ---------------------------------------------------------------------
WITH order_totals AS (
    SELECT
        o.order_id,
        o.customer_id,
        o.order_date,
        SUM(oi.quantity * oi.unit_price) AS order_value
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status IN ('completed', 'shipped')
    GROUP BY o.order_id, o.customer_id, o.order_date
)
SELECT
    customer_id,
    order_id,
    order_date,
    order_value,
    ROUND(SUM(order_value) OVER (
        PARTITION BY customer_id ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS running_customer_spend
FROM order_totals
ORDER BY customer_id, order_date;
