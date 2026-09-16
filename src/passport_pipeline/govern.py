"""Governance: PII handling, residency, and audit — the passport layer. [Iter 4]

Everything here is what makes this project more than a CSV-mover. Take your time.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


def pii_columns(contract: dict) -> list[str]:
    """Return the names of columns marked `pii: true` in the contract."""
    raise NotImplementedError


def mask_value(value: str, strategy: str) -> str:
    """Mask a single value according to `strategy`.

    Strategies used by the contracts:
      - 'hash'     : one-way hash (e.g. sha256) — same input -> same output.
      - 'tokenise' : replace with a stable surrogate token (think: a lookup you
                     could reverse if authorised; for now a deterministic token).
      - 'partial'  : keep only a small, non-identifying part (e.g. last 3 digits).
    Choose your exact scheme and document it. Consistency matters — the same
    input should mask to the same output across runs (so joins still work).
    """
    raise NotImplementedError


def load_residency_policy(path: Path) -> dict[str, Any]:
    """Load residency_policy.yml."""
    raise NotImplementedError


def classify_transfer(home_region: str, processing_region: str, policy: dict) -> str:
    """Return the residency verdict for a single record.

    Suggested outcomes: 'domestic', 'cross_border_flagged', 'blocked'.
    Use the allowed_regions / flagged_regions / on_unknown_region rules from the
    policy. This function is the core of your cross-border report later.
    """
    raise NotImplementedError


def audit(event: str, details: dict) -> None:
    """Append one entry to an append-only audit log.

    Record at least: timestamp, event name, and the details dict (e.g. how many
    rows moved cross-border in this run). Append-only — never overwrite history.
    Decide the sink: a table in the warehouse, or a JSONL file. Justify it.
    """
    raise NotImplementedError
