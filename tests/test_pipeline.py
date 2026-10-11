"""Iteration 6 — the whole thing, and idempotency.

The final proof: run the pipeline twice and assert the warehouse state is
identical (same row counts, same mart contents).
"""
import duckdb  # type: ignore

from passport_pipeline import config, pipeline

LAYERS = (config.BRONZE, config.SILVER, config.GOLD)
# Lineage stamp: a re-load legitimately gets a new timestamp. Everything else
# must come out the same.
VOLATILE_COLUMNS = {"_ingested_at"}


def _snapshot(db_path) -> dict[str, list[tuple]]:
    """Every table in bronze/silver/gold -> its sorted rows, minus volatile columns."""
    con = duckdb.connect(db_path.as_posix(), read_only=True)
    try:
        tables = con.execute(
            "SELECT table_schema, table_name FROM information_schema.tables "
            f"WHERE table_schema IN {LAYERS} ORDER BY 1, 2"
        ).fetchall()
        snapshot = {}
        for schema, table in tables:
            cols = [
                c for (c,) in con.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = ? AND table_name = ? ORDER BY ordinal_position",
                    [schema, table],
                ).fetchall()
                if c not in VOLATILE_COLUMNS
            ]
            select = ", ".join(f'"{c}"' for c in cols)
            rows = con.execute(f'SELECT {select} FROM {schema}."{table}"').fetchall()
            snapshot[f"{schema}.{table}"] = sorted(rows, key=repr)
        return snapshot
    finally:
        con.close()


def test_pipeline_is_idempotent(raw_dir, tmp_path, monkeypatch):
    db_path = tmp_path / "warehouse.duckdb"
    monkeypatch.setattr(config, "RAW_DIR", raw_dir)
    monkeypatch.setattr(config, "WAREHOUSE_PATH", db_path)

    pipeline.run()
    first = _snapshot(db_path)
    pipeline.run()
    second = _snapshot(db_path)

    # Guard against a vacuous pass: the run must actually have built the layers.
    assert {"bronze.customers", "silver.transactions", "gold.daily_revenue_by_province"} <= first.keys()
    assert all(first.values()), "a table came out empty"

    assert first.keys() == second.keys(), "re-run created or dropped tables"
    for table in first:
        assert len(first[table]) == len(second[table]), f"{table}: row count changed on re-run"
        assert first[table] == second[table], f"{table}: contents changed on re-run"
