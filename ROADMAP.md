# Roadmap

Build in this order. Each milestone has a **Definition of Done (DoD)** — the tests
that must pass and the visible result. Don't skip ahead; each layer assumes the one
before it works. Commit at every green milestone so your git history *is* your
progress story.

Legend: 🔴 not started · 🟡 in progress · 🟢 done

---

## Iteration 0 — Environment & sample data  🔴
Get the project running and produce data to work with.

- [ ] `make setup` installs cleanly into a venv.
- [ ] Implement `scripts/generate_sample_data.py` to the spec in its docstring:
      writes `data/raw/customers.csv` and `data/raw/transactions.csv` with
      realistic-but-fake SA data (including some deliberately *invalid* rows so
      validation has something to catch).
- **DoD:** `make seed` creates both CSVs; eyeballing them shows valid + invalid rows.

## Iteration 1 — Warehouse & config  🔴
- [ ] Implement `warehouse.py`: open/close a DuckDB connection, run a SQL file,
      create the bronze/silver/gold schemas.
- **DoD:** `test_warehouse.py` green. You can open a DuckDB shell and see the schemas.

## Iteration 2 — Ingest (→ Bronze)  🔴
- [ ] Implement `ingest.py`: land the raw CSVs into bronze tables **unchanged**,
      adding only lineage columns (`_ingested_at`, `_source_file`).
- **DoD:** `test_ingest.py` green. Bronze row counts equal the CSV row counts.

## Iteration 3 — Validation  🔴
The heart of "data quality as a gate."
- [ ] Implement `validate.py`: a set of checks driven by the data contracts in
      `governance/data_contracts/`. At minimum: not-null, type, SA-ID checksum,
      email + phone format, `amount_zar >= 0`, unique transaction_id,
      referential integrity (every txn.customer_id exists).
- **DoD:** `test_validate.py` green. Valid rows pass; the seeded bad rows are caught
      and reported with a reason.

## Iteration 4 — Governance  🔴
The passport layer.
- [ ] Implement `govern.py`:
      - PII detection (which columns are personal, from the contract),
      - masking/tokenisation of PII for the silver layer,
      - residency tagging (attach home_region + processing_region),
      - an append-only audit log of what ran and what data moved.
- **DoD:** `test_govern.py` green. Masked columns are unreadable in silver; the
      audit log records each run.

## Iteration 5 — Transform (Bronze → Silver → Gold)  🔴
- [ ] Implement `transform.py` + the SQL in `sql/staging/` and `sql/marts/`:
      - **silver**: cleaned, typed, deduped, PII-masked, valid rows only; bad rows
        routed to a `quarantine` table.
      - **gold** marts: `daily_revenue_by_province`,
        `customer_transaction_summary`, and the showpiece
        `cross_border_transfer_report`.
- **DoD:** `test_transform.py` green. The three marts exist and return sensible rows.

## Iteration 6 — Orchestrate end-to-end  🔴
- [ ] Finish `pipeline.py`: run seed → ingest → validate → govern → transform in
      order, with logging, and make it **idempotent** (re-running gives the same
      result, no duplicates).
- **DoD:** `make run` twice in a row produces identical warehouse state.
      `test_pipeline.py` green. **Full suite green — this is the demoable version.**

---

## Stretch (only after the suite is green)

- [ ] Swap the hand-rolled transforms for **dbt-duckdb** models — great to talk about.
- [ ] Add a real orchestrator (Prefect or Dagster) around the same stages.
- [ ] Replace local folders with **S3** and DuckDB-over-parquet; note the residency
      implications of bucket regions.
- [ ] A tiny Streamlit page that renders the cross-border report — a visual for demos.
- [ ] Data-quality metrics over time (how many rows quarantined per run).

Each stretch item is a self-contained talking point. Don't start them until
Iteration 6 is green — a finished small thing beats a half-built big thing.
