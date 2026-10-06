-- sql/checks/duplicate_customer_ids.sql
-- A customer_id carried by more than one DIFFERENT row. Exact copies (same
-- values, re-delivered) are not conflicts: silver collapses them with DISTINCT.
SELECT customer_id, COUNT(*) AS n
FROM (SELECT DISTINCT * EXCLUDE (_ingested_at, _source_file) FROM bronze.customers)
GROUP BY customer_id
HAVING COUNT(*) > 1;
