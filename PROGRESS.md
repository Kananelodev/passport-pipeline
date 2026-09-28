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
| 1 Warehouse     | 🟢 | — | test_warehouse.py   |
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


### 2026-09-27: Iteration 1: test_warehouse.py
- `src/passport_pipeline/warehouse.py` is the one that  enables connection to the DuckDB database `connect` and same with creating sample-data generator I had to make sure that the parent directory existed
- Had to import `duckdb` to enable us to have access to `DuckDB` database 
- The reason we are using `DuckDB` is because it's `OLAP` so it's best used for transactions compared to `OLTP` which is best used for analytical. Also it's because it serves as no port, no credentials just a file that can connect to the database with code
- I also created `create_schemas`, three schemas `bronze`: which we use for auditability and also reprocessing, this means that we can always see the source data and also gives us the ability to go back to the orginal should our cleaning logic break which means we can go the data. `silver`: This is where the data is cleaned and conformed. `gold`: This is when the data is business-aggregates ready
- Then we create a `run_sql_file` that enables us to read the sql file and execute it against the connection

### 2026-09-28: Iteration 2: ingest.py
- I implemented the `ingest.py` so to enable me to land the the raw CSVs into the the `bronze` tables unedited and unmodified
- I learned why we have `bronze` as part of the medallion architecture and how `bronze` is more about restraint in terms of not rushing to clean data
- The reason we have this is for `forensic` so that we have the orginal and other medallions can build from the data
- Learned about `Data Lineage` which helps us to check where the data came from and also what happened. Implemented those via `_source_file` and `ingested_at` which are our lineage columns
- Learned about what is `DataFrame` and how to use `pandas` to enable us to read the csv so we can ingest the data into the `warehouse`
- `con.register("staging_df", df)`: you put a name tag on the `DataFrame` so `DuckDB` can see it. Nothing is copied yet. DuckDB just gets a window onto the data, under the name `staging_df.`
- `CREATE OR REPLACE TABLE bronze.customers AS SELECT * FROM staging_df`: now you use that name in SQL. This reads everything through the window and `writes` it into a real table in the warehouse. This is the moment the data becomes `permanent.`
- `con.unregister("staging_df")`: you take the name tag off. The window closes. The table stays, because it was already copied into the warehouse.


### YYYY-MM-DD — Scaffold set up
- Cloned the skeleton, read the roadmap, got `make setup` working.
- Surprise: No suprises so far
- Next: Iteration 0 — write the sample-data generator.

<!-- Add new entries above this line, newest first. -->



---


