"""Render the cross-border report as a stamped passport.  [Rollout]

Run: `make site` (builds the whole site), or this script alone after `make run`

Reads the gold + silver layers and writes site/index.html, a self-contained
page where every cross-border transfer is a visa stamp in a data subject's
passport. Only already-masked silver values are used, so the page never sees
raw PII: the "photo" is an identicon of the tokenised SA ID.
"""
import json
import sys
from pathlib import Path

import duckdb  # type: ignore
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from passport_pipeline import config  # noqa: E402

TEMPLATE = Path(__file__).with_name("passport_template.html")
OUT = ROOT / "site" / "index.html"

REGION_NAMES = {
    "af-south-1": "Cape Town",
    "eu-west-1": "Ireland",
    "us-east-1": "N. Virginia",
}


def rows(con, sql: str) -> list[dict]:
    rel = con.sql(sql)
    cols = rel.columns
    return [dict(zip(cols, r)) for r in rel.fetchall()]


def main() -> None:
    con = duckdb.connect(str(config.WAREHOUSE_PATH), read_only=True)

    subjects = rows(con, """
        SELECT c.customer_id, c.sa_id_number, c.email, c.phone, c.province,
               CAST(c.signup_date AS VARCHAR) AS signup_date, c.home_region,
               COUNT(*) FILTER (WHERE t.processing_region =  t.home_region) AS domestic_txns
        FROM silver.customers c
        JOIN silver.transactions t USING (customer_id)
        GROUP BY ALL
        HAVING COUNT(*) FILTER (WHERE t.processing_region <> t.home_region) > 0
    """)
    stamps = rows(con, """
        SELECT transaction_id, customer_id, processing_region, residency_status,
               CAST(amount_zar AS DOUBLE) AS amount_zar, merchant,
               strftime(txn_timestamp, '%Y-%m-%d') AS txn_date
        FROM silver.transactions
        WHERE processing_region <> home_region
        ORDER BY txn_timestamp
    """)
    for s in subjects:
        s["stamps"] = [st for st in stamps if st["customer_id"] == s["customer_id"]]
    # Busiest traveller first: most distinct regions, then most stamps.
    subjects.sort(key=lambda s: (-len({st["processing_region"] for st in s["stamps"]}),
                                 -len(s["stamps"]), s["customer_id"]))

    totals = rows(con, """
        SELECT SUM(transfer_count) AS transfers,
               CAST(SUM(amount_zar) AS DOUBLE) AS amount_zar,
               COUNT(DISTINCT transfer_month) AS months
        FROM gold.cross_border_transfer_report
    """)[0]
    totals["subjects"] = len(subjects)
    totals["blocked"] = con.sql(
        "SELECT COUNT(*) FROM silver.quarantine WHERE rule = 'residency_blocked'"
    ).fetchone()[0]

    pii = rows(con, """
        SELECT column_name, mask_strategy FROM silver.pii_inventory
        WHERE dataset = 'customers'
    """)
    con.close()

    policy = yaml.safe_load(config.RESIDENCY_POLICY.read_text(encoding="utf-8"))
    data = {
        "subjects": subjects,
        "totals": totals,
        "pii": pii,
        "home_region": policy["home_region"],
        "flagged_regions": policy.get("flagged_regions", []),
        "region_names": REGION_NAMES,
    }

    payload = json.dumps(data, default=str).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("__PASSPORT_DATA__", payload)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {len(subjects)} passports, {len(stamps)} stamps -> {OUT}")


if __name__ == "__main__":
    main()
