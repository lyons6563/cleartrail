"""
Test/demo script for column alias functionality.

This demonstrates that payroll columns with variant names (Emp_ID, Pay_Date, Deferred_Amount)
are automatically mapped to canonical names before validation.
"""

import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from remittance_engine.ingest import ingest_payroll_file
from remittance_engine.normalize import normalize_payroll, apply_column_aliases, COLUMN_ALIASES


def test_payroll_aliases():
    """Test that payroll columns with variant names are correctly mapped."""
    
    # Create test data with variant column names
    test_data = pd.DataFrame({
        'Emp_ID': ['E1001', 'E1002', 'E1003'],
        'Pay_Date': ['01/15/2024', '01/29/2024', '02/12/2024'],
        'Deferred_Amount': [285.00, 320.00, 295.00],
        'Other_Column': ['A', 'B', 'C']
    })
    
    print("Original columns:", list(test_data.columns))
    print()
    
    # Apply aliases
    payroll_aliases = {
        'employee_id': COLUMN_ALIASES['payroll']['employee_id'],
        'pay_date': COLUMN_ALIASES['payroll']['pay_date'],
        'deferral_amount': COLUMN_ALIASES['payroll']['deferral_amount']
    }
    
    df_after_aliases = apply_column_aliases(test_data, payroll_aliases)
    print("Columns after alias mapping:", list(df_after_aliases.columns))
    print()
    
    # Verify mapping worked
    assert 'employee_id' in df_after_aliases.columns, "employee_id should be mapped from Emp_ID"
    assert 'pay_date' in df_after_aliases.columns, "pay_date should be mapped from Pay_Date"
    assert 'deferral_amount' in df_after_aliases.columns, "deferral_amount should be mapped from Deferred_Amount"
    assert 'Emp_ID' not in df_after_aliases.columns, "Emp_ID should be renamed"
    assert 'Pay_Date' not in df_after_aliases.columns, "Pay_Date should be renamed"
    assert 'Deferred_Amount' not in df_after_aliases.columns, "Deferred_Amount should be renamed"
    
    print("[PASS] Alias mapping successful!")
    print()
    
    # Now test full normalization (add source_file which is required)
    df_after_aliases['source_file'] = 'test.csv'
    
    # Normalize - this should work without errors
    normalized = normalize_payroll(df_after_aliases)
    
    print("Normalized columns:", list(normalized.columns))
    print("Normalized data shape:", normalized.shape)
    print()
    print("Sample normalized data:")
    print(normalized.head())
    print()
    
    # Verify normalization worked
    assert 'employee_id' in normalized.columns
    assert 'pay_date' in normalized.columns
    assert 'deferral_amount' in normalized.columns
    assert len(normalized) == 3
    
    print("[PASS] Full normalization successful!")
    print()
    print("Test passed: Payroll columns Emp_ID, Pay_Date, Deferred_Amount are correctly mapped!")


def test_backward_compatibility():
    """Test that original column names still work (backward compatibility)."""
    
    # Create test data with original canonical column names
    test_data = pd.DataFrame({
        'employee_id': ['E1001', 'E1002'],
        'pay_date': ['01/15/2024', '01/29/2024'],
        'deferral_amount': [285.00, 320.00],
        'source_file': ['test1.csv', 'test2.csv']
    })
    
    print("\n" + "="*60)
    print("Testing backward compatibility with original column names")
    print("="*60)
    print("Original columns:", list(test_data.columns))
    print()
    
    # Normalize - should work without issues
    normalized = normalize_payroll(test_data)
    
    print("Normalized columns:", list(normalized.columns))
    print("Normalized data shape:", normalized.shape)
    print()
    print("Sample normalized data:")
    print(normalized.head())
    print()
    
    # Verify it still works
    assert 'employee_id' in normalized.columns
    assert 'pay_date' in normalized.columns
    assert 'deferral_amount' in normalized.columns
    assert len(normalized) == 2
    
    print("[PASS] Backward compatibility test successful!")
    print("Original column names still work correctly.")


if __name__ == '__main__':
    test_payroll_aliases()
    test_backward_compatibility()
