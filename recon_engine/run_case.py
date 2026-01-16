"""
Case orchestration module - Runs full remittance analysis workflow.
"""

from pathlib import Path
import pandas as pd
from typing import Optional, Dict
import warnings

from .ingest import ingest_multiple_files
from .normalize import normalize_payroll, normalize_trust
from .reconcile import reconcile_payroll_to_deposits
from .outputs import write_all_outputs


def find_input_files(case_folder: str, file_type: str) -> list:
    """
    Find all CSV files in input directory.
    
    Args:
        case_folder: Case folder path
        file_type: 'payroll' or 'trust'
    
    Returns:
        List of file paths
    """
    input_dir = Path(case_folder) / 'inputs' / file_type
    
    if not input_dir.exists():
        warnings.warn(f"Input directory not found: {input_dir}")
        return []
    
    files = list(input_dir.glob('*.csv'))
    
    if not files:
        warnings.warn(f"No CSV files found in: {input_dir}")
    
    return [str(f) for f in files]


def run_case(case_folder: str,
             payroll_column_mapping: Optional[Dict[str, str]] = None,
             trust_column_mapping: Optional[Dict[str, str]] = None,
             late_threshold_days: int = 3):
    """
    Run full remittance analysis for a case.
    
    Args:
        case_folder: Path to case folder (with inputs/ and outputs/ subdirectories)
        payroll_column_mapping: Optional column mapping for payroll files
        trust_column_mapping: Optional column mapping for trust files
        late_threshold_days: Business days threshold for late deposits
    
    Returns:
        Dictionary with results summary
    """
    case_path = Path(case_folder)
    
    # Find input files
    payroll_files = find_input_files(case_folder, 'payroll')
    trust_files = find_input_files(case_folder, 'trust')
    
    if not payroll_files:
        raise ValueError(f"No payroll files found in {case_path / 'inputs' / 'payroll'}")
    
    if not trust_files:
        raise ValueError(f"No trust files found in {case_path / 'inputs' / 'trust'}")
    
    print(f"Processing case: {case_folder}")
    print(f"  Payroll files: {len(payroll_files)}")
    print(f"  Trust files: {len(trust_files)}")
    print()
    
    # Ingest files
    print("Ingesting files...")
    payroll_raw = ingest_multiple_files(payroll_files, payroll_column_mapping, 'payroll')
    trust_raw = ingest_multiple_files(trust_files, trust_column_mapping, 'trust')
    
    print(f"  Payroll records: {len(payroll_raw)}")
    print(f"  Trust records: {len(trust_raw)}")
    print()
    
    # Normalize data
    print("Normalizing data...")
    payroll_normalized = normalize_payroll(payroll_raw)
    trust_normalized = normalize_trust(trust_raw)
    
    print(f"  Payroll records (normalized): {len(payroll_normalized)}")
    print(f"  Trust records (normalized): {len(trust_normalized)}")
    print()
    
    # Reconcile
    print("Reconciling payroll to deposits...")
    remittance_schedule = reconcile_payroll_to_deposits(
        payroll_normalized,
        trust_normalized,
        late_threshold_days
    )
    
    print(f"  Pay periods analyzed: {len(remittance_schedule)}")
    
    # Count exceptions
    exceptions = remittance_schedule[remittance_schedule['exception_type'] != 'None']
    late_deposits = remittance_schedule[remittance_schedule['late_flag'] == 'Yes']
    
    print(f"  Exceptions found: {len(exceptions)}")
    print(f"  Late deposits: {len(late_deposits)}")
    print()
    
    # Write outputs
    print("Writing outputs...")
    output_dir = case_path / 'outputs'
    write_all_outputs(
        remittance_schedule,
        payroll_normalized,
        trust_normalized,
        str(output_dir)
    )
    
    print(f"  Output directory: {output_dir}")
    print(f"  Files created:")
    print(f"    - remittance_schedule.csv")
    print(f"    - timeliness_report.csv")
    print(f"    - exception_log.csv")
    print(f"    - audit_workpaper.csv")
    print(f"    - evidence_index.csv")
    print()
    
    # Summary statistics
    total_payroll = remittance_schedule['payroll_total'].sum()
    total_deposited = remittance_schedule['deposit_total'].fillna(0).sum()
    variance = total_payroll - total_deposited
    
    print("Summary:")
    print(f"  Total payroll contributions: ${total_payroll:,.2f}")
    print(f"  Total deposits: ${total_deposited:,.2f}")
    print(f"  Variance: ${variance:,.2f}")
    print()
    
    return {
        'pay_periods': len(remittance_schedule),
        'exceptions': len(exceptions),
        'late_deposits': len(late_deposits),
        'total_payroll': total_payroll,
        'total_deposited': total_deposited,
        'variance': variance
    }
