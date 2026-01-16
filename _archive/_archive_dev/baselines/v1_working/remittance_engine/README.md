# Payroll → Benefits/Retirement → Bank Reconciliation

**Operational tool that replaces manual Excel reconciliation work for benefit plan contribution tracing.**

## What This Tool Is

A specialized tool that:
- Reconciles employee contributions from payroll to bank deposits
- Tests timeliness compliance (DOL 29 CFR § 2510.3-102)
- Generates audit-ready evidence packs
- Replaces 20-40 hours of manual Excel work with 2-4 hours of automated processing

## What This Tool Is NOT

**NOT a general reconciliation platform** - Does not handle accounts payable, accounts receivable, or general ledger reconciliation. Focused solely on payroll-to-benefits-to-bank flow.

**NOT a payroll system** - Does not process payroll or calculate contributions. Reads payroll exports only.

**NOT a recordkeeping system** - Does not post contributions to participant accounts or manage plan administration. Validates recordkeeper data only (optional).

**NOT a bank reconciliation tool** - Does not reconcile bank statements to general ledger or handle cash management. Focused on contribution deposits only.

**NOT a data warehouse or ETL platform** - No real-time integration, no database storage. Batch processing of CSV exports only.

**NOT a compliance monitoring system** - Does not monitor ongoing compliance or send alerts. Generates point-in-time analysis only.

**This is a specialized operational tool that replaces manual Excel reconciliation work for benefit plan contribution tracing. Nothing more, nothing less.**

---

## Quick Start

### Command Line Usage

```bash
# Basic usage (payroll + bank)
python run_recon.py payroll.csv bank.csv

# With optional recordkeeper file
python run_recon.py payroll.csv bank.csv recordkeeper.csv

# Custom late threshold (default: 3 business days)
python run_recon.py payroll.csv bank.csv --late-threshold 5

# Specify output directory
python run_recon.py payroll.csv bank.csv --output-dir ./reports
```

### Required Input Files

**Payroll CSV:**
- `employee_id` (or employee number)
- `pay_date`
- `deferral_amount` (or 401k amount)

**Bank/Trust CSV:**
- `deposit_id` (or transaction reference)
- `deposit_date`
- `deposit_amount`

**Optional - Recordkeeper CSV:**
- Participant-level contribution postings (for v1.1)

The tool handles different column names, date formats (MM/DD/YYYY, YYYY-MM-DD, etc.), and numeric formatting automatically.

### Output Files

Four CSV files are generated:

1. **remittance_schedule.csv** - Complete reconciliation by pay period
2. **timeliness_report.csv** - Late deposits only
3. **exception_log.csv** - All exceptions (Partial/Missing matches)
4. **evidence_index.csv** - Source document inventory

---

## Exception Types Detected

**Late Deposits:** Deposit made more than 3 business days after pay date (configurable). Calculates exact business days late. Flags for DOL compliance testing.

**Missing Deposits:** Payroll shows contributions but no matching deposit found. Identifies unremitted contributions.

**Amount Mismatches:** Deposit amount doesn't match payroll total. Calculates variance. Flags as "Partial Match" if within 10%, "Missing" if greater.

**Missing Employee Contributions:** Individual employee deferrals not found in deposits. Identifies specific employees and amounts.

**Data Quality Issues:** Unparseable dates or amounts, missing required fields, duplicate records.

---

## Requirements

- Python 3.7+
- pandas
- python-dateutil
- numpy

## Installation

```bash
pip install pandas python-dateutil numpy
```

---

## Regulatory Context

This tool addresses requirements from:
- **AICPA EBPAQC**: Timeliness of remittances testing
- **DOL EBSA**: Timely remittance of participant contributions (29 CFR § 2510.3-102)
- **PCAOB**: Audit evidence requirements for benefit plan audits

---

## Design Principles

1. **Correctness**: Robust date/numeric parsing, validated business logic
2. **Transparency**: Clear match logic, confidence scores, source file tracking
3. **Audit-Ready**: Regulatory-grade outputs with evidence references
4. **No Over-Engineering**: Focused on compliance use case, not general data science

---

## Error Handling

The tool provides warnings for:
- Unparseable dates or amounts
- Missing required columns
- Data quality issues
- No matching deposits found

All warnings are logged but processing continues where possible.

---

## License

Internal use for compliance and audit purposes.
