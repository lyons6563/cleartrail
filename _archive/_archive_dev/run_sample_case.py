#!/usr/bin/env python3
"""
Sample case runner - Demonstrates remittance engine usage.
"""

from remittance_engine.run_case import run_case

if __name__ == '__main__':
    print("=" * 60)
    print("Remittance Engine - Sample Case")
    print("=" * 60)
    print()
    
    # Run the sample case
    results = run_case(
        case_folder='sample_case',
        late_threshold_days=3
    )
    
    print()
    print("=" * 60)
    print("Analysis Complete")
    print("=" * 60)
    print()
    print("Review outputs in: sample_case/outputs/")
