"""Iteration 1 — make these pass by implementing warehouse.py."""
from passport_pipeline import warehouse


def test_create_schemas_makes_medallion_layers(con):
    warehouse.create_schemas(con)
    schemas = {r[0] for r in con.sql(
        "select schema_name from information_schema.schemata"
    ).fetchall()}
    assert {"bronze", "silver", "gold"}.issubset(schemas)
