"""DuckDB warehouse helpers.  [Iteration 1]

Implement these. Keep them thin — the point is a clean handle on the warehouse
that every other module uses.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from passport_pipeline import config  # type: ignore


def connect(db_path: Path | None = None) -> "duckdb.DuckDBPyConnection":
    """Open (creating if needed) a DuckDB connection to the warehouse.

    Use config.WAREHOUSE_PATH when db_path is None. Make sure the parent
    directory exists before connecting.
    """

    target = db_path if db_path is not None else config.WAREHOUSE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(target.as_posix())



def create_schemas(con: "duckdb.DuckDBPyConnection") -> None:
    """Create the bronze / silver / gold schemas if they don't exist.

    (In DuckDB these are SCHEMAs: `CREATE SCHEMA IF NOT EXISTS bronze;` etc.)
    """
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")
    con.execute("CREATE SCHEMA IF NOT EXISTS silver;")
    con.execute("CREATE SCHEMA IF NOT EXISTS gold;")
    


def run_sql_file(con: "duckdb.DuckDBPyConnection", path: Path) -> None:
    """Read a .sql file and execute it against the connection.

    You'll use this in Iteration 5 to run the files in sql/staging and sql/marts.
    """
    con.execute(path.read_text(encoding="utf-8"))
