"""
Tests for recon_engine.reconcile — transaction matching and exception classification.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from recon_engine.normalize import normalize_transactions
from recon_engine.reconcile import reconcile_transactions


def _make_df(rows: list[dict]) -> pd.DataFrame:
    """Build a normalized transaction DataFrame from minimal row dicts."""
    defaults = {
        "txn_date": "2024-01-15",
        "txn_amount": 100.0,
        "source_file": "test.csv",
        "description": None,
        "reference": None,
    }
    df = pd.DataFrame([{**defaults, **r} for r in rows])
    return normalize_transactions(df)


# ---------------------------------------------------------------------------
# Exact match
# ---------------------------------------------------------------------------

class TestExactMatch:
    def test_identical_rows_match_exactly(self):
        a = _make_df([{"txn_amount": 285.0, "txn_date": "2024-01-15"}])
        b = _make_df([{"txn_amount": 285.0, "txn_date": "2024-01-16"}])
        result = reconcile_transactions(a, b, date_window_days=3)
        matched = result[result["match_status"] == "Exact"]
        assert len(matched) == 1

    def test_no_unmatched_when_all_match(self):
        a = _make_df([{"txn_amount": 100.0}, {"txn_amount": 200.0}])
        b = _make_df([{"txn_amount": 100.0}, {"txn_amount": 200.0}])
        result = reconcile_transactions(a, b, date_window_days=3)
        assert "Missing" not in result["match_status"].values

    def test_result_is_dataframe(self):
        a = _make_df([{"txn_amount": 100.0}])
        b = _make_df([{"txn_amount": 100.0}])
        result = reconcile_transactions(a, b)
        assert isinstance(result, pd.DataFrame)


# ---------------------------------------------------------------------------
# Missing records
# ---------------------------------------------------------------------------

class TestMissingRecords:
    def test_missing_in_b_detected(self):
        a = _make_df([{"txn_amount": 100.0}, {"txn_amount": 999.0}])
        b = _make_df([{"txn_amount": 100.0}])
        result = reconcile_transactions(a, b, date_window_days=1)
        missing = result[result["match_status"] == "Missing"]
        assert len(missing) >= 1

    def test_missing_in_a_detected(self):
        a = _make_df([{"txn_amount": 100.0}])
        b = _make_df([{"txn_amount": 100.0}, {"txn_amount": 999.0}])
        result = reconcile_transactions(a, b, date_window_days=1)
        missing = result[result["match_status"] == "Missing"]
        assert len(missing) >= 1

    def test_empty_inputs_return_empty(self):
        a = _make_df([{"txn_amount": 100.0}]).iloc[0:0]
        b = _make_df([{"txn_amount": 100.0}]).iloc[0:0]
        result = reconcile_transactions(a, b)
        assert isinstance(result, pd.DataFrame)


# ---------------------------------------------------------------------------
# Partial / amount mismatch
# ---------------------------------------------------------------------------

class TestPartialMatch:
    def test_small_amount_delta_is_partial(self):
        a = _make_df([{"txn_amount": 100.0}])
        b = _make_df([{"txn_amount": 105.0}])   # 5% delta, within partial_tolerance=10%
        result = reconcile_transactions(a, b, date_window_days=3, partial_tolerance=0.10)
        assert len(result) >= 1
        # Should not be "Missing" — partial match found
        assert result.iloc[0]["match_status"] != "Missing"


# ---------------------------------------------------------------------------
# Exception classification output columns
# ---------------------------------------------------------------------------

class TestExceptionClassification:
    def test_required_columns_present(self):
        a = _make_df([{"txn_amount": 100.0}])
        b = _make_df([{"txn_amount": 100.0}])
        result = reconcile_transactions(a, b)
        for col in ("exception_code", "exception_label", "exception_reason",
                    "suggested_action", "confidence_score", "severity"):
            assert col in result.columns, f"Missing column: {col}"

    def test_matched_rows_have_confidence_gt_zero(self):
        a = _make_df([{"txn_amount": 100.0}])
        b = _make_df([{"txn_amount": 100.0}])
        result = reconcile_transactions(a, b)
        matched = result[result["exception_code"] == "matched"]
        if not matched.empty:
            assert (matched["confidence_score"] > 0).all()

    def test_no_duplicate_output_columns(self):
        a = _make_df([{"txn_amount": 100.0}])
        b = _make_df([{"txn_amount": 100.0}])
        result = reconcile_transactions(a, b)
        assert len(result.columns) == len(set(result.columns)), "Duplicate column names in output"
