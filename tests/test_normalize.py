"""
Tests for recon_engine.normalize — column alias mapping and transaction normalization.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from recon_engine.normalize import (
    TRANSACTION_ALIASES,
    apply_column_aliases,
    normalize_transactions,
)


# ---------------------------------------------------------------------------
# apply_column_aliases
# ---------------------------------------------------------------------------

class TestColumnAliases:
    def test_variant_names_mapped_to_canonical(self):
        df = pd.DataFrame({
            "PostDate": ["2024-01-15", "2024-01-29"],
            "Charge": [285.00, 320.00],
            "Memo": ["A", "B"],
            "Ref": ["R-1", "R-2"],
        })
        result = apply_column_aliases(df, TRANSACTION_ALIASES)
        assert "txn_date" in result.columns
        assert "txn_amount" in result.columns
        assert "description" in result.columns
        assert "reference" in result.columns

    def test_canonical_names_pass_through(self):
        df = pd.DataFrame({
            "txn_date": ["2024-01-15"],
            "txn_amount": [100.0],
            "source_file": ["test.csv"],
        })
        result = apply_column_aliases(df, TRANSACTION_ALIASES)
        assert "txn_date" in result.columns
        assert "txn_amount" in result.columns

    def test_unknown_columns_preserved(self):
        df = pd.DataFrame({
            "txn_date": ["2024-01-15"],
            "txn_amount": [100.0],
            "custom_field": ["x"],
        })
        result = apply_column_aliases(df, TRANSACTION_ALIASES)
        assert "custom_field" in result.columns

    def test_aliases_contain_no_duplicates(self):
        for canonical, alias_list in TRANSACTION_ALIASES.items():
            seen = set()
            for alias in alias_list:
                normalized = alias.lower().strip()
                assert normalized not in seen, (
                    f"Duplicate alias '{alias}' in {canonical} list"
                )
                seen.add(normalized)


# ---------------------------------------------------------------------------
# normalize_transactions
# ---------------------------------------------------------------------------

class TestNormalizeTransactions:
    def _minimal_df(self, n=2):
        return pd.DataFrame({
            "txn_date": ["2024-01-15", "2024-01-29"][:n],
            "txn_amount": [100.0, 200.0][:n],
            "source_file": ["test.csv"] * n,
        })

    def test_returns_dataframe(self):
        result = normalize_transactions(self._minimal_df())
        assert isinstance(result, pd.DataFrame)

    def test_txn_date_is_datetime(self):
        result = normalize_transactions(self._minimal_df())
        assert pd.api.types.is_datetime64_any_dtype(result["txn_date"])

    def test_txn_amount_is_float(self):
        result = normalize_transactions(self._minimal_df())
        assert pd.api.types.is_float_dtype(result["txn_amount"])

    def test_row_count_preserved(self):
        df = self._minimal_df(2)
        result = normalize_transactions(df)
        assert len(result) == 2

    def test_variant_columns_normalized(self):
        df = pd.DataFrame({
            "PostDate": ["01/15/2024", "01/29/2024", "02/12/2024"],
            "Charge": [285.00, 320.00, 295.00],
            "source_file": ["t.csv"] * 3,
        })
        result = normalize_transactions(apply_column_aliases(df, TRANSACTION_ALIASES))
        assert "txn_date" in result.columns
        assert "txn_amount" in result.columns
        assert len(result) == 3

    def test_row_id_assigned(self):
        result = normalize_transactions(self._minimal_df())
        assert "row_id" in result.columns
        assert result["row_id"].notna().all()
