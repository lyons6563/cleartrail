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
        'severity',
        'recommended_action',
        'payroll_source_files',
        'deposit_source_files',
        'payroll_component_ids',
        'deposit_component_ids',
        'unmatched_payroll_amount',
        'unmatched_deposit_amount',
        'principal_at_risk',
        'days_late_adjusted',
        'assumed_annual_rate',
        'lost_earnings_estimate'
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
            'deposit_source_files',
            'review_required',
            'review_reason',
            'severity',
            'recommended_action',
            'principal_at_risk',
            'days_late_adjusted',
            'assumed_annual_rate',
            'lost_earnings_estimate'
        ]
        
        exception_df = exception_df[columns]
    # Ensure review fields exist even if older schedules are used
    for col in ['review_required', 'review_reason', 'severity', 'recommended_action']:
        if col not in exception_df.columns:
            exception_df[col] = None
    
    exception_df.to_csv(output_path, index=False)


def write_audit_workpaper(remittance_df: pd.DataFrame, output_path: str):
    """
    Write audit workpaper CSV (single-sheet auditor workpaper).
    
    Args:
        remittance_df: Remittance schedule DataFrame
        output_path: Output file path
    """
    workpaper_df = remittance_df[
        remittance_df['exception_type'] != 'None'
    ].copy()
    
    if workpaper_df.empty:
        workpaper_df = pd.DataFrame(columns=[
            'pay_date',
            'exception_type',
            'late_flag',
            'days_to_deposit',
            'payroll_total',
            'deposit_total',
            'variance',
            'payroll_component_ids',
            'deposit_component_ids',
            'payroll_source_files',
            'deposit_source_files',
            'review_reason',
            'severity',
            'recommended_action'
        ])
    else:
        workpaper_df['variance'] = workpaper_df['payroll_total'] - workpaper_df['deposit_total'].fillna(0)
        workpaper_df['pay_date'] = workpaper_df['pay_date'].apply(format_date_for_output)
        workpaper_df = workpaper_df[[
            'pay_date',
            'exception_type',
            'late_flag',
            'days_to_deposit',
            'payroll_total',
            'deposit_total',
            'variance',
            'payroll_component_ids',
            'deposit_component_ids',
            'payroll_source_files',
            'deposit_source_files',
            'review_reason',
            'severity',
            'recommended_action'
        ]]
    
    workpaper_df.to_csv(output_path, index=False)


def _split_component_ids(component_ids: Optional[str]) -> list:
    """
    Split component id string into a list.
    """
    if component_ids is None or pd.isna(component_ids):
        return []
    if isinstance(component_ids, str):
        return [item.strip() for item in component_ids.split(',') if item.strip()]
    return [str(component_ids)]


def write_exception_trace_packs(remittance_df: pd.DataFrame,
                               payroll_df: pd.DataFrame,
                               deposits_df: pd.DataFrame,
                               output_dir: str):
    """
    Write exception trace packs for rows requiring review.
    """
    output_path = Path(output_dir)
    exceptions_root = output_path / 'exceptions'
    exceptions_root.mkdir(parents=True, exist_ok=True)

    review_rows = remittance_df[remittance_df['review_required'] == 'YES'].copy()
    for _, row in review_rows.iterrows():
        pay_date_str = format_date_for_output(row.get('pay_date'))
        case_dir = exceptions_root / pay_date_str
        case_dir.mkdir(parents=True, exist_ok=True)

        payroll_ids = _split_component_ids(row.get('payroll_component_ids'))
        deposit_ids = _split_component_ids(row.get('deposit_component_ids'))

        payroll_components = payroll_df[payroll_df['payroll_row_id'].isin(payroll_ids)].copy()
        deposit_components = deposits_df[deposits_df['deposit_row_id'].isin(deposit_ids)].copy()

        payroll_components.to_csv(case_dir / 'payroll_components.csv', index=False)
        deposit_components.to_csv(case_dir / 'deposit_components.csv', index=False)

        payroll_total = row.get('payroll_total')
        deposit_total = row.get('deposit_total')
        variance = None
        if pd.notna(payroll_total):
            variance = payroll_total - (deposit_total if pd.notna(deposit_total) else 0)

        days_to_deposit = row.get('days_to_deposit')
        days_late = days_to_deposit if row.get('late_flag') == 'Yes' else 0

        summary_lines = [
            f"Pay date: {pay_date_str}",
            f"Payroll total: {payroll_total}",
            f"Deposit total: {deposit_total}",
            f"Variance: {variance}",
            f"Exception type: {row.get('exception_type')}",
            f"Severity: {row.get('severity')}",
            f"Days late: {days_late}",
            f"Recommended action: {row.get('recommended_action')}",
            f"Payroll source files: {row.get('payroll_source_files')}",
            f"Deposit source files: {row.get('deposit_source_files')}"
        ]
        (case_dir / 'trace_summary.txt').write_text("\n".join(summary_lines), encoding='utf-8')


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
    write_audit_workpaper(remittance_df, output_path / 'audit_workpaper.csv')
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

    write_exception_trace_packs(remittance_df, payroll_df, deposits_df, output_dir)
    write_correction_packet_index(remittance_df, output_path / 'correction_packet_index.csv')


def write_correction_packet_index(remittance_df: pd.DataFrame, output_path: str):
    """
    Write correction packet index for CRITICAL exceptions.
    """
    critical_df = remittance_df[remittance_df['severity'] == 'CRITICAL'].copy()

    columns = [
        'case_id',
        'pay_date',
        'exception_type',
        'severity',
        'principal_at_risk',
        'days_late_adjusted',
        'lost_earnings_estimate',
        'regulatory_basis',
        'correction_required',
        'documents_needed',
        'next_action_owner',
        'generated_on'
    ]

    if critical_df.empty:
        pd.DataFrame(columns=columns).to_csv(output_path, index=False)
        return

    def _regulatory_language(exception_type: str) -> str:
        if exception_type == 'Late Deposit':
            return 'Policy: Deposits should be completed as soon as administratively feasible.'
        if exception_type == 'Amount Mismatch':
            return 'Policy: Deposits should be completed in full; partial deposits require correction and restoration.'
        if exception_type == 'Missing Deposit':
            return 'Policy: Missing deposits require correction and documentation.'
        return 'Policy basis requires review.'

    def _documents_needed(exception_type: str) -> str:
        if exception_type == 'Late Deposit':
            return 'Source register, deposit statement, reconciliation confirmation'
        if exception_type == 'Amount Mismatch':
            return 'Source register, deposit detail, reconciliation worksheet'
        if exception_type == 'Missing Deposit':
            return 'Source register, deposit statement, deposit confirmation or proof of correction'
        return 'Source documents'

    def _correction_required(exception_type: str) -> str:
        return 'Yes' if exception_type in ['Late Deposit', 'Amount Mismatch', 'Missing Deposit'] else 'Review'

    generated_on = datetime.now().strftime('%Y-%m-%d')
    rows = []
    for idx, row in critical_df.reset_index(drop=True).iterrows():
        case_id = f"CP-{idx + 1:04d}"
        rows.append({
            'case_id': case_id,
            'pay_date': format_date_for_output(row.get('pay_date')),
            'exception_type': row.get('exception_type'),
            'severity': row.get('severity'),
            'principal_at_risk': row.get('principal_at_risk'),
            'days_late_adjusted': row.get('days_late_adjusted'),
            'lost_earnings_estimate': row.get('lost_earnings_estimate'),
            'regulatory_basis': _regulatory_language(row.get('exception_type')),
            'correction_required': _correction_required(row.get('exception_type')),
            'documents_needed': _documents_needed(row.get('exception_type')),
            'next_action_owner': 'Process Owner',
            'generated_on': generated_on
        })

    pd.DataFrame(rows, columns=columns).to_csv(output_path, index=False)