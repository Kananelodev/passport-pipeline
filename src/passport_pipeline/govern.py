"""Governance: PII handling, residency, and audit — the passport layer. [Iter 4]

Everything here is what makes this project more than a CSV-mover. Take your time.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib, hmac, os
import yaml
import logging

logging.basicConfig(level=logging.INFO)

def pii_columns(contract: dict) -> list[str]:
    """Return the names of columns marked `pii: true` in the contract."""
    masked_columns = []
    for column in contract.get("columns", []):
        if column.get("pii", False):
            masked_columns.append(column["name"])
    return masked_columns


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
    if strategy == "hash":
        return hashlib.sha256(value.encode()).hexdigest()
    elif strategy == "tokenise":
        # Simple deterministic tokenization using HMAC with a secret key
        secret_key = os.environ.get("TOKENIZATION_KEY", "default_secret_key")
        return hmac.new(secret_key.encode(), value.encode(), hashlib.sha256).hexdigest()
    elif strategy == "partial":
        # Keep only the last 3 characters of the value
        return value[-3:] if len(value) >= 3 else value
    else:
        raise ValueError(f"Unknown masking strategy: {strategy}")


def load_residency_policy(path: Path) -> dict[str, Any]:
    """Load residency_policy.yml."""
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def classify_transfer(home_region: str, processing_region: str, policy: dict) -> str:
    """Return the residency verdict for a single record.

    Suggested outcomes: 'domestic', 'cross_border_flagged', 'blocked'.
    Use the allowed_regions / flagged_regions / on_unknown_region rules from the
    policy. This function is the core of your cross-border report later.
    """
    allowed_regions = policy.get("allowed_regions", [])
    flagged_regions = policy.get("flagged_regions", [])
    on_unknown_region = policy.get("on_unknown_region", "blocked")

    if processing_region == home_region:
        return "domestic"
    elif processing_region in allowed_regions:
        return "domestic"
    elif processing_region in flagged_regions:
        return "cross_border_flagged"
    else:
        return on_unknown_region


def audit(event: str, details: dict) -> None:
    """Append one entry to an append-only audit log.

    Record at least: timestamp, event name, and the details dict (e.g. how many
    rows moved cross-border in this run). Append-only — never overwrite history.
    Decide the sink: a table in the warehouse, or a JSONL file. Justify it.
    """
    logging.info("Audit event: %s, Details: %s", event, details)
    

