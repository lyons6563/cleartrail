"""
Test/demo script for column alias functionality.

This demonstrates that transaction columns with variant names are automatically
mapped to canonical names before validation.
"""

import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from recon_engine.ingest import ingest_file
from recon_engine.normalize import normalize_transactions, apply_column_aliases, TRANSACTION_ALIASES


def test_transaction_aliases():
    """Test that transaction columns with variant names are correctly mapped."""
    test_data = pd.DataFrame({
        'PostDate': ['01/15/2024', '01/29/2024', '02/12/2024'],
        'Charge': [285.00, 320.00, 295.00],
        'Memo': ['A', 'B', 'C'],
        'Ref': ['R-1', 'R-2', 'R-3']
    })

    print("Original columns:", list(test_data.columns))
    print()

    df_after_aliases = apply_column_aliases(test_data, TRANSACTION_ALIASES)
    print("Columns after alias mapping:", list(df_after_aliases.columns))
    print()

    assert 'txn_date' in df_after_aliases.columns, "txn_date should be mapped from PostDate"
    assert 'txn_amount' in df_after_aliases.columns, "txn_amount should be mapped from Charge"
    assert 'description' in df_after_aliases.columns, "description should be mapped from Memo"
    assert 'reference' in df_after_aliases.columns, "reference should be mapped from Ref"

    print("[PASS] Alias mapping successful!")
    print()

    df_after_aliases['source_file'] = 'test.csv'
    normalized = normalize_transactions(df_after_aliases)

    print("Normalized columns:", list(normalized.columns))
    print("Normalized data shape:", normalized.shape)
    print()
    print("Sample normalized data:")
    print(normalized.head())
    print()

    assert 'txn_date' in normalized.columns
    assert 'txn_amount' in normalized.columns
    assert len(normalized) == 3

    print("[PASS] Full normalization successful!")
    print()
    print("Test passed: Transaction columns PostDate and Charge are correctly mapped!")


def test_backward_compatibility():
    """Test that canonical column names still work (backward compatibility)."""
    test_data = pd.DataFrame({
        'txn_date': ['01/15/2024', '01/29/2024'],
        'txn_amount': [285.00, 320.00],
        'source_file': ['test1.csv', 'test2.csv']
    })

    print("\n" + "="*60)
    print("Testing backward compatibility with canonical column names")
    print("="*60)
    print("Original columns:", list(test_data.columns))
    print()

    normalized = normalize_transactions(test_data)

    print("Normalized columns:", list(normalized.columns))
    print("Normalized data shape:", normalized.shape)
    print()
    print("Sample normalized data:")
    print(normalized.head())
    print()

    assert 'txn_date' in normalized.columns
    assert 'txn_amount' in normalized.columns
    assert len(normalized) == 2

    print("[PASS] Backward compatibility test successful!")
    print("Canonical column names still work correctly.")


if __name__ == '__main__':
    test_transaction_aliases()
    test_backward_compatibility()
