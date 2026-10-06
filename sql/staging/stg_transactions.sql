-- silver.transactions
-- GRAIN: one row per transaction_id. Cleaned, typed, deduped, valid only, and
-- tagged with its residency verdict (the passport stamp).
-- Build silver.customers FIRST: home_region comes from there.
CREATE OR REPLACE TABLE silver.transactions AS
WITH deduped AS (
    SELECT DISTINCT * FROM bronze.transactions
)
SELECT
    TRIM(t.transaction_id)                                  AS transaction_id,
    TRIM(t.customer_id)                                     AS customer_id,
    CAST(TRIM(t.amount_zar) AS DECIMAL(12, 2))              AS amount_zar,
    TRIM(t.currency)                                        AS currency,
    TRIM(t.merchant)                                        AS merchant,
    CAST(TRIM(t.txn_timestamp) AS TIMESTAMP)                AS txn_timestamp,
    c.home_region,
    TRIM(t.processing_region)                               AS processing_region,
    classify_transfer(c.home_region, TRIM(t.processing_region)) AS residency_status,
    t._source_file,
    t._ingested_at
FROM deduped t
-- Inner join is safe: every surviving transaction has a surviving customer,
-- because orphans and children of rejected customers are quarantined.
JOIN silver.customers c ON c.customer_id = t.customer_id
WHERE NOT EXISTS (
    SELECT 1 FROM silver.quarantine q
    WHERE q.dataset = 'transactions' AND q.record_key = t.transaction_id
)
ORDER BY transaction_id;
