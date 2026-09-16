"""DuckDB warehouse helpers.  [Iteration 1]

Implement these. Keep them thin — the point is a clean handle on the warehouse
that every other module uses.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb  # type: ignore


def connect(db_path: Path | None = None) -> "duckdb.DuckDBPyConnection":
    """Open (creating if needed) a DuckDB connection to the warehouse.

    Use config.WAREHOUSE_PATH when db_path is None. Make sure the parent
    directory exists before connecting.
    """
    raise NotImplementedError


def create_schemas(con: "duckdb.DuckDBPyConnection") -> None:
    """Create the bronze / silver / gold schemas if they don't exist.

    (In DuckDB these are SCHEMAs: `CREATE SCHEMA IF NOT EXISTS bronze;` etc.)
    """
    raise NotImplementedError


def run_sql_file(con: "duckdb.DuckDBPyConnection", path: Path) -> None:
    """Read a .sql file and execute it against the connection.

    You'll use this in Iteration 5 to run the files in sql/staging and sql/marts.
    """
    raise NotImplementedError
