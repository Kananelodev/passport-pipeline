-- gold.customer_transaction_summary
-- GRAIN: one row per customer_id in silver.customers, INCLUDING customers with
-- no transactions (LEFT JOIN + COALESCE), so "inactive" is visible, not missing.
-- Keyed on customer_id; no direct identifiers (names, ID, email) reach gold.
CREATE OR REPLACE TABLE gold.customer_transaction_summary AS
WITH merchant_rank AS (
    -- Favourite merchant = most transactions. Ties broken alphabetically so the
    -- answer is deterministic. mode() would pick arbitrarily, and a mart that
    -- changes between identical runs breaks idempotency.
    SELECT
        customer_id,
        merchant,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY COUNT(*) DESC, merchant
        ) AS rn
    FROM silver.transactions
    GROUP BY customer_id, merchant
),

totals AS (
    SELECT
        customer_id,
        COUNT(*)                                            AS transaction_count,
        SUM(amount_zar)                                     AS total_spend_zar,
        ROUND(AVG(amount_zar), 2)                           AS avg_transaction_zar,
        MIN(txn_timestamp)                                  AS first_txn_at,
        MAX(txn_timestamp)                                  AS last_txn_at,
        -- Same definition as the cross-border report: data physically left home.
        COUNT(*) FILTER (WHERE processing_region <> home_region) AS cross_border_txn_count
    FROM silver.transactions
    GROUP BY customer_id
)

SELECT
    c.customer_id,
    c.province,
    c.signup_date,
    COALESCE(t.transaction_count, 0)        AS transaction_count,
    COALESCE(t.total_spend_zar, 0)          AS total_spend_zar,
    t.avg_transaction_zar,
    t.first_txn_at,
    t.last_txn_at,
    m.merchant                              AS favourite_merchant,
    COALESCE(t.cross_border_txn_count, 0)   AS cross_border_txn_count
FROM silver.customers c
LEFT JOIN totals t        ON t.customer_id = c.customer_id
LEFT JOIN merchant_rank m ON m.customer_id = c.customer_id AND m.rn = 1
ORDER BY c.customer_id;
