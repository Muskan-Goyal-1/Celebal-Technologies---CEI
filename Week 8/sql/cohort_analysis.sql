-- cohort_analysis.sql
-- Step 6: Cohort & Retention Analysis
-- Step 7: Customer Segmentation (frequency tier, spend tier, RFM)

-- ---------------------------------------------------------------------
-- 1. Assign each customer to a cohort = month of their first order
-- ---------------------------------------------------------------------
WITH first_purchase AS (
    SELECT
        customer_id,
        MIN(strftime('%Y-%m', order_date)) AS cohort_month
    FROM orders
    WHERE status IN ('completed', 'shipped')
    GROUP BY customer_id
)
SELECT cohort_month, COUNT(*) AS customers_in_cohort
FROM first_purchase
GROUP BY cohort_month
ORDER BY cohort_month;


-- ---------------------------------------------------------------------
-- 2. Monthly retention rate per cohort
--    For each cohort, what % of the original cohort placed an order
--    in each subsequent "months since first purchase" bucket.
-- ---------------------------------------------------------------------
WITH first_purchase AS (
    SELECT
        customer_id,
        MIN(strftime('%Y-%m', order_date)) AS cohort_month
    FROM orders
    WHERE status IN ('completed', 'shipped')
    GROUP BY customer_id
),
activity AS (
    SELECT DISTINCT
        o.customer_id,
        strftime('%Y-%m', o.order_date) AS active_month
    FROM orders o
    WHERE o.status IN ('completed', 'shipped')
),
cohort_activity AS (
    SELECT
        fp.cohort_month,
        fp.customer_id,
        a.active_month,
        -- months elapsed since the customer's first purchase
        (CAST(strftime('%Y', a.active_month || '-01') AS INTEGER) - CAST(strftime('%Y', fp.cohort_month || '-01') AS INTEGER)) * 12
        + (CAST(strftime('%m', a.active_month || '-01') AS INTEGER) - CAST(strftime('%m', fp.cohort_month || '-01') AS INTEGER)) AS month_number
    FROM first_purchase fp
    JOIN activity a ON a.customer_id = fp.customer_id
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
    FROM first_purchase
    GROUP BY cohort_month
)
SELECT
    ca.cohort_month,
    ca.month_number,
    COUNT(DISTINCT ca.customer_id)                              AS active_customers,
    cs.cohort_size,
    ROUND(100.0 * COUNT(DISTINCT ca.customer_id) / cs.cohort_size, 1) AS retention_pct
FROM cohort_activity ca
JOIN cohort_sizes cs ON cs.cohort_month = ca.cohort_month
GROUP BY ca.cohort_month, ca.month_number
ORDER BY ca.cohort_month, ca.month_number;


-- ---------------------------------------------------------------------
-- 3. Churned vs repeat customers
--    "repeat"  = placed more than one order
--    "churned" = single order more than 90 days before the most recent
--                order date in the whole dataset (i.e. inactive since)
-- ---------------------------------------------------------------------
WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(*)        AS order_count,
        MAX(order_date) AS last_order_date
    FROM orders
    WHERE status IN ('completed', 'shipped')
    GROUP BY customer_id
),
dataset_max_date AS (
    SELECT MAX(order_date) AS max_date FROM orders
)
SELECT
    co.customer_id,
    co.order_count,
    co.last_order_date,
    CASE
        WHEN co.order_count > 1 THEN 'repeat'
        WHEN julianday((SELECT max_date FROM dataset_max_date)) - julianday(co.last_order_date) > 90 THEN 'churned'
        ELSE 'one_time_recent'
    END AS customer_status
FROM customer_orders co
ORDER BY co.order_count DESC;


-- ---------------------------------------------------------------------
-- 4. Segmentation: purchase-frequency tier + spend tier + RFM
-- ---------------------------------------------------------------------
WITH customer_orders AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT o.order_id)                       AS frequency,
        SUM(oi.quantity * oi.unit_price)                 AS monetary,
        MAX(o.order_date)                                AS last_order_date
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status IN ('completed', 'shipped')
    GROUP BY o.customer_id
),
dataset_max_date AS (
    SELECT MAX(order_date) AS max_date FROM orders
),
rfm_base AS (
    SELECT
        co.customer_id,
        CAST(julianday((SELECT max_date FROM dataset_max_date)) - julianday(co.last_order_date) AS INTEGER) AS recency_days,
        co.frequency,
        ROUND(co.monetary, 2) AS monetary
    FROM customer_orders co
),
rfm_scored AS (
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,   -- 4 = most recent (smallest recency_days)
        NTILE(4) OVER (ORDER BY frequency DESC)    AS f_score,   -- 4 = most frequent
        NTILE(4) OVER (ORDER BY monetary DESC)     AS m_score    -- 4 = highest spend
    FROM rfm_base
)
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    CASE
        WHEN frequency = 1 THEN 'one-time'
        WHEN frequency BETWEEN 2 AND 4 THEN 'occasional'
        ELSE 'loyal'
    END AS frequency_tier,
    CASE
        WHEN monetary < 100 THEN 'low'
        WHEN monetary < 500 THEN 'medium'
        ELSE 'high'
    END AS spend_tier,
    r_score, f_score, m_score,
    (r_score + f_score + m_score) AS rfm_total_score
FROM rfm_scored
ORDER BY rfm_total_score DESC;
