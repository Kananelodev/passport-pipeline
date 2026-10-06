"""Iteration 5 — bronze -> silver -> gold, end to end on freshly seeded data.

The fixture runs the real generator into a temp folder (so the tests don't depend
on `make seed` having been run), ingests it, and builds silver + gold once.
"""
import runpy
from pathlib import Path

import duckdb  # type: ignore
import pytest

from passport_pipeline import config, govern, ingest, transform, validate, warehouse

GENERATOR = Path(__file__).resolve().parents[1] / "scripts" / "generate_sample_data.py"

# What the generator injects (see its docstring) -> the rule that must catch it.
EXPECTED_QUARANTINE = {
    ("customers", "C00001", "sa_id"),
    ("customers", "C00002", "email"),
    ("customers", "C00003", "allowed_values"),
    ("customers", "C00004", "not_null"),
    ("transactions", "T000001", "min"),
    ("transactions", "T000001", "unique"),
    ("transactions", "T000002", "allowed_values"),
    ("transactions", "T000003", "not_null"),
    ("transactions", "T001000", "referential_integrity"),
}
MARTS = ["daily_revenue_by_province", "customer_transaction_summary",
         "cross_border_transfer_report"]


def _seed(raw_dir: Path) -> None:
    """Run the generator fresh (its RNG seeds at import) into raw_dir."""
    module = runpy.run_path(str(GENERATOR), run_name="generator")
    module["main"].__globals__["RAW_DIR"] = raw_dir
    module["main"]()


def _build(raw_dir: Path) -> "duckdb.DuckDBPyConnection":
    con = duckdb.connect(":memory:")
    warehouse.create_schemas(con)
    ingest.ingest_csv(con, raw_dir / "customers.csv", "customers")
    ingest.ingest_csv(con, raw_dir / "transactions.csv", "transactions")
    transform.build_silver(con)
    transform.build_gold(con)
    return con


@pytest.fixture(scope="module")
def raw_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("raw")
    _seed(path)
    return path


@pytest.fixture(scope="module")
def wh(raw_dir):
    con = _build(raw_dir)
    yield con
    con.close()


def rows(con, sql):
    return con.execute(sql).fetchall()


# --- silver -----------------------------------------------------------------

def test_every_injected_fault_is_quarantined_for_the_right_reason(wh):
    found = set(rows(wh, "SELECT dataset, record_key, rule FROM silver.quarantine"))
    assert EXPECTED_QUARANTINE <= found


def test_quarantine_only_adds_cascades_beyond_contract_faults(wh):
    """Anything quarantined that the generator didn't inject must be a child of a
    rejected customer. No false positives on good data."""
    extra = set(rows(wh, "SELECT dataset, record_key, rule FROM silver.quarantine"))
    extra -= EXPECTED_QUARANTINE
    assert extra and all(rule == "parent_quarantined" for _, _, rule in extra)


@pytest.mark.parametrize("dataset, key", [("customers", "customer_id"),
                                          ("transactions", "transaction_id")])
def test_no_record_is_lost(wh, dataset, key):
    """Conservation: every distinct bronze key is in silver XOR quarantine."""
    bronze = {r[0] for r in rows(wh, f"SELECT DISTINCT {key} FROM bronze.{dataset}")}
    silver = {r[0] for r in rows(wh, f"SELECT {key} FROM silver.{dataset}")}
    quarantined = {r[0] for r in rows(
        wh, f"SELECT record_key FROM silver.quarantine WHERE dataset = '{dataset}'")}
    assert silver.isdisjoint(quarantined)
    assert silver | quarantined == bronze


def test_silver_keys_are_unique_and_referentially_intact(wh):
    assert rows(wh, """SELECT COUNT(*) - COUNT(DISTINCT transaction_id)
                       FROM silver.transactions""") == [(0,)]
    assert rows(wh, """SELECT COUNT(*) FROM silver.transactions t
                       ANTI JOIN silver.customers c USING (customer_id)""") == [(0,)]


def test_silver_is_typed(wh):
    types = dict(rows(wh, """
        SELECT column_name, data_type FROM information_schema.columns
        WHERE table_schema = 'silver' AND table_name IN ('customers', 'transactions')
    """))
    assert types["amount_zar"] == "DECIMAL(12,2)"
    assert types["txn_timestamp"] == "TIMESTAMP"
    assert types["signup_date"] == "DATE"


def test_silver_pii_matches_the_contract(wh):
    """Contract test: every PII column is either absent (mask: drop) or present
    and never equal to its raw bronze value. Catches SQL drifting from the YAML."""
    contract = validate.load_contract(config.CONTRACTS_DIR / "customers.yml")
    strategy = {c["name"]: c.get("mask") for c in contract["columns"]}
    silver_cols = {r[0] for r in rows(wh, """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'silver' AND table_name = 'customers'""")}

    for col in govern.pii_columns(contract):
        if strategy[col] == "drop":
            assert col not in silver_cols, f"{col} should be dropped from silver"
            continue
        assert col in silver_cols
        leaks = rows(wh, f"""SELECT COUNT(*) FROM silver.customers s
                             JOIN bronze.customers b USING (customer_id)
                             WHERE s.{col} = b.{col}""")
        assert leaks == [(0,)], f"{col} reached silver unmasked"


def test_quarantine_reasons_do_not_leak_pii(wh):
    raw_id = rows(wh, "SELECT sa_id_number FROM bronze.customers WHERE customer_id = 'C00001'")[0][0]
    reasons = " ".join(r[0] for r in rows(wh, "SELECT reason FROM silver.quarantine"))
    assert raw_id not in reasons


def test_unknown_region_is_blocked_into_quarantine(raw_dir):
    con = duckdb.connect(":memory:")
    warehouse.create_schemas(con)
    ingest.ingest_csv(con, raw_dir / "customers.csv", "customers")
    ingest.ingest_csv(con, raw_dir / "transactions.csv", "transactions")
    con.execute("""UPDATE bronze.transactions SET processing_region = 'ap-south-1'
                   WHERE transaction_id = 'T000010'""")
    transform.build_silver(con)
    assert rows(con, """SELECT rule FROM silver.quarantine
                        WHERE record_key = 'T000010'""") == [("residency_blocked",)]
    assert rows(con, "SELECT COUNT(*) FROM silver.transactions WHERE transaction_id = 'T000010'") == [(0,)]
    con.close()


# --- gold -------------------------------------------------------------------

@pytest.mark.parametrize("mart", MARTS)
def test_marts_exist_and_have_rows(wh, mart):
    assert rows(wh, f"SELECT COUNT(*) FROM gold.{mart}")[0][0] > 0


def test_daily_revenue_reconciles_to_silver(wh):
    assert rows(wh, "SELECT SUM(revenue_zar) FROM gold.daily_revenue_by_province") == \
           rows(wh, "SELECT SUM(amount_zar) FROM silver.transactions")


def test_customer_summary_has_one_row_per_customer_and_reconciles(wh):
    assert rows(wh, "SELECT COUNT(*), COUNT(DISTINCT customer_id) FROM gold.customer_transaction_summary") == \
           rows(wh, "SELECT COUNT(*), COUNT(*) FROM silver.customers")
    assert rows(wh, "SELECT SUM(total_spend_zar) FROM gold.customer_transaction_summary") == \
           rows(wh, "SELECT SUM(amount_zar) FROM silver.transactions")


def test_cross_border_report_covers_every_transfer_and_nothing_domestic(wh):
    report = rows(wh, """SELECT SUM(transfer_count), SUM(amount_zar)
                         FROM gold.cross_border_transfer_report""")
    silver = rows(wh, """SELECT COUNT(*), SUM(amount_zar) FROM silver.transactions
                         WHERE processing_region <> home_region""")
    assert report == silver and report[0][0] > 0
    assert rows(wh, """SELECT COUNT(*) FROM gold.cross_border_transfer_report
                       WHERE processing_region = home_region""") == [(0,)]
    assert rows(wh, """SELECT COUNT(*) FROM gold.cross_border_transfer_report
                       WHERE pii_categories NOT LIKE '%sa_id_number%'""") == [(0,)]


def test_rebuild_is_idempotent(wh):
    """Running the transform again on the same connection changes nothing."""
    tables = ["silver.quarantine", "silver.customers", "silver.transactions",
              *(f"gold.{m}" for m in MARTS)]
    before = {t: rows(wh, f"SELECT * FROM {t} ORDER BY ALL") for t in tables}
    transform.build_silver(wh)
    transform.build_gold(wh)
    after = {t: rows(wh, f"SELECT * FROM {t} ORDER BY ALL") for t in tables}
    assert before == after
