#!/usr/bin/env python3
"""
Source System → Deposits Reconciliation
CLI Entry Point

Usage:
    python run_recon.py <system_a.csv> <system_b.csv>
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import uuid
import json
import os
import zipfile

from recon_engine.ingest import ingest_file
from recon_engine.normalize import normalize_transactions
from recon_engine.reconcile import reconcile_transactions
from recon_engine.case_manifest import build_case_manifest, compute_sha256
from recon_engine import __version__ as engine_version


def main():
    parser = argparse.ArgumentParser(
        description='Source System → Deposits Reconciliation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_recon.py system_a.csv system_b.csv
  python run_recon.py system_a.csv system_b.csv --date-window 5
        """
    )
    
    parser.add_argument('system_a_file', help='System A CSV file')
    parser.add_argument('system_b_file', help='System B CSV file')
    parser.add_argument('--date-window', type=int, default=3,
                       help='Date proximity window in days (default: 3)')
    parser.add_argument('--output-dir', type=str, default='.',
                       help='Output directory for reports (default: current directory)')
    
    args = parser.parse_args()
    case_id = uuid.uuid4().hex
    
    # Validate input files
    if not Path(args.system_a_file).exists():
        print(f"Error: System A file not found: {args.system_a_file}")
        sys.exit(1)
    
    if not Path(args.system_b_file).exists():
        print(f"Error: System B file not found: {args.system_b_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("Source System -> Deposits Reconciliation")
    print("=" * 60)
    print()
    print(f"System A file: {args.system_a_file}")
    print(f"System B file: {args.system_b_file}")
    print(f"Date window: {args.date_window} days")
    print()
    
    try:
        # Ingest files
        print("Loading files...")
        system_a_raw = ingest_file(args.system_a_file)
        system_b_raw = ingest_file(args.system_b_file)
        
        print(f"  System A records: {len(system_a_raw)}")
        print(f"  System B records: {len(system_b_raw)}")
        print()
        
        # Normalize data
        print("Normalizing data...")
        system_a_normalized = normalize_transactions(system_a_raw)
        system_b_normalized = normalize_transactions(system_b_raw)
        
        print(f"  System A records (normalized): {len(system_a_normalized)}")
        print(f"  System B records (normalized): {len(system_b_normalized)}")
        print()
        
        # Reconcile
        print("Reconciling records...")
        remittance_schedule = reconcile_transactions(
            system_a_normalized,
            system_b_normalized,
            date_window_days=args.date_window
        )
        
        print(f"  Records analyzed: {len(remittance_schedule)}")
        
        # Count exceptions
        exceptions = remittance_schedule[remittance_schedule['exception_code'] != 'matched']
        print(f"  Exceptions found: {len(exceptions)}")
        print()
        
        # Write outputs
        print("Writing outputs...")
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        remittance_path = output_dir / "remittance.csv"
        matched_path = output_dir / "matched.csv"
        probable_path = output_dir / "probable.csv"
        summary_path = output_dir / "exception_summary.json"

        remittance_schedule.to_csv(remittance_path, index=False)
        remittance_schedule[remittance_schedule['exception_code'] == 'matched'].to_csv(matched_path, index=False)
        remittance_schedule[remittance_schedule['exception_code'] == 'probable_match'].to_csv(probable_path, index=False)
        remittance_schedule[remittance_schedule['exception_code'] != 'matched'].to_csv(output_dir / "exceptions.csv", index=False)
        exception_summary = remittance_schedule[remittance_schedule['exception_code'] != 'matched']['exception_code'].value_counts().to_dict()
        with open(summary_path, "w", encoding="utf-8") as handle:
            json.dump(exception_summary, handle, indent=2)
        
        print(f"  Output directory: {output_dir}")
        print(f"  Files created:")
        print(f"    - remittance.csv")
        print(f"    - matched.csv")
        print(f"    - probable.csv")
        print(f"    - exceptions.csv")
        print(f"    - exception_summary.json")
        print()
        
        # Summary statistics
        total_a = remittance_schedule['txn_amount_a'].fillna(0).sum()
        total_b = remittance_schedule['txn_amount_b'].fillna(0).sum()
        variance = total_a - total_b
        
        print("Summary:")
        print(f"  Total system A amount: ${total_a:,.2f}")
        print(f"  Total system B amount: ${total_b:,.2f}")
        print(f"  Variance: ${variance:,.2f}")
        print()
        
        if len(exceptions) > 0:
            print("[!] Exceptions detected - review exception_summary.json")
        else:
            print("[OK] No exceptions found")
        
        print()
        print("=" * 60)
        print("Analysis Complete")
        print("=" * 60)

        # Case package
        cases_dir = Path("cases")
        case_dir = cases_dir / f"cleartrail_case_{case_id}"
        inputs_dir = case_dir / "inputs"
        outputs_dir = case_dir / "outputs"
        inputs_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)

        input_entries = []
        for src in [args.system_a_file, args.system_b_file]:
            src_path = Path(src)
            dest_path = inputs_dir / src_path.name
            dest_path.write_bytes(src_path.read_bytes())
            input_entries.append({
                "original_filename": src_path.name,
                "saved_filename": dest_path.name,
                "rows": None,
                "columns": None,
                "detected_fields": None,
                "sha256": compute_sha256(str(dest_path)),
                "file_size_bytes": dest_path.stat().st_size
            })

        output_entries = []
        for path in [remittance_path, matched_path, probable_path, output_dir / "exceptions.csv", summary_path]:
            if not path.exists():
                continue
            dest = outputs_dir / path.name
            dest.write_bytes(path.read_bytes())
            output_entries.append({
                "filename": dest.name,
                "rows": None,
                "sha256": compute_sha256(str(dest))
            })

        normalization_info = {
            "steps": [
                "Normalize headers",
                "Detect date/amount/reference/description",
                "Standardize to canonical fields"
            ],
            "mappings": []
        }
        reconciliation_info = {
            "matching_logic": "Date-window matching with amount/reference confidence scoring.",
            "tolerances": {
                "date_window_days": args.date_window,
                "amount_tolerance": 0.01,
                "partial_tolerance": 0.10
            },
            "warnings": [],
            "assumptions": ["Systems are peer exports with independent timing."],
            "status": "complete",
            "error": None,
            "totals": {"system_a": float(total_a), "system_b": float(total_b)},
            "matched_exact": int((remittance_schedule["exception_code"] == "matched").sum()),
            "matched_fuzzy": int((remittance_schedule["exception_code"] == "probable_match").sum()),
            "unmatched_a": int((remittance_schedule["exception_code"] == "missing_in_a").sum()),
            "unmatched_b": int((remittance_schedule["exception_code"] == "missing_in_b").sum()),
            "exception_count": int((remittance_schedule["exception_code"] != "matched").sum())
        }
        manifest = build_case_manifest(
            case_id=case_id,
            input_files=input_entries,
            normalization_info=normalization_info,
            reconciliation_info=reconciliation_info,
            outputs=output_entries,
            parameters={"date_window_days": args.date_window, "amount_tolerance": 0.01},
            engine_version=engine_version
        )
        manifest_path = case_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        bundle_path = case_dir / f"cleartrail_case_{case_id}.zip"
        with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(case_dir):
                for name in files:
                    full = Path(root) / name
                    if full == bundle_path:
                        continue
                    zipf.write(full, arcname=str(full.relative_to(case_dir)))
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
