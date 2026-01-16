# Dataset Reconciliation Issues Summary

## Overview
Three CSV files representing a mid-size employer's 401(k) plan with biweekly payroll, showing data from payroll export, bank/trust activity, and recordkeeper contributions.

**Scenario:** Payroll vendor change occurred between Period 2 and Period 3 (late January/early February 2024)

---

## Files Created

1. **01_Payroll_Export.csv** - Source payroll data (authoritative)
2. **02_Trust_Bank_Activity_Export.csv** - Bank deposit records
3. **03_Recordkeeper_Contribution_Export.csv** - Recordkeeper transaction postings

---

## Intentional Issues Built Into Data

### 1. Late Deposit (Period 3)
- **Pay Date:** 02/26/2024
- **Required Deposit Date:** ~03/05/2024 (7 business days)
- **Actual Deposit Date:** 03/11/2024
- **Days Late:** ~4 business days
- **Amount:** $1,313.00 (correct amount, but late)

### 2. Deposit Total Mismatch (Period 4)
- **Payroll Truth:** $1,313.00 (all 4 employees: $375 + $270 + $464 + $204)
- **Actual Deposit:** $1,109.00
- **Variance:** -$204.00 (Maria Garcia's deferral not included in deposit)
- **Root Cause:** New payroll vendor failed to include Maria Garcia in the deposit file

### 3. Missing Employee Deferral (Periods 3 & 4)
- **Employee:** Maria Garcia (Emp #1004)
- **Missing From:** Recordkeeper Contribution Export
- **Missing Amounts:**
  - Period 3: $204.00
  - Period 4: $204.00
  - **Total Missing:** $408.00
- **Root Cause:** Employee ID mapping error during payroll vendor transition - Maria Garcia's contributions not transmitted to recordkeeper

### 4. Formatting Inconsistencies

**Name Formats:**
- Payroll: "James Martinez" (First Last)
- Recordkeeper: "Martinez, James" (Last, First)

**Date Formats:**
- Payroll: "01/15/2024" (MM/DD/YYYY)
- Recordkeeper: "Jan 15 2024" (Mon DD YYYY)
- Bank: "2024-01-18" (YYYY-MM-DD)

---

## Reconciliation Summary

### Period 1 (Pay Date: 01/15/2024)
- **Payroll Total:** $1,313.00 ✅
- **Bank Deposit:** $1,313.00 ✅
- **Recordkeeper Posted:** $1,313.00 ✅
- **Status:** Fully reconciled

### Period 2 (Pay Date: 01/29/2024)
- **Payroll Total:** $1,313.00 ✅
- **Bank Deposit:** $1,313.00 ✅
- **Recordkeeper Posted:** $1,313.00 ✅
- **Status:** Fully reconciled

### Period 3 (Pay Date: 02/26/2024) - **VENDOR TRANSITION**
- **Payroll Total:** $1,313.00 ✅
- **Bank Deposit:** $1,313.00 ✅ (but **LATE** - deposited 03/11)
- **Recordkeeper Posted:** $1,109.00 ❌ (missing Maria Garcia $204.00)
- **Status:** Missing deferral, late deposit

### Period 4 (Pay Date: 03/12/2024)
- **Payroll Total:** $1,313.00 ✅
- **Bank Deposit:** $1,109.00 ❌ (missing Maria Garcia $204.00)
- **Recordkeeper Posted:** $1,109.00 ❌ (missing Maria Garcia $204.00)
- **Status:** Deposit mismatch, missing deferral

---

## Key Findings

1. **Late Deposit:** Period 3 deposit made 4+ business days late
2. **Deposit Mismatch:** Period 4 deposit short by $204.00
3. **Missing Contributions:** Maria Garcia's deferrals not posted to recordkeeper for periods 3 & 4 ($408.00 total)
4. **Data Quality Issues:** Inconsistent name and date formats require normalization for reconciliation

---

## Total Exposure

- **Missing Contributions:** $408.00 (Maria Garcia, periods 3 & 4)
- **Late Deposit:** Period 3 (lost earnings calculation required)
- **Unallocated Funds:** $204.00 (Period 4 deposit includes funds not posted to participant accounts)
