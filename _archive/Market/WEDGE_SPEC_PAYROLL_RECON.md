# Payroll → Benefits/Retirement → Bank Reconciliation
## Wedge Product Specification

---

## 1. Target Customer and Buyer

**Primary Buyer:** Payroll Manager or Controller at mid-size to large employers (200-5,000 employees) with 401(k) or other defined contribution plans.

**Pain Point:** Manual reconciliation of employee contributions from payroll system to bank deposits to recordkeeper postings. This work is required for:
- Annual plan audits (CPA firms)
- DOL compliance testing (timely remittance)
- Internal controls documentation
- Vendor transition validation

**Current State:** 20-40 hours per engagement of manual Excel work, prone to errors, difficult to defend in audits.

---

## 2. Operational Workflow This Replaces

**Step 1:** Export payroll data from payroll system (ADP, Paychex, Workday, etc.)
- Extract employee deferrals by pay period
- Handle different date formats and naming conventions
- Aggregate by pay date

**Step 2:** Export bank/trust statements
- Extract deposit transactions
- Match deposit dates to pay dates
- Calculate business days between pay date and deposit date

**Step 3:** Export recordkeeper contribution files
- Extract posted contributions by participant
- Match to payroll by employee ID (often inconsistent formats)
- Identify missing postings

**Step 4:** Manual reconciliation in Excel
- Build three-way reconciliation: Payroll → Bank → Recordkeeper
- Match amounts and dates
- Flag exceptions (late deposits, missing contributions, amount mismatches)
- Calculate variances

**Step 5:** Generate audit documentation
- Create remittance schedule
- Document exceptions
- Build evidence index
- Prepare timeliness report

**Time Required:** 20-40 hours per engagement, repeated quarterly or annually.

---

## 3. Required Input Files (Minimum Viable)

**Payroll Export (CSV):**
- employee_id (or employee number)
- pay_date
- deferral_amount (or 401k amount)

**Bank/Trust Export (CSV):**
- deposit_id (or transaction reference)
- deposit_date
- deposit_amount

**Optional (for v1.1):**
- Recordkeeper contribution export (participant-level postings)

**Format Flexibility:** Handles different column names, date formats (MM/DD/YYYY, YYYY-MM-DD, etc.), and numeric formatting ($ signs, commas).

---

## 4. Exception Types Detected in v1

**Late Deposits:**
- Deposit made more than 3 business days after pay date (configurable threshold)
- Calculates exact business days late
- Flags for DOL compliance testing (29 CFR § 2510.3-102)

**Missing Deposits:**
- Payroll shows contributions but no matching deposit found
- Identifies unremitted contributions

**Amount Mismatches:**
- Deposit amount doesn't match payroll total
- Calculates variance
- Flags as "Partial Match" if within 10%, "Missing" if greater

**Missing Employee Contributions:**
- Individual employee deferrals not found in deposits
- Identifies specific employees and amounts

**Data Quality Issues:**
- Unparseable dates or amounts
- Missing required fields
- Duplicate records

---

## 5. Outputs / Deliverables Produced

**remittance_schedule.csv:**
- Pay period reconciliation table
- Columns: pay_date, payroll_total, deposit_total, matched_deposit_date, days_to_deposit, match_status, late_flag, exception_type
- Source file references for audit trail

**timeliness_report.csv:**
- Subset showing only late deposits
- Days over threshold
- Exception classification

**exception_log.csv:**
- All exceptions (Partial/Missing matches)
- Variance calculations
- Source file references

**evidence_index.csv:**
- Inventory of all source documents
- Evidence IDs (PAY-001, DEP-001, etc.)
- Date ranges, record counts, total amounts
- Relevance descriptions

**All outputs are CSV format, ready for Excel or audit workpapers.**

---

## 6. Evidence and Audit Support Features

**Source File Tracking:**
- Every output row references source files
- Evidence index provides complete document inventory
- Supports audit trail requirements

**Match Confidence Scoring:**
- 0.0 to 1.0 confidence score for each match
- Transparent matching logic
- Defensible in audit review

**Business Day Calculation:**
- Excludes weekends
- Aligns with DOL timing requirements
- Configurable threshold (default 3 business days)

**Exception Classification:**
- Standardized exception types
- Regulatory basis references (DOL, ERISA)
- Ready for audit documentation

**Date/Amount Normalization:**
- Handles inconsistent formats across systems
- Robust parsing with error handling
- Validates data quality

---

## 7. ROI Narrative

**Time Saved:**
- Reduces 20-40 hour manual process to 2-4 hours (data export + review)
- 80-90% time reduction
- At $150/hour professional rate: $2,700-$5,700 saved per engagement

**Risk Reduced:**
- Eliminates manual calculation errors
- Systematic exception detection
- Consistent methodology across engagements
- Reduces audit deficiency risk

**Penalties Avoided:**
- Early detection of late deposits (DOL penalties: $100/day per violation)
- Identifies missing contributions before audit
- Prevents Form 5500 filing errors
- Supports timely correction (reduces lost earnings exposure)

**Audit Efficiency:**
- Pre-structured evidence pack
- Reduces auditor questions and follow-up
- Faster audit completion
- Lower audit fees

**Typical Annual Value:** $5,000-$15,000 per employer (time savings + risk reduction + penalty avoidance).

---

## 8. Explicit Non-Goals (What This Is NOT)

**NOT a general reconciliation platform:**
- Does not handle accounts payable, accounts receivable, or general ledger reconciliation
- Focused solely on payroll-to-benefits-to-bank flow

**NOT a payroll system:**
- Does not process payroll
- Does not calculate contributions
- Reads payroll exports only

**NOT a recordkeeping system:**
- Does not post contributions to participant accounts
- Does not manage plan administration
- Validates recordkeeper data only

**NOT a bank reconciliation tool:**
- Does not reconcile bank statements to general ledger
- Does not handle cash management
- Focused on contribution deposits only

**NOT a data warehouse or ETL platform:**
- No real-time integration
- No database storage
- Batch processing of CSV exports only

**NOT a compliance monitoring system:**
- Does not monitor ongoing compliance
- Does not send alerts
- Generates point-in-time analysis only

**This is a specialized operational tool that replaces manual Excel reconciliation work for benefit plan contribution tracing. Nothing more, nothing less.**

---

*Version 1.0 | For Payroll Managers and Controllers*
