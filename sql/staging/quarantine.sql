 -- silver.quarantine
-- GRAIN: one row per (dataset, record_key, rule, column_name), i.e. one row per
-- REASON a record was rejected. A record with two problems appears twice.
--
-- This is the ONE place that decides what is kept out of silver. The stg_*.sql
-- files just anti-join against it. Reasons come from three places:
--   1. contract_violations: temp table written by transform.py from validate.py
--      (row rules + the set checks in sql/checks/). The contract is the judge.
--   2. parent_quarantined: a transaction whose customer was rejected. Silver
--      must be referentially intact, or gold joins silently drop rows.
--   3. residency_blocked: processed in a region the policy neither allows nor
--      flags. classify_transfer() is govern.py, registered as a SQL function.
--
-- No raw payload is copied in: bronze already holds every original row, and
-- copying it here would spread unmasked PII into a second table. record_key +
-- source_table is the pointer back to the evidence.
CREATE OR REPLACE TABLE silver.quarantine AS
WITH rejected_customers AS (
    SELECT DISTINCT record_key AS customer_id
    FROM contract_violations
    WHERE dataset = 'customers'
),

parent_quarantined AS (
    SELECT DISTINCT
        'transactions'          AS dataset,
        t.transaction_id        AS record_key,
        'customer_id'           AS column_name,
        'parent_quarantined'    AS rule,
        'customer ' || t.customer_id || ' is quarantined' AS reason
    FROM bronze.transactions t
    JOIN rejected_customers r USING (customer_id)
),

residency_blocked AS (
    SELECT DISTINCT
        'transactions'          AS dataset,
        t.transaction_id        AS record_key,
        'processing_region'     AS column_name,
        'residency_blocked'     AS rule,
        'processing_region ' || t.processing_region || ' -> '
            || classify_transfer(c.home_region, t.processing_region) AS reason
    FROM bronze.transactions t
    JOIN bronze.customers c USING (customer_id)
    -- Fail closed: anything the policy doesn't explicitly allow or flag is out.
    WHERE classify_transfer(c.home_region, t.processing_region)
          NOT IN ('domestic', 'cross_border_flagged')
),

all_reasons AS (
    SELECT dataset, record_key, column_name, rule, reason FROM contract_violations
    UNION
    SELECT * FROM parent_quarantined
    UNION
    SELECT * FROM residency_blocked
)

SELECT
    dataset,
    record_key,
    column_name,
    rule,
    reason,
    'bronze.' || dataset AS source_table
FROM all_reasons
ORDER BY dataset, record_key, rule, column_name;
