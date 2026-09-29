-- sql/checks/duplicate_transaction_ids.sql
SELECT transaction_id, COUNT(*) AS n
FROM bronze.transactions
GROUP BY transaction_id
HAVING COUNT(*) > 1;