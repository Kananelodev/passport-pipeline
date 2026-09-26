# Progress log



## How to use it
- After each milestone, add a dated entry: what you built, one thing that surprised
  you, one thing you'd do differently.
- Screenshot `make test` going from red to green over time — visible progress beats
  claims.

---

## Milestone tracker
| Iteration | Status | Date done | Test file            |
|-----------|--------|-----------|----------------------|
| 0 Sample data   | 🟢 | 2026-09-27 | (manual)     |
| 1 Warehouse     | 🔴 | — | test_warehouse.py   |
| 2 Ingest        | 🔴 | — | test_ingest.py      |
| 3 Validation    | 🔴 | — | test_validate.py    |
| 4 Governance    | 🔴 | — | test_govern.py      |
| 5 Transform     | 🔴 | — | test_transform.py   |
| 6 Orchestration | 🔴 | — | test_pipeline.py    |

---

## Log

### 2026-09-27- Iteration 0: sample-data generator
- `scripts/generate_sample_data.py` writes `data/raw/customers.csv` (200 rows) and
  `data/raw/transactions.csv` (1000 rows). SA ID numbers are built by hand from
  YYMMDD + sequence + citizenship + race digit + a Luhn check digit.
- 9 bad rows injected on purpose (4 customers, 5 transactions), plus 40 valid
  cross-border transactions for the governance layer to flag. Iteration 3 should
  catch exactly 9.
- faker has no `en_ZA` locale in v30, so names come from a `zu_ZA` + `en_GB` mix.
- All dates are anchored to a fixed `REFERENCE_DATE` instead of `today`, so two
  runs produce byte-identical CSVs — verified by diffing consecutive runs.
- Surprise: Had to research about creating a path that would both run on different OS
- Next: Iteration 1 — warehouse.py + DuckDB schemas.

### YYYY-MM-DD — Scaffold set up
- Cloned the skeleton, read the roadmap, got `make setup` working.
- Surprise: No suprises so far
- Next: Iteration 0 — write the sample-data generator.

<!-- Add new entries above this line, newest first. -->

---


