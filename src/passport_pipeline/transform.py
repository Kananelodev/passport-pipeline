"""Transform bronze -> silver -> gold.  [Iteration 5]

The set-based work lives in SQL (sql/staging, sql/marts). This module is the thin
Python that does what SQL can't on its own, then runs the models in order:

  1. Judge:    run the contract validator (validate.py) over bronze and load
               every violation into a temp table, `contract_violations`.
  2. Equip:    register govern.py's masking + residency rules as SQL functions
               (mask_pii, classify_transfer), so there's ONE implementation of
               each rule, shared by Python and SQL.
  3. Build:    run the staging models (quarantine first, then the silver tables
               that anti-join against it), then the marts.

Every model is CREATE OR REPLACE, so re-running rebuilds the same tables from
bronze rather than appending: the transform is idempotent by construction.
"""
from __future__ import annotations

import duckdb  # type: ignore
from duckdb.typing import VARCHAR  # type: ignore

from passport_pipeline import config, govern, validate
from passport_pipeline.warehouse import run_sql_file

STAGING_DIR = config.SQL_DIR / "staging"
MARTS_DIR = config.SQL_DIR / "marts"
CHECKS_DIR = config.SQL_DIR / "checks"

# Order matters: each model reads the ones before it.
STAGING_MODELS = ["quarantine.sql", "stg_customers.sql", "stg_transactions.sql"]
MART_MODELS = [
    "daily_revenue_by_province.sql",
    "customer_transaction_summary.sql",
    "cross_border_transfer_report.sql",
]
DATASETS = ["customers", "transactions"]


def _load_contracts() -> dict[str, dict]:
    return {
        name: validate.load_contract(config.CONTRACTS_DIR / f"{name}.yml")
        for name in DATASETS
    }


def _register_udfs(con: "duckdb.DuckDBPyConnection", policy: dict) -> None:
    """Expose govern.py's rules to SQL.

    DuckDB refuses to register a name twice, so drop any earlier registration:
    the pipeline may call build_silver more than once on the same connection.
    NULL in -> NULL out is DuckDB's default, so nullable columns stay NULL.
    """
    udfs = {
        "mask_pii": (govern.mask_value, [VARCHAR, VARCHAR]),
        "classify_transfer": (
            lambda home, processing: govern.classify_transfer(home, processing, policy),
            [VARCHAR, VARCHAR],
        ),
    }
    for name, (fn, params) in udfs.items():
        try:
            con.remove_function(name)
        except duckdb.InvalidInputException:
            pass  # not registered yet
        con.create_function(name, fn, params, VARCHAR)


def _load_contract_violations(
    con: "duckdb.DuckDBPyConnection", contracts: dict[str, dict]
) -> int:
    """Run every contract check over bronze into TEMP table contract_violations.

    TEMP: it's an intermediate for quarantine.sql, scoped to this connection and
    never persisted. The validator's reasons quote the offending value, so for
    PII columns the reason is redacted. Otherwise the quarantine table would
    leak the very ID numbers and emails that silver masks.
    """
    pii = {(name, col) for name, c in contracts.items() for col in govern.pii_columns(c)}

    violations: list[validate.Violation] = []
    for name, contract in contracts.items():
        violations += validate.validate_dataset(validate.fetch_rows(con, name), contract)
    violations += validate.run_set_checks(con, CHECKS_DIR)

    rows = {
        (
            v.dataset,
            v.row_id,
            v.column,
            v.rule,
            f"{v.rule} check failed (value redacted: PII)"
            if (v.dataset, v.column) in pii else v.reason,
        )
        for v in violations
    }
    con.execute("""
        CREATE OR REPLACE TEMP TABLE contract_violations (
            dataset VARCHAR, record_key VARCHAR, column_name VARCHAR,
            rule VARCHAR, reason VARCHAR
        )
    """)
    if rows:
        con.executemany(
            "INSERT INTO contract_violations VALUES (?, ?, ?, ?, ?)", sorted(rows)
        )
    return len(rows)


def _build_pii_inventory(
    con: "duckdb.DuckDBPyConnection", contracts: dict[str, dict]
) -> None:
    """silver.pii_inventory: a queryable record of every PII column and its fate.

    Derived from the contracts, so it can't drift from them. The cross-border
    report reads it to say WHICH personal information a transfer touched.
    """
    rows = [
        (name, col["name"], col.get("mask", "none"))
        for name, contract in contracts.items()
        for col in contract.get("columns", [])
        if col["name"] in govern.pii_columns(contract)
    ]
    con.execute("""
        CREATE OR REPLACE TABLE silver.pii_inventory (
            dataset VARCHAR, column_name VARCHAR, mask_strategy VARCHAR
        )
    """)
    if rows:
        con.executemany("INSERT INTO silver.pii_inventory VALUES (?, ?, ?)", rows)


def _count(con: "duckdb.DuckDBPyConnection", sql: str) -> int:
    return con.execute(sql).fetchone()[0]


def build_silver(con: "duckdb.DuckDBPyConnection") -> None:
    """Bronze -> Silver.

    Silver = clean, typed, deduplicated, PII-masked, VALID rows only. Every
    rejected row is accounted for in silver.quarantine with a reason.
    """
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {config.SILVER}")
    contracts = _load_contracts()
    policy = govern.load_residency_policy(config.RESIDENCY_POLICY)

    _register_udfs(con, policy)
    n_violations = _load_contract_violations(con, contracts)
    _build_pii_inventory(con, contracts)
    for model in STAGING_MODELS:
        run_sql_file(con, STAGING_DIR / model)

    govern.audit("build_silver", {
        "contract_violations": n_violations,
        "quarantined_records": _count(
            con, "SELECT COUNT(DISTINCT (dataset, record_key)) FROM silver.quarantine"
        ),
        "silver_customers": _count(con, "SELECT COUNT(*) FROM silver.customers"),
        "silver_transactions": _count(con, "SELECT COUNT(*) FROM silver.transactions"),
        "cross_border_transactions": _count(
            con,
            "SELECT COUNT(*) FROM silver.transactions WHERE processing_region <> home_region",
        ),
    })


def build_gold(con: "duckdb.DuckDBPyConnection") -> None:
    """Silver -> Gold marts (sql/marts/*.sql), each a CREATE OR REPLACE TABLE."""
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {config.GOLD}")
    for model in MART_MODELS:
        run_sql_file(con, MARTS_DIR / model)
