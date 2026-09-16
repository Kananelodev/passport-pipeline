"""Iteration 6 — the whole thing, and idempotency.

The final proof: run the pipeline twice and assert the warehouse state is
identical (same row counts, same mart contents). Write this once `run()` works.
"""
import pytest


@pytest.mark.skip(reason="Iteration 6: assert running run() twice is idempotent.")
def test_pipeline_is_idempotent():
    ...
