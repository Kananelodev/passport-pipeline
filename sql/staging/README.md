# Staging (silver) SQL models

Write one file per silver table, e.g. `stg_customers.sql`, `stg_transactions.sql`.
Each should read from the matching `bronze.*` table and produce a clean, typed,
deduplicated, PII-masked `silver.*` table (valid rows only; route bad rows to
`silver.quarantine`). Called from `transform.build_silver()`.
