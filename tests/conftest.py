"""Shared pytest fixtures.

Add fixtures here as you need them — e.g. an in-memory DuckDB connection, or a
few sample rows. Kept minimal on purpose; grow it to serve your tests.
"""
import duckdb  # type: ignore
import pytest


@pytest.fixture
def con():
    """A throwaway in-memory DuckDB connection for fast, isolated tests."""
    connection = duckdb.connect(":memory:")
    yield connection
    connection.close()
