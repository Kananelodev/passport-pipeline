"""Iteration 4 — implement govern.py."""
import pytest

from passport_pipeline import govern


def test_masking_is_deterministic():
    """Same input + strategy must give the same output (so joins survive)."""
    a = govern.mask_value("0821234567", "hash")
    b = govern.mask_value("0821234567", "hash")
    assert a == b

def test_masking_actually_hides_value():
    masked = govern.mask_value("0821234567", "hash")
    assert "0821234567" not in masked


# @pytest.mark.skip(reason="Un-skip once classify_transfer + a policy dict are ready.")
def test_flags_cross_border():
    policy = {
        "allowed_regions": ["af-south-1"],
        "flagged_regions": ["eu-west-1"],
        "on_unknown_region": "block",
    }
    assert govern.classify_transfer("af-south-1", "eu-west-1", policy) == "cross_border_flagged"
    assert govern.classify_transfer("af-south-1", "af-south-1", policy) == "domestic"
