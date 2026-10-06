-- silver.customers
-- GRAIN: one row per customer_id. Cleaned, typed, deduped, PII-masked, valid only.
--
-- PII handling follows governance/data_contracts/customers.yml:
--   first_name, last_name -> mask: drop      (not selected at all: minimisation)
--   sa_id_number          -> mask: tokenise  (HMAC token, still joinable)
--   email                 -> mask: hash      (sha256, still joinable)
--   phone                 -> mask: partial   (last 3 digits)
-- tests/test_transform.py checks this file agrees with the contract.
CREATE OR REPLACE TABLE silver.customers AS
WITH deduped AS (
    -- Exact re-delivered copies collapse here. Conflicting copies (same id,
    -- different values) were already quarantined by the duplicate check.
    SELECT DISTINCT * FROM bronze.customers
)
SELECT
    TRIM(customer_id)                                       AS customer_id,
    mask_pii(TRIM(sa_id_number), 'tokenise')                AS sa_id_number,
    mask_pii(LOWER(TRIM(email)), 'hash')                    AS email,
    mask_pii(NULLIF(TRIM(phone), ''), 'partial')            AS phone,
    TRIM(province)                                          AS province,
    CAST(TRIM(signup_date) AS DATE)                         AS signup_date,
    TRIM(home_region)                                       AS home_region,
    _source_file,
    _ingested_at
FROM deduped d
-- NOT EXISTS, not NOT IN: if the subquery ever held a NULL, NOT IN would
-- evaluate to NULL for every row and silver would silently come out empty.
WHERE NOT EXISTS (
    SELECT 1 FROM silver.quarantine q
    WHERE q.dataset = 'customers' AND q.record_key = d.customer_id
)
ORDER BY customer_id;
