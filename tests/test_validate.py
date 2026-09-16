"""Iteration 3 — implement validate.py.

The SA-ID tests below are real and should pass once is_valid_sa_id works. Replace
the placeholder IDs with numbers you've verified by hand (compute the Luhn digit
yourself — doing it once teaches you the algorithm).
"""
import pytest

from passport_pipeline import validate


class TestSaIdChecksum:
    def test_rejects_wrong_length(self):
        assert validate.is_valid_sa_id("12345") is False

    def test_rejects_non_digits(self):
        assert validate.is_valid_sa_id("80010150091AB") is False

    @pytest.mark.skip(reason="Put a hand-verified VALID SA ID here, then un-skip.")
    def test_accepts_valid_id(self):
        assert validate.is_valid_sa_id("REPLACE_WITH_VALID_13_DIGIT_ID") is True

    @pytest.mark.skip(reason="Put an ID with a wrong checksum here, then un-skip.")
    def test_rejects_bad_checksum(self):
        assert validate.is_valid_sa_id("REPLACE_WITH_BAD_CHECKSUM_ID") is False


@pytest.mark.skip(reason="Build validate_dataset, then design this against your contract.")
def test_amount_must_be_non_negative():
    contract = {"dataset": "transactions", "columns": [
        {"name": "amount_zar", "type": "decimal", "nullable": False},
    ]}
    rows = [{"transaction_id": "T1", "amount_zar": "-5"}]
    violations = validate.validate_dataset(rows, contract)
    assert any("amount_zar" == v.column for v in violations)
