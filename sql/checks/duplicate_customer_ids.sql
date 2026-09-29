-- sql/checks/duplicate_customer_ids.sql
SELECT customer_id, COUNT(*) AS n
FROM bronze.customers
GROUP BY customer_id
HAVING COUNT(*) > 1;