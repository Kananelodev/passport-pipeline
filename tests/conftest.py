"""Shared pytest fixtures.

Add fixtures here as you need them — e.g. an in-memory DuckDB connection, or a
few sample rows. Kept minimal on purpose; grow it to serve your tests.
"""
import runpy
from pathlib import Path

import duckdb  # type: ignore
import pytest

GENERATOR = Path(__file__).resolve().parents[1] / "scripts" / "generate_sample_data.py"


@pytest.fixture
def con():
    """A throwaway in-memory DuckDB connection for fast, isolated tests."""
    connection = duckdb.connect(":memory:")
    yield connection
    connection.close()


@pytest.fixture(scope="session")
def raw_dir(tmp_path_factory):
    """Freshly generated raw CSVs in a temp folder, so tests don't need `make seed`.

    The generator seeds its RNG at import, so every run produces the same data.
    """
    path = tmp_path_factory.mktemp("raw")
    module = runpy.run_path(str(GENERATOR), run_name="generator")
    module["main"].__globals__["RAW_DIR"] = path
    module["main"]()
    return path
