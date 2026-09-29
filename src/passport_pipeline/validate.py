"""Data-quality validation driven by data contracts."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
import re
import yaml


@dataclass
class Violation:
    """Represents a single contract rule failure."""
    dataset: str
    row_number: int | None
    row_id: str
    column: str
    rule: str
    reason: str


def load_contract(path: Path) -> dict[str, Any]:
    """Load and parse a YAML data contract into a dict."""
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def is_valid_sa_id(value: str) -> bool:
    """Return True if `value` is a structurally valid South African ID number."""
    if not isinstance(value, str):
        value = str(value)

    # 1. Exactly 13 digits
    if not value.isdigit() or len(value) != 13:
        return False

    # 2. First 6 digits encode a real date (YYMMDD)
    try:
        datetime.strptime(value[:6], "%y%m%d")
    except ValueError:
        return False

    # 3. Luhn checksum over 13 digits
    total_sum = 0
    for i, char in enumerate(value):
        digit = int(char)
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total_sum += digit

    return total_sum % 10 == 0




EMAIL_REGEX = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
PHONE_REGEX = re.compile(r"\+27\d{9}")

# Each rule returns a reason string if the value FAILS, or None if it passes.
def check_sa_id(value, _arg):
    return None if is_valid_sa_id(value) else f"Invalid SA ID (format or checksum): '{value}'"

def check_email(value, _arg):
    return None if EMAIL_REGEX.fullmatch(value) else f"Invalid email: '{value}'"

def check_phone(value, _arg):
    return None if PHONE_REGEX.fullmatch(value) else f"Phone must be +27 then 9 digits: '{value}'"

def check_allowed(value, allowed):
    return None if value in allowed else f"'{value}' not in allowed set {allowed}"

def check_min(value, minimum):
    try:
        number = float(value)
    except ValueError:
        return f"Not a number: '{value}'"
    return None if number >= minimum else f"{number} is below minimum {minimum}"

def check_type(value, expected):
    try:
        if expected in ("int", "integer"):
            int(value)
        elif expected in ("float", "numeric", "decimal"):
            float(value)
    except ValueError:
        return f"Cannot read '{value}' as {expected}"
    return None


CHECKS = {
    "type": check_type,
    "allowed_values": check_allowed,
    "sa_id": check_sa_id,
    "email": check_email,
    "phone": check_phone,
    "min": check_min,
}
# Keys that are valid in the YAML but are not row-level rules.
NON_RULE_KEYS = {"name", "nullable", "pii", "mask", "description", "unique", "foreign_key"}


def _reject_unknown_keys(contract: dict[str, Any]) -> None:
    known = set(CHECKS) | NON_RULE_KEYS
    for col in contract.get("columns", []):
        unknown = set(col) - known
        if unknown:
            raise ValueError(
                f"{contract.get('dataset')}.{col['name']}: unknown contract keys {sorted(unknown)}"
            )


def validate_dataset(rows: list[dict[str, Any]], contract: dict[str, Any]) -> list[Violation]:
    _reject_unknown_keys(contract)
    dataset = contract.get("dataset", "unnamed_dataset")
    pk_col = contract.get("primary_key")
    columns = contract.get("columns", [])
    violations: list[Violation] = []

    for row_number, row in enumerate(rows, start=1):
        row_id = str(row.get(pk_col, f"row_{row_number}"))

        for col in columns:
            name = col["name"]
            raw = row.get(name)
            text = "" if raw is None else str(raw).strip()

            failures: list[tuple[str, str]] = []   # (rule, reason)
            if text == "":
                if not col.get("nullable", True):
                    failures.append(("not_null", "Required field is missing or empty"))
            else:
                for rule, arg in col.items():
                    if rule in CHECKS and arg is not False:
                        reason = CHECKS[rule](text, arg)
                        if reason:
                            failures.append((rule, reason))

            violations.extend(
                Violation(dataset, row_number, row_id, name, rule, reason)
                for rule, reason in failures
            )
    return violations



from passport_pipeline.warehouse import fetch_sql_file

SET_CHECKS = [
    # (sql file, dataset, column, rule, how to describe one returned row)
    ("duplicate_customer_ids.sql", "customers", "customer_id", "unique",
     lambda r: f"customer_id appears {r[1]} times"),
    ("duplicate_transaction_ids.sql", "transactions", "transaction_id", "unique",
     lambda r: f"transaction_id appears {r[1]} times"),
    ("orphan_transactions.sql", "transactions", "customer_id", "referential_integrity",
     lambda r: f"customer_id '{r[1]}' not found in customers"),
]


def run_set_checks(con, checks_dir: Path) -> list[Violation]:
    violations = []
    for filename, dataset, column, rule, describe in SET_CHECKS:
        for row in fetch_sql_file(con, checks_dir / filename):
            violations.append(
                Violation(dataset, None, str(row[0]), column, rule, describe(row))
            )
    return violations


def fetch_rows(con, table: str) -> list[dict[str, Any]]:
    cur = con.execute(f"SELECT * FROM bronze.{table}")
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]