# Payroll → Benefits/Retirement → Bank Reconciliation
## Commercial Product Specification

---This product replaces manual Excel-based payroll contribution reconciliation with a standardized, audit-defensible reconciliation and evidence pack.

## 1. Target Customer + Buyer

**Buyer:** Payroll Manager or Controller at employers with 200-5,000 employees who sponsor 401(k) or other defined contribution plans.

**Problem:** You spend 20-40 hours per year manually reconciling employee contributions from payroll to bank deposits to recordkeeper postings. This work is required for annual plan audits, DOL compliance testing, and internal controls. It's error-prone, time-consuming, and difficult to defend when auditors ask questions.

---

## 2. The Painful Workflow Being Replaced

**Current Process:**
1. Export payroll data from your payroll system (ADP, Paychex, Workday, etc.)
2. Export bank/trust statements showing deposits
3. Export recordkeeper contribution files
4. Manually match amounts and dates across three systems in Excel
5. Calculate business days between pay dates and deposit dates
6. Flag exceptions (late deposits, missing contributions, amount mismatches)
7. Build reconciliation schedules and exception logs
8. Create evidence index for auditors

**Time Required:** 20-40 hours per engagement, repeated quarterly or annually.

**Pain Points:** Different date formats, inconsistent employee IDs, manual calculations, Excel errors, incomplete audit trails.

---

## 3. Exact Inputs Required

**Payroll Export (CSV file):**
- employee_id (or employee number)
- pay_date
- deferral_amount (or 401k amount)

**Bank/Trust Export (CSV file):**
- deposit_id (or transaction reference)
- deposit_date
- deposit_amount

**That's it.** The tool handles different column names, date formats (MM/DD/YYYY, YYYY-MM-DD, etc.), and numeric formatting automatically.

---

## 4. Exact Outputs Produced

**Four CSV files ready for Excel or audit workpapers:**

1. **remittance_schedule.csv** - Complete reconciliation by pay period showing: pay_date, payroll_total, deposit_total, matched_deposit_date, days_to_deposit, match_status, late_flag, exception_type, source file references

2. **timeliness_report.csv** - Late deposits only with days over threshold and exception classification

3. **exception_log.csv** - All exceptions (Partial/Missing matches) with variance calculations and source file references

4. **evidence_index.csv** - Complete inventory of source documents with evidence IDs, date ranges, record counts, and relevance descriptions

All outputs include source file tracking for complete audit trails.

---

## 5. Core Exceptions Detected

**Late Deposits:** Deposit made more than 3 business days after pay date (configurable). Calculates exact business days late. Flags for DOL compliance testing (29 CFR § 2510.3-102).

**Missing Deposits:** Payroll shows contributions but no matching deposit found. Identifies unremitted contributions.

**Amount Mismatches:** Deposit amount doesn't match payroll total. Calculates variance. Flags as "Partial Match" if within 10%, "Missing" if greater.

**Missing Employee Contributions:** Individual employee deferrals not found in deposits. Identifies specific employees and amounts.

**Data Quality Issues:** Unparseable dates or amounts, missing required fields, duplicate records.

---

## 6. Why Finance/Compliance Would Pay For This

**Time Savings:** Reduces 20-40 hour manual process to 2-4 hours (data export + review). 80-90% time reduction. At $150/hour: $2,700-$5,700 saved per engagement.

**Risk Reduction:** Eliminates manual calculation errors. Systematic exception detection. Consistent methodology. Reduces audit deficiency risk.

**Penalty Avoidance:** Early detection of late deposits (DOL penalties: $100/day per violation). Identifies missing contributions before audit. Prevents Form 5500 filing errors. Supports timely correction to reduce lost earnings exposure.

**Audit Efficiency:** Pre-structured evidence pack reduces auditor questions and follow-up. Faster audit completion. Lower audit fees.

**Typical Annual Value:** $5,000-$15,000 per employer (time savings + risk reduction + penalty avoidance).

---

## 7. Explicit Non-Goals

**NOT a general reconciliation platform** - Does not handle accounts payable, accounts receivable, or general ledger reconciliation. Focused solely on payroll-to-benefits-to-bank flow.

**NOT a payroll system** - Does not process payroll or calculate contributions. Reads payroll exports only.

**NOT a recordkeeping system** - Does not post contributions to participant accounts or manage plan administration. Validates recordkeeper data only.

**NOT a bank reconciliation tool** - Does not reconcile bank statements to general ledger or handle cash management. Focused on contribution deposits only.

**NOT a data warehouse or ETL platform** - No real-time integration, no database storage. Batch processing of CSV exports only.

**NOT a compliance monitoring system** - Does not monitor ongoing compliance or send alerts. Generates point-in-time analysis only.

**This is a specialized operational tool that replaces manual Excel reconciliation work for benefit plan contribution tracing. Nothing more, nothing less.**

---

*For questions or a demonstration, contact [contact information]*
