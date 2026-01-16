#!/usr/bin/env python3
"""
Timely Remittance & Completeness Engine - Module 1
Builds remittance schedule by matching payroll contributions to trust deposits.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil import parser
from dateutil.relativedelta import relativedelta
import sys
import os


def parse_date_robust(date_str):
    """Parse date string robustly, handling various formats."""
    if pd.isna(date_str):
        return None
    try:
        return parser.parse(str(date_str), dayfirst=False, yearfirst=True)
    except (ValueError, TypeError):
        try:
            return pd.to_datetime(date_str)
        except:
            raise ValueError(f"Unable to parse date: {date_str}")


def business_days_between(start_date, end_date):
    """Calculate business days between two dates (exclusive of end_date)."""
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


def find_matching_deposit(payroll_total, pay_date, deposits_df, tolerance=0.01):
    """
    Find the closest subsequent deposit that matches the payroll total.
    Returns (deposit_date, deposit_amount, match_status, days_to_deposit)
    """
    # Filter deposits that occur on or after pay_date
    subsequent_deposits = deposits_df[deposits_df['deposit_date'] >= pay_date].copy()
    
    if subsequent_deposits.empty:
        return None, None, 'Missing', None
    
    # Calculate absolute difference from payroll total
    subsequent_deposits['amount_diff'] = abs(subsequent_deposits['deposit_amount'] - payroll_total)
    
    # Find closest match by amount
    closest_idx = subsequent_deposits['amount_diff'].idxmin()
    closest_deposit = subsequent_deposits.loc[closest_idx]
    
    deposit_amount = closest_deposit['deposit_amount']
    deposit_date = closest_deposit['deposit_date']
    amount_diff = closest_deposit['amount_diff']
    
    # Determine match status
    if amount_diff <= tolerance:
        match_status = 'Matched'
    elif amount_diff <= payroll_total * 0.10:  # Within 10% considered partial
        match_status = 'Partial'
    else:
        match_status = 'Missing'
    
    days_to_deposit = business_days_between(pay_date, deposit_date)
    
    return deposit_date, deposit_amount, match_status, days_to_deposit


def build_remittance_schedule(payroll_file, trust_file, late_threshold_days=3):
    """
    Build remittance schedule from payroll and trust deposit files.
    
    Args:
        payroll_file: Path to payroll CSV
        trust_file: Path to trust deposit CSV
        late_threshold_days: Number of business days before deposit is considered late
    
    Returns:
        tuple: (remittance_schedule_df, exception_log_df)
    """
    
    # Read input files
    try:
        payroll_df = pd.read_csv(payroll_file)
        trust_df = pd.read_csv(trust_file)
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading files: {e}")
        sys.exit(1)
    
    # Validate required columns
    required_payroll_cols = ['employee_id', 'pay_date', 'deferral_amount']
    required_trust_cols = ['deposit_id', 'deposit_date', 'deposit_amount']
    
    for col in required_payroll_cols:
        if col not in payroll_df.columns:
            raise ValueError(f"Missing required column in payroll file: {col}")
    
    for col in required_trust_cols:
        if col not in trust_df.columns:
            raise ValueError(f"Missing required column in trust file: {col}")
    
    # Parse dates
    payroll_df['pay_date'] = payroll_df['pay_date'].apply(parse_date_robust)
    trust_df['deposit_date'] = trust_df['deposit_date'].apply(parse_date_robust)
    
    # Convert amounts to numeric
    payroll_df['deferral_amount'] = pd.to_numeric(payroll_df['deferral_amount'], errors='coerce')
    trust_df['deposit_amount'] = pd.to_numeric(trust_df['deposit_amount'], errors='coerce')
    
    # Aggregate payroll by pay_date
    payroll_agg = payroll_df.groupby('pay_date')['deferral_amount'].sum().reset_index()
    payroll_agg.columns = ['pay_date', 'payroll_total']
    payroll_agg = payroll_agg.sort_values('pay_date')
    
    # Sort deposits by date
    trust_df = trust_df.sort_values('deposit_date')
    
    # Build remittance schedule
    remittance_rows = []
    exception_rows = []
    
    for _, payroll_row in payroll_agg.iterrows():
        pay_date = payroll_row['pay_date']
        payroll_total = payroll_row['payroll_total']
        
        # Find matching deposit
        deposit_date, deposit_amount, match_status, days_to_deposit = find_matching_deposit(
            payroll_total, pay_date, trust_df
        )
        
        # Determine late flag
        late_flag = 'Yes' if (days_to_deposit is not None and days_to_deposit > late_threshold_days) else 'No'
        
        # Build remittance row
        remittance_row = {
            'pay_date': pay_date.strftime('%Y-%m-%d') if pay_date else '',
            'payroll_total': round(payroll_total, 2),
            'matched_deposit_date': deposit_date.strftime('%Y-%m-%d') if deposit_date else '',
            'matched_deposit_amount': round(deposit_amount, 2) if deposit_amount else '',
            'days_to_deposit': days_to_deposit if days_to_deposit is not None else '',
            'match_status': match_status,
            'late_flag': late_flag
        }
        remittance_rows.append(remittance_row)
        
        # Add to exception log if Partial or Missing
        if match_status in ['Partial', 'Missing']:
            exception_row = {
                'pay_date': pay_date.strftime('%Y-%m-%d') if pay_date else '',
                'payroll_total': round(payroll_total, 2),
                'matched_deposit_date': deposit_date.strftime('%Y-%m-%d') if deposit_date else '',
                'matched_deposit_amount': round(deposit_amount, 2) if deposit_amount else '',
                'variance': round(payroll_total - deposit_amount, 2) if deposit_amount else round(payroll_total, 2),
                'match_status': match_status,
                'days_to_deposit': days_to_deposit if days_to_deposit is not None else '',
                'late_flag': late_flag
            }
            exception_rows.append(exception_row)
    
    # Create DataFrames
    remittance_schedule_df = pd.DataFrame(remittance_rows)
    exception_log_df = pd.DataFrame(exception_rows)
    
    return remittance_schedule_df, exception_log_df


def main():
    """Main execution function."""
    
    # Configuration
    payroll_file = 'payroll.csv'
    trust_file = 'trust.csv'
    output_schedule = 'remittance_schedule.csv'
    output_exceptions = 'exception_log.csv'
    late_threshold_days = 3  # Configurable threshold
    
    # Check if input files exist
    if not os.path.exists(payroll_file):
        print(f"Error: Payroll file not found: {payroll_file}")
        sys.exit(1)
    
    if not os.path.exists(trust_file):
        print(f"Error: Trust file not found: {trust_file}")
        sys.exit(1)
    
    print(f"Building remittance schedule...")
    print(f"  Payroll file: {payroll_file}")
    print(f"  Trust file: {trust_file}")
    print(f"  Late threshold: {late_threshold_days} business days")
    print()
    
    try:
        # Build remittance schedule
        remittance_df, exception_df = build_remittance_schedule(
            payroll_file, trust_file, late_threshold_days
        )
        
        # Write outputs
        remittance_df.to_csv(output_schedule, index=False)
        print(f"[OK] Remittance schedule written to: {output_schedule}")
        print(f"  Total pay periods: {len(remittance_df)}")
        
        if len(exception_df) > 0:
            exception_df.to_csv(output_exceptions, index=False)
            print(f"[OK] Exception log written to: {output_exceptions}")
            print(f"  Exceptions found: {len(exception_df)}")
            
            # Summary statistics
            missing_count = len(exception_df[exception_df['match_status'] == 'Missing'])
            partial_count = len(exception_df[exception_df['match_status'] == 'Partial'])
            late_count = len(exception_df[exception_df['late_flag'] == 'Yes'])
            
            print(f"    - Missing: {missing_count}")
            print(f"    - Partial: {partial_count}")
            print(f"    - Late: {late_count}")
        else:
            print(f"[OK] No exceptions found - all matches successful")
        
        print()
        print("Remittance Schedule Summary:")
        print(remittance_df.to_string(index=False))
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
