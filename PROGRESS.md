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

### 2026-09-29: Iteration 3: validate.py
- I got to read about `Data contract` how they live in the version control so they can be seen anyone and it helps with knowing the `shape` of the data
- It helps in cases where you would have to write a lot fo if statements to check your so instead you write generic rules functions which you can from the file
- `Schemas-on-write` enforces structure at load time, this is what we would use for our `silver medallion` because that's where we reject the bad data
`Schemas-on-read` accepts anything and applies structure, this is the one we use for the `bronze medallion` because it accepts everything and brings back without "rejecting" bad data
- So basically nothing is lost at the door (`bronze`) and nothing that is unverified (`silver`) get's to the layer that analyst use
- Also went deep into `Data Quality Dimensions` which map to what type of check I am going to create
- `Completeness`: Is required data present?
- `Validity`: 	Does it conform to its rules?
- `Uniqueness`: Any unintended duplicates?
- `Consistency`: Does it agree across fields/sources?
- `Referential_Integrity`:  integrity	Do the keys point at something?
- `Timeliness`: Is it recent enough to be useful?
- Also learned that `Uniqueness` and `Referential_Integrity` are set-level properties which means that we can't check for them in isolation
- To account for this we run those checks in `sql` files
- Being done meant being able to catch bad rows but not only catch that row but also return the reason why it is bad

### 2026-09-30
- `Personal information` broader than people expect: not just names and ID numbers but anything relating to an `identifiable living person`
- A responsible party decides why and how data is processed; an `operator` processes on their behalf. If you're the `platform`, you're usually the `operator`and your obligations flow from that.
- `Cross-border transfer` is the one that really shapes our architecture because we're using `POPIA` which restricts sending personal information outside South Africa unless certain conditions don't hold.
- So where you `compute` runs and where your `storage` lives are compliance decisions not just `latency` and `cost decisions`
- My `Data Model` is setup so that `home_region`: where the person's data lives and `governance` attaches `processing_region`: where it was actually handled and should the two differ we know a transfer occured
- Essentially this is the `showpiece` of the whole project in a sense that the `cross_border_transfer_report` makes `compliance queryable` instead of it being asserted in a PDF
- `Masking vs Tokenisation vs Hashing` our contract ask for all three techniques and the choice is driven by what users still have to do with the value
- | Technique | What it does | Reversible? | Joinable? |
  | :--- | :--- | :--- | :--- |
  | **Masking (partial)** | Hides part: `+27••••••789` | No | No |
  | **Hashing** | One-way function to a fixed digest | No (but see below) | Yes same input, same hash |
  | **Tokenisation** | Swaps the value for a random token; a separate vault maps back | Yes, with vault access | Yes |`
- Because SA_ID numbers are 13 digits and also heavily structered we can't just use `hashing` because the input space is tiny. For protection I am using `secret salt` and also `HMAC key` held outside the data.
- I am using `Append-only` for the logs because this way we keep the "audit" which means by append=only we are only adding rows. The minute we are able update or delete the log, we lose the audit evidence.
- In `DuckDb` I did this by enforcing this inside my code, this meant only `INSERT` can be used not `UPDATE` or `DELETE`
- I learned that in production this would look different, they would enforced by the storage layer: `S3 object lock`, `an immutable ledger table`, `write-once buckets.`



### YYYY-MM-DD — Scaffold set up
- Cloned the skeleton, read the roadmap, got `make setup` working.
- Surprise: No suprises so far
- Next: Iteration 0 — write the sample-data generator.

<!-- Add new entries above this line, newest first. -->



---


