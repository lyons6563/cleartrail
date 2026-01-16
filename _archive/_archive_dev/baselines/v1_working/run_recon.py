#!/usr/bin/env python3
"""
Payroll → Benefits/Retirement → Bank Reconciliation
CLI Entry Point

Usage:
    python run_recon.py <payroll.csv> <bank.csv> [recordkeeper.csv]
"""

import sys
import argparse
from pathlib import Path
import pandas as pd

from remittance_engine.ingest import ingest_payroll_file, ingest_trust_file
from remittance_engine.normalize import normalize_payroll, normalize_trust
from remittance_engine.reconcile import reconcile_payroll_to_deposits
from remittance_engine.outputs import write_all_outputs


def main():
    parser = argparse.ArgumentParser(
        description='Payroll → Benefits/Retirement → Bank Reconciliation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_recon.py payroll.csv bank.csv
  python run_recon.py payroll.csv bank.csv recordkeeper.csv
  python run_recon.py payroll.csv bank.csv --late-threshold 5
        """
    )
    
    parser.add_argument('payroll_file', help='Payroll CSV file (employee_id, pay_date, deferral_amount)')
    parser.add_argument('bank_file', help='Bank/Trust CSV file (deposit_id, deposit_date, deposit_amount)')
    parser.add_argument('recordkeeper_file', nargs='?', help='Optional: Recordkeeper CSV file')
    parser.add_argument('--late-threshold', type=int, default=3,
                       help='Business days threshold for late deposits (default: 3)')
    parser.add_argument('--output-dir', type=str, default='.',
                       help='Output directory for reports (default: current directory)')
    
    args = parser.parse_args()
    
    # Validate input files
    if not Path(args.payroll_file).exists():
        print(f"Error: Payroll file not found: {args.payroll_file}")
        sys.exit(1)
    
    if not Path(args.bank_file).exists():
        print(f"Error: Bank file not found: {args.bank_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("Payroll -> Benefits/Retirement -> Bank Reconciliation")
    print("=" * 60)
    print()
    print(f"Payroll file: {args.payroll_file}")
    print(f"Bank file: {args.bank_file}")
    if args.recordkeeper_file:
        print(f"Recordkeeper file: {args.recordkeeper_file}")
    print(f"Late threshold: {args.late_threshold} business days")
    print()
    
    try:
        # Ingest files
        print("Loading files...")
        payroll_raw = ingest_payroll_file(args.payroll_file)
        trust_raw = ingest_trust_file(args.bank_file)
        
        print(f"  Payroll records: {len(payroll_raw)}")
        print(f"  Bank records: {len(trust_raw)}")
        print()
        
        # Normalize data
        print("Normalizing data...")
        payroll_normalized = normalize_payroll(payroll_raw)
        trust_normalized = normalize_trust(trust_raw)
        
        print(f"  Payroll records (normalized): {len(payroll_normalized)}")
        print(f"  Bank records (normalized): {len(trust_normalized)}")
        print()
        
        # Reconcile
        print("Reconciling payroll to deposits...")
        remittance_schedule = reconcile_payroll_to_deposits(
            payroll_normalized,
            trust_normalized,
            args.late_threshold
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
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
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
        
        if len(exceptions) > 0:
            print("[!] Exceptions detected - review exception_log.csv")
        else:
            print("[OK] No exceptions found")
        
        print()
        print("=" * 60)
        print("Analysis Complete")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
