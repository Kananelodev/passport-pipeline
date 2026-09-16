# Marts (gold) SQL models

One file per mart:
- `daily_revenue_by_province.sql`
- `customer_transaction_summary.sql`
- `cross_border_transfer_report.sql`  ← the showpiece

Each reads from `silver.*` and writes a `gold.*` table. Called from
`transform.build_gold()`.
