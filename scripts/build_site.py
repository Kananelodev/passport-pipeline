"""Build the public GitHub Pages site into site/.  [Rollout]

Run: `make site`  (needs `make run` first so the warehouse exists)

    site/index.html   the stamped-passport view of the cross-border report
    site/query.html   a SQL console running DuckDB-WASM in the browser
    site/data/*.parquet + tables.json   what the console queries

Only gold and silver are exported. Bronze holds raw (synthetic) PII by design,
so it never leaves the warehouse — the published site gets the same view an
analyst would. CI builds this with a test-only TOKENIZATION_KEY, so nothing
derived from a real key is ever published.
"""
import json
import shutil
import sys
from pathlib import Path

import duckdb  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))
from passport_pipeline import config  # noqa: E402
import render_passport  # noqa: E402

SITE = ROOT / "site"
DATA = SITE / "data"
EXPORT_SCHEMAS = ("silver", "gold")


def export_tables(con) -> list[dict]:
    tables = con.sql(f"""
        SELECT table_schema, table_name FROM information_schema.tables
        WHERE table_schema IN {EXPORT_SCHEMAS} AND table_type = 'BASE TABLE'
        ORDER BY table_schema DESC, table_name
    """).fetchall()

    manifest = []
    for schema, table in tables:
        cols = con.sql(f"""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_schema = '{schema}' AND table_name = '{table}'
            ORDER BY ordinal_position
        """).fetchall()
        # DECIMAL -> DOUBLE: Arrow decimals don't render cleanly in the browser.
        select = ", ".join(
            f'CAST("{c}" AS DOUBLE) AS "{c}"' if t.startswith("DECIMAL") else f'"{c}"'
            for c, t in cols
        )
        out = DATA / f"{schema}.{table}.parquet"
        con.sql(f"COPY (SELECT {select} FROM {schema}.{table}) TO '{out.as_posix()}' (FORMAT parquet)")
        rows = con.sql(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0]
        manifest.append({
            "schema": schema, "table": table, "file": out.name, "rows": rows,
            "columns": [{"name": c, "type": "DOUBLE" if t.startswith("DECIMAL") else t} for c, t in cols],
        })
    return manifest


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    DATA.mkdir(parents=True)

    render_passport.main()

    con = duckdb.connect(str(config.WAREHOUSE_PATH), read_only=True)
    manifest = export_tables(con)
    con.close()
    (DATA / "tables.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    shutil.copy(Path(__file__).with_name("query_template.html"), SITE / "query.html")
    (SITE / ".nojekyll").touch()
    print(f"Exported {len(manifest)} tables -> {DATA}")


if __name__ == "__main__":
    main()
