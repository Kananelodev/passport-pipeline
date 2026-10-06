-- gold.cross_border_transfer_report  (the showpiece)
-- GRAIN: one row per (transfer_month, home_region, processing_region).
--
-- Answers the POPIA question "whose personal information was processed outside
-- its home region, where, and how much?" as a query rather than a PDF.
--   - which PII:  the personal-information categories linked to the transferred
--                 records, read from silver.pii_inventory (built from the contract)
--   - how much:   transfers, distinct data subjects, rand value, and the share of
--                 that month's processing that left the home region
-- Blocked regions never get here (they're in silver.quarantine), so every row
-- is a PERMITTED transfer that must be recorded.
CREATE OR REPLACE TABLE gold.cross_border_transfer_report AS
WITH monthly_volume AS (
    SELECT DATE_TRUNC('month', txn_timestamp) AS transfer_month, COUNT(*) AS all_txns
    FROM silver.transactions
    GROUP BY 1
),

pii_linked AS (
    SELECT STRING_AGG(column_name, ', ' ORDER BY column_name) AS pii_categories
    FROM silver.pii_inventory
    WHERE dataset = 'customers'
)

SELECT
    CAST(DATE_TRUNC('month', t.txn_timestamp) AS DATE)       AS transfer_month,
    t.home_region,
    t.processing_region,
    t.residency_status,
    COUNT(*)                                                 AS transfer_count,
    COUNT(DISTINCT t.customer_id)                            AS data_subjects_affected,
    SUM(t.amount_zar)                                        AS amount_zar,
    ROUND(100.0 * COUNT(*) / ANY_VALUE(v.all_txns), 2)       AS pct_of_month_txns,
    MIN(t.txn_timestamp)                                     AS first_transfer_at,
    MAX(t.txn_timestamp)                                     AS last_transfer_at,
    ANY_VALUE(p.pii_categories)                              AS pii_categories
FROM silver.transactions t
JOIN monthly_volume v ON v.transfer_month = DATE_TRUNC('month', t.txn_timestamp)
CROSS JOIN pii_linked p
WHERE t.processing_region <> t.home_region
GROUP BY 1, 2, 3, 4
ORDER BY transfer_month, processing_region;
