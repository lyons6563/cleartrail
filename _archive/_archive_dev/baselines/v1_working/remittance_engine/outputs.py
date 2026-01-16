"""
Output generation module - Creates audit-ready reports.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime


def format_date_for_output(date_value) -> str:
    """Format date for CSV output."""
    if pd.isna(date_value) or date_value is None:
        return ''
    if isinstance(date_value, pd.Timestamp):
        return date_value.strftime('%Y-%m-%d')
    return str(date_value)


def write_remittance_schedule(remittance_df: pd.DataFrame, output_path: str):
    """
    Write remittance schedule CSV.
    
    Args:
        remittance_df: Remittance schedule DataFrame
        output_path: Output file path
    """
    output_df = remittance_df.copy()
    
    # Format dates
    output_df['pay_date'] = output_df['pay_date'].apply(format_date_for_output)
    output_df['matched_deposit_date'] = output_df['matched_deposit_date'].apply(format_date_for_output)
    
    # Select and order columns
    columns = [
        'pay_date',
        'payroll_total',
        'deposit_total',
        'matched_deposit_date',
        'days_to_deposit',
        'match_status',
        'match_confidence',
        'late_flag',
        'exception_type',
        'review_required',
        'review_reason',
        'payroll_source_files',
        'deposit_source_files'
    ]
    
    output_df = output_df[columns]
    output_df.to_csv(output_path, index=False)


def write_timeliness_report(remittance_df: pd.DataFrame, output_path: str):
    """
    Write timeliness report CSV.
    
    Args:
        remittance_df: Remittance schedule DataFrame
        output_path: Output file path
    """
    # Filter to only late deposits
    timeliness_df = remittance_df[remittance_df['late_flag'] == 'Yes'].copy()
    
    if timeliness_df.empty:
        # Create empty DataFrame with correct structure
        timeliness_df = pd.DataFrame(columns=[
            'pay_date',
            'payroll_total',
            'deposit_date',
            'days_to_deposit',
            'threshold_days',
            'days_over_threshold',
            'exception_type'
        ])
    else:
        timeliness_df = timeliness_df.copy()
        timeliness_df['deposit_date'] = timeliness_df['matched_deposit_date']
        timeliness_df['threshold_days'] = 3  # Default threshold
        timeliness_df['days_over_threshold'] = timeliness_df['days_to_deposit'] - 3
        
        # Format dates
        timeliness_df['pay_date'] = timeliness_df['pay_date'].apply(format_date_for_output)
        timeliness_df['deposit_date'] = timeliness_df['deposit_date'].apply(format_date_for_output)
        
        # Select columns
        columns = [
            'pay_date',
            'payroll_total',
            'deposit_date',
            'days_to_deposit',
            'threshold_days',
            'days_over_threshold',
            'exception_type'
        ]
        
        timeliness_df = timeliness_df[columns]
    
    timeliness_df.to_csv(output_path, index=False)


def write_exception_log(remittance_df: pd.DataFrame, output_path: str):
    """
    Write exception log CSV.
    
    Args:
        remittance_df: Remittance schedule DataFrame
        output_path: Output file path
    """
    # Filter to exceptions only
    exception_df = remittance_df[
        remittance_df['exception_type'] != 'None'
    ].copy()
    
    if exception_df.empty:
        # Create empty DataFrame with correct structure
        exception_df = pd.DataFrame(columns=[
            'pay_date',
            'payroll_total',
            'deposit_total',
            'variance',
            'match_status',
            'days_to_deposit',
            'late_flag',
            'exception_type',
            'payroll_source_files',
            'deposit_source_files'
        ])
    else:
        exception_df = exception_df.copy()
        
        # Calculate variance
        exception_df['variance'] = exception_df['payroll_total'] - exception_df['deposit_total'].fillna(0)
        
        # Format dates
        exception_df['pay_date'] = exception_df['pay_date'].apply(format_date_for_output)
        exception_df['matched_deposit_date'] = exception_df['matched_deposit_date'].apply(format_date_for_output)
        
        # Select columns
        columns = [
            'pay_date',
            'payroll_total',
            'deposit_total',
            'variance',
            'match_status',
            'days_to_deposit',
            'late_flag',
            'exception_type',
            'payroll_source_files',
            'deposit_source_files'
        ]
        
        exception_df = exception_df[columns]
    
    exception_df.to_csv(output_path, index=False)


def write_evidence_index(payroll_df: pd.DataFrame,
                        deposits_df: pd.DataFrame,
                        remittance_df: pd.DataFrame,
                        output_path: str,
                        trust_noise_df: Optional[pd.DataFrame] = None):
    """
    Write evidence index CSV.
    
    Args:
        payroll_df: Normalized payroll DataFrame
        deposits_df: Normalized deposits DataFrame
        remittance_df: Remittance schedule DataFrame
        output_path: Output file path
    """
    evidence_rows = []
    
    # Add payroll source files
    payroll_files = payroll_df['source_file'].unique()
    for file_name in payroll_files:
        file_data = payroll_df[payroll_df['source_file'] == file_name]
        evidence_rows.append({
            'evidence_id': f'PAY-{len(evidence_rows) + 1:03d}',
            'document_name': file_name,
            'document_type': 'Payroll Export',
            'source': 'Payroll System',
            'date_range': f"{file_data['pay_date'].min().strftime('%Y-%m-%d')} to {file_data['pay_date'].max().strftime('%Y-%m-%d')}",
            'record_count': len(file_data),
            'total_amount': round(file_data['deferral_amount'].sum(), 2),
            'rows_kept': None,
            'rows_excluded': None,
            'relevance': 'Primary source for contribution calculations'
        })
    
    # Add deposit source files
    kept_counts = {}
    excluded_counts = {}
    if deposits_df is not None and hasattr(deposits_df, 'attrs'):
        summary = deposits_df.attrs.get('trust_filter_summary', {})
        kept_counts = summary.get('kept_counts', {})
        excluded_counts = summary.get('excluded_counts', {})

    deposit_files = deposits_df['source_file'].unique()
    for file_name in deposit_files:
        file_data = deposits_df[deposits_df['source_file'] == file_name]
        rows_kept = kept_counts.get(file_name, len(file_data))
        rows_excluded = excluded_counts.get(file_name, 0)
        evidence_rows.append({
            'evidence_id': f'DEP-{len(evidence_rows) + 1:03d}',
            'document_name': file_name,
            'document_type': 'Bank/Trust Statement',
            'source': 'Bank/Custodian',
            'date_range': f"{file_data['deposit_date'].min().strftime('%Y-%m-%d')} to {file_data['deposit_date'].max().strftime('%Y-%m-%d')}",
            'record_count': len(file_data),
            'total_amount': round(file_data['deposit_amount'].sum(), 2),
            'rows_kept': rows_kept,
            'rows_excluded': rows_excluded,
            'relevance': 'Verification of deposit timing and amounts'
        })
    
    # Add remittance schedule
    evidence_rows.append({
        'evidence_id': f'REM-{len(evidence_rows) + 1:03d}',
        'document_name': 'remittance_schedule.csv',
        'document_type': 'Reconciliation Report',
        'source': 'Remittance Engine',
        'date_range': f"{remittance_df['pay_date'].min().strftime('%Y-%m-%d')} to {remittance_df['pay_date'].max().strftime('%Y-%m-%d')}",
        'record_count': len(remittance_df),
        'total_amount': round(remittance_df['payroll_total'].sum(), 2),
        'rows_kept': None,
        'rows_excluded': None,
        'relevance': 'Reconciliation of payroll to deposits'
    })
    
    evidence_df = pd.DataFrame(evidence_rows)
    evidence_df['date_created'] = datetime.now().strftime('%Y-%m-%d')
    
    evidence_df.to_csv(output_path, index=False)


def write_all_outputs(remittance_df: pd.DataFrame,
                     payroll_df: pd.DataFrame,
                     deposits_df: pd.DataFrame,
                     output_dir: str):
    """
    Write all output files to output directory.
    
    Args:
        remittance_df: Remittance schedule DataFrame
        payroll_df: Normalized payroll DataFrame
        deposits_df: Normalized deposits DataFrame
        output_dir: Output directory path
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    write_remittance_schedule(remittance_df, output_path / 'remittance_schedule.csv')
    write_timeliness_report(remittance_df, output_path / 'timeliness_report.csv')
    write_exception_log(remittance_df, output_path / 'exception_log.csv')
    # Write trust noise log if available
    trust_noise_df = pd.DataFrame()
    if deposits_df is not None and hasattr(deposits_df, 'attrs'):
        trust_noise_df = deposits_df.attrs.get('trust_noise_log')
        if trust_noise_df is None:
            trust_noise_df = pd.DataFrame()
    trust_noise_df.to_csv(output_path / 'trust_noise_log.csv', index=False)

    write_evidence_index(
        payroll_df,
        deposits_df,
        remittance_df,
        output_path / 'evidence_index.csv',
        trust_noise_df=trust_noise_df
    )
