"""
Reconciliation module - Matches payroll to deposits.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
from .rules import business_days_between, is_late_deposit, calculate_match_confidence, get_exception_type
import warnings


def calculate_review_fields(match_confidence: float,
                           exception_type: str,
                           late_flag: str,
                           deposit_total: Optional[float]) -> Tuple[str, str]:
    """
    Calculate review_required and review_reason for audit triage.
    Accumulates multiple reasons into a comma-separated string.
    
    Args:
        match_confidence: Match confidence score (0.0-1.0)
        exception_type: Exception type string
        late_flag: Late flag ('Yes', 'No', or None)
        deposit_total: Deposit total amount (or None/NaN if missing)
    
    Returns:
        Tuple of (review_required, review_reason)
    """
    reasons = []
    
    # Check each condition independently and accumulate reasons
    # 1. Low confidence match
    if match_confidence is not None and match_confidence < 0.90:
        reasons.append("Low confidence match")
    
    # 2. Late deposit
    if late_flag == "Yes":
        reasons.append("Late deposit")
    
    # 3. Amount mismatch
    if exception_type and "Mismatch" in exception_type:
        reasons.append("Amount mismatch")
    
    # 4. Missing deposit (check for None, NaN, or zero)
    import pandas as pd
    if deposit_total is None or pd.isna(deposit_total) or deposit_total == 0:
        reasons.append("Missing deposit")
    
    # Determine if review required
    review_required = "YES" if (match_confidence is not None and match_confidence < 0.90) or (exception_type != "None") else "NO"
    
    # Build review reason - comma-separated string of all applicable reasons
    review_reason = ", ".join(reasons) if reasons else ""
    
    return review_required, review_reason


def aggregate_payroll_by_date(payroll_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate payroll data by pay_date.
    
    Args:
        payroll_df: Normalized payroll DataFrame
    
    Returns:
        Aggregated DataFrame with pay_date and payroll_total
    """
    agg = payroll_df.groupby('pay_date').agg({
        'deferral_amount': 'sum',
        'source_file': lambda x: ', '.join(x.unique())
    }).reset_index()
    
    agg.columns = ['pay_date', 'payroll_total', 'payroll_source_files']
    agg = agg.sort_values('pay_date')
    
    return agg


def find_matching_deposit(payroll_total: float,
                         pay_date: pd.Timestamp,
                         deposits_df: pd.DataFrame,
                         tolerance: float = 0.01) -> Tuple[Optional[pd.Timestamp], Optional[float], str, float]:
    """
    Find the closest subsequent deposit that matches the payroll total.
    
    Args:
        payroll_total: Total payroll amount
        pay_date: Payroll date
        deposits_df: Normalized deposits DataFrame
        tolerance: Tolerance for exact match
    
    Returns:
        Tuple of (deposit_date, deposit_amount, match_status, confidence_score)
    """
    # Filter deposits that occur on or after pay_date
    subsequent_deposits = deposits_df[deposits_df['deposit_date'] >= pay_date].copy()
    
    if subsequent_deposits.empty:
        return None, None, 'Missing', 0.0
    
    # Calculate match confidence for each deposit
    subsequent_deposits['match_status'] = subsequent_deposits['deposit_amount'].apply(
        lambda x: calculate_match_confidence(payroll_total, x, tolerance)[0]
    )
    subsequent_deposits['confidence'] = subsequent_deposits['deposit_amount'].apply(
        lambda x: calculate_match_confidence(payroll_total, x, tolerance)[1]
    )
    
    # Calculate absolute difference for ranking
    subsequent_deposits['amount_diff'] = abs(subsequent_deposits['deposit_amount'] - payroll_total)
    
    # Prioritize: Exact matches first, then by confidence, then by proximity
    subsequent_deposits['priority'] = (
        (subsequent_deposits['match_status'] == 'Exact').astype(int) * 1000 +
        subsequent_deposits['confidence'] * 100 +
        (1.0 / (1.0 + subsequent_deposits['amount_diff'] / payroll_total)) * 10
    )
    
    # Get best match
    best_match_idx = subsequent_deposits['priority'].idxmax()
    best_match = subsequent_deposits.loc[best_match_idx]
    
    deposit_date = best_match['deposit_date']
    deposit_amount = best_match['deposit_amount']
    match_status = best_match['match_status']
    confidence = best_match['confidence']
    
    return deposit_date, deposit_amount, match_status, confidence


def reconcile_payroll_to_deposits(payroll_df: pd.DataFrame,
                                  deposits_df: pd.DataFrame,
                                  late_threshold_days: int = 3) -> pd.DataFrame:
    """
    Reconcile payroll contributions to trust deposits.
    
    Args:
        payroll_df: Normalized payroll DataFrame
        deposits_df: Normalized deposits DataFrame
        late_threshold_days: Business days threshold for late deposits
    
    Returns:
        Remittance schedule DataFrame
    """
    # Aggregate payroll by date
    payroll_agg = aggregate_payroll_by_date(payroll_df)
    
    # Sort deposits by date
    deposits_df = deposits_df.sort_values('deposit_date').copy()
    
    # Build remittance schedule
    remittance_rows = []
    
    for _, payroll_row in payroll_agg.iterrows():
        pay_date = payroll_row['pay_date']
        payroll_total = payroll_row['payroll_total']
        payroll_source_files = payroll_row['payroll_source_files']
        
        # Find matching deposit
        deposit_date, deposit_amount, match_status, confidence = find_matching_deposit(
            payroll_total, pay_date, deposits_df
        )
        
        # Calculate days to deposit
        days_to_deposit = business_days_between(pay_date, deposit_date) if deposit_date else None
        
        # Determine late flag
        late_flag = is_late_deposit(pay_date, deposit_date, late_threshold_days) if deposit_date else None
        
        # Get exception type
        exception_type = get_exception_type(match_status, late_flag)
        
        # Get deposit source file if matched
        deposit_source_file = None
        if deposit_date and deposit_amount:
            matching_deposits = deposits_df[
                (deposits_df['deposit_date'] == deposit_date) &
                (deposits_df['deposit_amount'] == deposit_amount)
            ]
            if not matching_deposits.empty:
                deposit_source_file = ', '.join(matching_deposits['source_file'].unique())
        
        # Calculate review fields
        late_flag_str = 'Yes' if late_flag else 'No' if late_flag is False else None
        deposit_total_value = round(deposit_amount, 2) if deposit_amount else None
        review_required, review_reason = calculate_review_fields(
            confidence,
            exception_type,
            late_flag_str,
            deposit_total_value
        )
        
        # Build remittance row
        remittance_row = {
            'pay_date': pay_date,
            'payroll_total': round(payroll_total, 2),
            'deposit_total': deposit_total_value,
            'matched_deposit_date': deposit_date,
            'days_to_deposit': days_to_deposit,
            'match_status': match_status,
            'match_confidence': round(confidence, 3),
            'late_flag': late_flag_str,
            'exception_type': exception_type,
            'review_required': review_required,
            'review_reason': review_reason,
            'payroll_source_files': payroll_source_files,
            'deposit_source_files': deposit_source_file
        }
        remittance_rows.append(remittance_row)
    
    remittance_df = pd.DataFrame(remittance_rows)
    
    return remittance_df
