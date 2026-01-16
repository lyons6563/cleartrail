"""
Business rules module - Timeliness calculations and match scoring.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import pandas as pd


def business_days_between(start_date: datetime, end_date: datetime) -> int:
    """
    Calculate business days between two dates (exclusive of end_date).
    
    Args:
        start_date: Start date
        end_date: End date
    
    Returns:
        Number of business days
    """
    if start_date is None or end_date is None:
        return None
    
    current = start_date.date()
    end = end_date.date()
    business_days = 0
    
    while current < end:
        # Monday = 0, Sunday = 6
        if current.weekday() < 5:  # Monday through Friday
            business_days += 1
        current += timedelta(days=1)
    
    return business_days


def is_late_deposit(pay_date: datetime, 
                   deposit_date: datetime, 
                   threshold_days: int = 3) -> bool:
    """
    Determine if deposit is late based on business days threshold.
    
    Args:
        pay_date: Payroll date
        deposit_date: Deposit date
        threshold_days: Number of business days before considered late
    
    Returns:
        True if late, False otherwise
    """
    if pay_date is None or deposit_date is None:
        return None
    
    days_to_deposit = business_days_between(pay_date, deposit_date)
    
    if days_to_deposit is None:
        return None
    
    return days_to_deposit > threshold_days


def calculate_match_confidence(payroll_total: float,
                              deposit_amount: float,
                              tolerance: float = 0.01) -> Tuple[str, float]:
    """
    Calculate match confidence score and status.
    
    Args:
        payroll_total: Total payroll amount
        deposit_amount: Deposit amount
        tolerance: Tolerance for exact match (default 0.01)
    
    Returns:
        Tuple of (match_status, confidence_score)
        match_status: 'Exact', 'Partial', or 'Missing'
        confidence_score: 0.0 to 1.0
    """
    if payroll_total is None or deposit_amount is None:
        return ('Missing', 0.0)
    
    if payroll_total == 0:
        return ('Missing', 0.0)
    
    amount_diff = abs(payroll_total - deposit_amount)
    percent_diff = amount_diff / payroll_total
    
    if amount_diff <= tolerance:
        return ('Exact', 1.0)
    elif percent_diff <= 0.10:  # Within 10% considered partial
        confidence = 1.0 - (percent_diff / 0.10)  # Linear scale from 0.9 to 1.0
        return ('Partial', confidence)
    else:
        return ('Missing', 0.0)


def get_exception_type(match_status: str, late_flag: bool) -> str:
    """
    Determine exception type based on match status and late flag.
    Matches commercial spec exception categories.
    
    Args:
        match_status: Match status ('Exact', 'Partial', 'Missing')
        late_flag: Whether deposit is late
    
    Returns:
        Exception type string matching commercial spec:
        - 'Late Deposit'
        - 'Missing Deposit'
        - 'Amount Mismatch'
        - 'None'
    """
    if match_status == 'Missing':
        return 'Missing Deposit'
    elif match_status == 'Partial':
        return 'Amount Mismatch'
    elif late_flag:
        return 'Late Deposit'
    else:
        return 'None'
