-- sql/checks/orphan_transactions.sql
SELECT t.transaction_id, t.customer_id
FROM bronze.transactions t
LEFT JOIN bronze.customers c ON t.customer_id = c.customer_id
WHERE c.customer_id IS NULL;