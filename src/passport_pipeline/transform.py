"""Transform bronze -> silver -> gold.  [Iteration 5]

You can do this in Python, in SQL (files under sql/), or a mix. Prefer SQL for the
set-based work — it's what the job actually looks like. transform.py is the thin
Python that orchestrates running those SQL models via warehouse.run_sql_file.
"""
from __future__ import annotations

import duckdb  # type: ignore


def build_silver(con: "duckdb.DuckDBPyConnection") -> None:
    """Bronze -> Silver.

    Silver = clean, typed, deduplicated, PII-masked, VALID rows only.
    - cast columns to their real types (per the contract),
    - drop/route invalid rows to a `silver.quarantine` table (don't lose them),
    - apply the masking from govern.py to PII columns,
    - attach residency classification to transactions.
    Write the logic in sql/staging/*.sql and call it from here.
    """
    raise NotImplementedError


def build_gold(con: "duckdb.DuckDBPyConnection") -> None:
    """Silver -> Gold marts.

    Build at least these three (SQL in sql/marts/*.sql):
      - daily_revenue_by_province
      - customer_transaction_summary
      - cross_border_transfer_report   <- the showpiece: which PII was processed
                                          outside its home region, and how much.
    """
    raise NotImplementedError
