# Remittance Engine Package Overview

## Package Structure

```
remittance_engine/
├── __init__.py          # Package initialization
├── ingest.py            # Data ingestion with column mapping
├── normalize.py         # Canonical table conversion
├── reconcile.py         # Payroll-to-deposit matching
├── rules.py             # Business rules (timeliness, matching)
├── outputs.py           # Report generation (4 CSV outputs)
├── run_case.py          # Case orchestration
└── README.md            # Documentation

sample_case/
├── inputs/
│   ├── payroll/
│   │   └── payroll_q1_2024.csv
│   └── trust/
│       └── trust_statements_q1_2024.csv
└── outputs/
    ├── remittance_schedule.csv
    ├── timeliness_report.csv
    ├── exception_log.csv
    └── evidence_index.csv
```

## Module Responsibilities

### ingest.py
- Loads CSV files with flexible column mapping
- Robust date parsing (handles multiple formats)
- Standardizes numeric fields
- Supports multiple input files

### normalize.py
- Converts to canonical tables:
  - `payroll_normalized`: employee_id, pay_date, deferral_amount, source_file
  - `trust_normalized`: deposit_id, deposit_date, deposit_amount, source_file
- Validates data quality
- Removes invalid records

### reconcile.py
- Aggregates payroll by pay_date
- Matches deposits by amount and proximity
- Match types: Exact, Partial, Missing
- Returns comprehensive remittance table

### rules.py
- Business-day calculation (excludes weekends)
- Late-deposit rule (configurable threshold)
- Match confidence scoring (0.0-1.0)
- Exception type classification

### outputs.py
Generates four audit-ready reports:
1. **remittance_schedule.csv**: Complete reconciliation
2. **timeliness_report.csv**: Late deposits only
3. **exception_log.csv**: All exceptions
4. **evidence_index.csv**: Source document inventory

### run_case.py
- Orchestrates full workflow
- Accepts case folder structure
- Returns summary statistics

## Sample Case Results

The sample case demonstrates:
- 4 pay periods analyzed
- 2 exceptions found (1 late deposit, 1 missing deposit)
- $204.00 variance identified
- All outputs generated successfully

## Usage Example

```python
from remittance_engine.run_case import run_case

results = run_case(
    case_folder='sample_case',
    late_threshold_days=3
)
```

## Key Features

✅ **Robust Data Handling**: Flexible column mapping, robust date parsing  
✅ **Audit-Ready Outputs**: Regulatory-grade reports with evidence references  
✅ **Transparency**: Clear match logic, confidence scores, source tracking  
✅ **Correctness**: Validated business logic, error handling  
✅ **No Over-Engineering**: Focused on compliance use case

## Regulatory Compliance

Addresses requirements from:
- AICPA EBPAQC: Timeliness of remittances testing
- DOL EBSA: 29 CFR § 2510.3-102 (timely remittance)
- PCAOB: Audit evidence requirements
