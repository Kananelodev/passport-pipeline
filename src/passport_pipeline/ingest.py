"""Ingest raw CSVs into the BRONZE layer, unchanged.  [Iteration 2]

Golden rule: bronze is immutable and faithful to the source. Do NOT clean, cast,
or filter here. The only columns you add are lineage columns.
"""
from __future__ import annotations

from pathlib import Path

import duckdb  # type: ignore


def ingest_csv(con: "duckdb.DuckDBPyConnection", csv_path: Path, table: str) -> int:
    """Load one CSV into bronze.<table> exactly as-is, plus lineage columns.

    Add:
        _ingested_at  : the load timestamp (now)
        _source_file  : the csv file name

    Load everything as text/varchar for now — bronze doesn't enforce types.
    Return the number of rows loaded. Make it safe to re-run (Iteration 6 will
    lean on this being idempotent — think about how you'll handle a re-load).
    """
    raise NotImplementedError


def ingest_all(con: "duckdb.DuckDBPyConnection") -> dict[str, int]:
    """Ingest customers.csv and transactions.csv from config.RAW_DIR.

    Return a dict of {table_name: row_count}.
    """
    raise NotImplementedError
