"""Iteration 5 — implement transform.py + the SQL models.

Kept as a skipped skeleton because these need seeded data and a real warehouse.
Turn it into a proper end-to-end check once build_silver / build_gold exist:
seed -> ingest -> silver -> gold, then assert the three marts exist and are sane.
"""
import pytest


@pytest.mark.skip(reason="Write the end-to-end mart assertions in Iteration 5.")
def test_cross_border_report_exists():
    ...  # assert gold.cross_border_transfer_report has rows for flagged transfers
