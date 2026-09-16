"""Data-quality validation driven by the data contracts.  [Iteration 3]

This is the "quality as a gate" milestone. Read the YAML contracts in
governance/data_contracts/ and check each row against the rules.

Design suggestion (yours to change): represent each failure as a small record
(row identifier, column, rule, reason) so you can both quarantine the row and
report *why* it failed. Silent dropping is the thing you're proving you DON'T do.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Violation:
    """One failed check. Fill in fields as makes sense to you."""
    dataset: str
    row_id: str
    column: str
    rule: str
    reason: str


def load_contract(path: Path) -> dict[str, Any]:
    """Load and parse a YAML data contract into a dict."""
    raise NotImplementedError


def is_valid_sa_id(value: str) -> bool:
    """Return True if `value` is a structurally valid South African ID number.

    Rules to implement:
      - exactly 13 digits,
      - first 6 encode a real calendar date (YYMMDD),
      - final digit is a valid Luhn checksum of the first 12.
    (Study the SA ID structure + Luhn algorithm — see LEARNING.md, Iter 0/3.)
    """
    raise NotImplementedError


def validate_dataset(rows: list[dict], contract: dict) -> list[Violation]:
    """Check every row against the contract; return all violations found.

    Cover at least: not-null, type, unique key, allowed-values, the SA-ID rule,
    email + phone format, and amount_zar >= 0. Referential integrity
    (transactions -> customers) needs both datasets — decide where that lives.
    """
    raise NotImplementedError
