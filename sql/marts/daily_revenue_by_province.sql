-- gold.daily_revenue_by_province
-- GRAIN: one row per (txn_date, province).
-- Province is a customer attribute, so this is a fact (transactions) joined to a
-- dimension (customers) and rolled up. Cross-border transactions count too:
-- revenue is revenue wherever it was processed.
CREATE OR REPLACE TABLE gold.daily_revenue_by_province AS
SELECT
    CAST(t.txn_timestamp AS DATE)           AS txn_date,
    c.province,
    COUNT(*)                                AS transaction_count,
    COUNT(DISTINCT t.customer_id)           AS unique_customers,
    SUM(t.amount_zar)                       AS revenue_zar,
    ROUND(AVG(t.amount_zar), 2)             AS avg_transaction_zar
FROM silver.transactions t
JOIN silver.customers c USING (customer_id)
GROUP BY ALL
ORDER BY txn_date, province;
