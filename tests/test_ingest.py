"""Iteration 2 — implement ingest.py.

These are a starting point. As you build, add tests for: idempotent re-load,
lineage columns present, row counts matching the source.
"""
import pytest

from passport_pipeline import ingest, warehouse


@pytest.mark.skip(reason="Write me once ingest.ingest_csv works. Remove this skip.")
def test_ingest_adds_lineage_columns(con, tmp_path):
    warehouse.create_schemas(con)
    csv = tmp_path / "customers.csv"
    csv.write_text("customer_id,first_name\nC1,Thandi\n")
    ingest.ingest_csv(con, csv, "customers")
    cols = {r[1] for r in con.sql("pragma table_info('bronze.customers')").fetchall()}
    assert "_ingested_at" in cols and "_source_file" in cols
