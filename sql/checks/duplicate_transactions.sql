-- sql/checks/duplicate_transactions.sql
-- A transaction_id carried by more than one DIFFERENT row (see the customers
-- check for why exact copies don't count).
SELECT transaction_id, COUNT(*) AS n
FROM (SELECT DISTINCT * EXCLUDE (_ingested_at, _source_file) FROM bronze.transactions)
GROUP BY transaction_id
HAVING COUNT(*) > 1;
