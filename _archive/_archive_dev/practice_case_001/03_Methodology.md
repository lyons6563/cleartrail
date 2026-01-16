# Methodology

## Purpose
This document outlines the approach, procedures, and validation methods used to reconstruct the retirement plan transactions and identify compliance failures.

---

## Reconstruction Approach

### Overall Strategy
[Description of the high-level approach - e.g., "Bottom-up reconstruction using source payroll data as the truth source, reconciled against recordkeeper postings and bank deposits"]

### Key Principles
1. **Source Data Priority:** [Which data source is considered authoritative]
2. **Reconciliation Methodology:** [How discrepancies are identified and resolved]
3. **Validation Standards:** [What constitutes a validated transaction]
4. **Exception Handling:** [How exceptions are documented and escalated]

---

## Data Collection Procedures

### Step 1: Data Extraction
- **Objective:** Extract all relevant data from source systems
- **Sources:** [List of systems]
- **Extraction Method:** [Automated/Manual/API]
- **Data Elements:** [List key fields]
- **Validation:** [How data completeness is verified]
- **Documentation:** [Where extraction logs are stored]

### Step 2: Data Normalization
- **Objective:** Standardize data formats, field names, and date formats
- **Procedures:**
  - [Procedure 1 - e.g., Convert all dates to YYYY-MM-DD format]
  - [Procedure 2 - e.g., Standardize participant identifiers]
  - [Procedure 3 - e.g., Normalize contribution type codes]
- **Validation:** [How normalization is verified]

### Step 3: Data Matching & Linking
- **Objective:** Link records across systems using common identifiers
- **Matching Keys:** [List of fields used for matching]
- **Matching Rules:** [How partial matches are handled]
- **Unmatched Records:** [How unmatched records are handled]

---

## Reconstruction Procedures

### Procedure 1: Payroll Truth Table Construction
**Purpose:** Establish the authoritative record of what should have been contributed

**Steps:**
1. Extract payroll data for all pay periods in scope
2. Apply plan document rules (e.g., deferral limits, match formulas)
3. Calculate expected contributions by participant and pay period
4. Validate calculations against plan document provisions
5. Document any assumptions or interpretations

**Output:** Payroll Truth Table (see Reconstruction Ledgers)

### Procedure 2: Deposit Ledger Construction
**Purpose:** Track actual deposits made to the plan trust

**Steps:**
1. Extract bank/custodian deposit records
2. Match deposits to expected contribution amounts
3. Identify late deposits (compare deposit date to required deposit date)
4. Calculate deposit timing compliance
5. Reconcile deposit totals to contribution totals

**Output:** Deposit Ledger (see Reconstruction Ledgers)

### Procedure 3: Recordkeeper Posting Verification
**Purpose:** Verify what was actually posted to participant accounts

**Steps:**
1. Extract recordkeeper transaction data
2. Match postings to payroll truth table
3. Identify missing postings, duplicate postings, incorrect amounts
4. Verify allocation accuracy (correct participant, correct account type)
5. Validate transaction dates and effective dates

**Output:** Recordkeeper Posting Ledger (see Reconstruction Ledgers)

### Procedure 4: Reconciliation
**Purpose:** Identify and explain discrepancies between systems

**Reconciliation Points:**
- Payroll Truth Table vs. Deposit Ledger
- Deposit Ledger vs. Recordkeeper Postings
- Recordkeeper Postings vs. Participant Statements
- Bank Statements vs. Recordkeeper Cash Activity

**Reconciliation Methodology:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

---

## Validation & Quality Assurance

### Validation Rules

| Rule ID | Description | Validation Method | Action on Failure |
|---------|-------------|-------------------|-------------------|
| V001 | Payroll totals match recordkeeper totals | Sum comparison | Flag for investigation |
| V002 | All deposits within DOL timing requirements | Date comparison | Calculate lost earnings |
| V003 | Participant IDs consistent across systems | Cross-reference check | Manual review |
| V004 | Contribution amounts within plan limits | Limit check | Flag exception |

### Quality Assurance Procedures
1. **Independent Review:** [Who reviews the reconstruction]
2. **Sampling:** [If sampling is used, describe methodology]
3. **Re-performance:** [Key calculations that are re-performed]
4. **Documentation Review:** [How documentation is verified]

---

## Exception Handling

### Exception Classification

| Severity | Definition | Examples | Escalation |
|----------|------------|----------|------------|
| Critical | Regulatory violation with immediate impact | Late deposits > 15 days | Immediate notification |
| High | Significant discrepancy requiring correction | Missing contributions > $1,000 | Management review |
| Medium | Discrepancy requiring investigation | Data quality issues | Document in log |
| Low | Minor discrepancies or data quality issues | Rounding differences | Note for future review |

### Exception Resolution Process
1. **Identification:** [How exceptions are identified]
2. **Documentation:** [Where exceptions are logged]
3. **Investigation:** [Who investigates and how]
4. **Resolution:** [How resolutions are tracked]
5. **Verification:** [How resolutions are verified]

---

## Calculations & Formulas

### Contribution Calculations

#### Employee Deferrals
```
Formula: [e.g., MIN(Employee_Deferral_Percent × Gross_Pay, Annual_Limit - YTD_Deferrals)]
Source: Plan Document Section [X]
Validation: [How this is validated]
```

#### Employer Match
```
Formula: [e.g., IF(Deferral > 0, MIN(Deferral × Match_Rate, Max_Match_Amount), 0)]
Source: Plan Document Section [X]
Validation: [How this is validated]
```

### Lost Earnings Calculations
```
Method: [DOL Online Calculator / Actual Return / Reasonable Interest Rate]
Rate: [Rate used]
Period: [Calculation period]
```

---

## Tools & Technology

| Tool | Purpose | Version | Notes |
|------|---------|---------|-------|
| [Tool] | [Purpose] | [Version] | [Notes] |
| [Tool] | [Purpose] | [Version] | [Notes] |

---

## Assumptions & Limitations

### Key Assumptions
1. [Assumption 1 - e.g., Payroll data is accurate and complete]
2. [Assumption 2]
3. [Assumption 3]

### Known Limitations
1. [Limitation 1 - e.g., Historical data only available from MM/DD/YYYY]
2. [Limitation 2]
3. [Limitation 3]

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | [Date] | [Name] | Initial creation |
