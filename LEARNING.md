# What to learn, per stage

You don't need to know all of this up front. Learn each concept *right before* the
milestone that uses it — that's when it sticks. Search terms are given instead of
links so you find current sources yourself (and because links rot).

## Iteration 0 — sample data
- Python `csv` / `faker` library basics.
- The structure of a **South African ID number** (13 digits: YYMMDD + sequence +
  citizenship + checksum) and the **Luhn checksum** algorithm — you'll validate
  these later, so generate both valid and invalid ones nowg

## Iteration 1 — warehouse
- What an **OLAP** columnar warehouse is and why it differs from a transactional DB.
- DuckDB basics: `duckdb.connect`, running SQL, schemas.
- Search: "duckdb python tutorial", "OLAP vs OLTP".

## Iteration 2 — ingest / bronze
- The **medallion architecture** (bronze/silver/gold) and *why raw is immutable*.
- **Data lineage** — why `_ingested_at` and `_source_file` matter.
- Search: "medallion architecture", "raw layer immutability data lake".

## Iteration 3 — validation
- **Data contracts** and schema-on-read vs schema-on-write.
- Common data-quality dimensions: completeness, validity, uniqueness, consistency,
  referential integrity.
- Search: "data quality dimensions", "data contract yaml", "referential integrity".

## Iteration 4 — governance
- **POPIA** basics: what counts as personal information, cross-border transfer rules.
- **PII masking vs tokenisation vs hashing** — when to use which.
- **Audit logging** / append-only logs.
- Search: "POPIA cross-border transfer", "pii masking vs tokenization",
  "append only audit log design".

## Iteration 5 — transform
- SQL: `CREATE TABLE AS`, joins, aggregations, window functions, `GROUP BY`.
- **Dimensional modelling** at a light level (facts vs dimensions) — enough to name it.
- Quarantine / dead-letter patterns for bad rows.
- Search: "dimensional modelling star schema basics", "dead letter quarantine ETL".

## Iteration 6 — orchestration & idempotency
- **Idempotency** in pipelines: upserts/merges, truncate-and-reload, run keys.
- Basic logging in Python (`logging` module).
- Search: "idempotent data pipeline", "truncate and reload vs merge".

## Ties back to the certs path
Everything above is cloud-agnostic on purpose — that's the "fundamentals first"
advice. When you do AWS Cloud Practitioner → Data Engineer Associate, you'll be
re-meeting these same ideas wearing S3 / Glue / Redshift / Lake Formation names,
and they'll feel obvious instead of new.
