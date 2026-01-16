# Scope & Systems Map

## Purpose
This document defines the scope of the reconstruction effort and maps the systems, data sources, and processes involved in the retirement plan operations to identify data flow, integration points, and potential failure points.

---

## Scope Definition

### In Scope
- **Time Period:** [Start Date] to [End Date]
- **Plan Components:** [e.g., 401(k) deferrals, employer match, safe harbor contributions]
- **Participant Population:** [e.g., All active participants, terminated participants with account balances]
- **Data Sources:** [List of systems/data sources included]

### Out of Scope
- [Exclusion 1 - e.g., Prior plan years]
- [Exclusion 2 - e.g., Non-qualified plans]
- [Exclusion 3 - e.g., Specific participant groups]

### Scope Limitations
[Any constraints, data availability issues, or limitations that affect the reconstruction]

---

## Systems Architecture

### System Overview

| System Name | Type | Owner/Vendor | Purpose | Data Retention Period |
|-------------|------|--------------|---------|----------------------|
| [System 1] | Payroll | [Vendor] | [Description] | [Period] |
| [System 2] | HRIS | [Vendor] | [Description] | [Period] |
| [System 3] | Recordkeeping | [Vendor] | [Description] | [Period] |
| [System 4] | TPA System | [Vendor] | [Description] | [Period] |

---

## Data Flow Diagram

### Process Flow: Contribution Processing

```
[Payroll System]
    │
    ├─> Extract: Employee deferrals, match calculations
    │
    ├─> [Manual Process/Interface]
    │
    ├─> [Recordkeeper System]
    │       │
    │       ├─> Post contributions
    │       ├─> Allocate to participant accounts
    │       └─> Generate confirmations
    │
    └─> [Bank/Custodian]
            │
            └─> Deposit funds
```

### Integration Points

| Integration | Source System | Target System | Method | Frequency | Failure Points |
|-------------|---------------|---------------|--------|-----------|----------------|
| Payroll → Recordkeeper | [System] | [System] | [API/File/Manual] | [Daily/Weekly] | [Known issues] |
| HRIS → Payroll | [System] | [System] | [Method] | [Frequency] | [Issues] |
| Recordkeeper → Bank | [System] | [System] | [Method] | [Frequency] | [Issues] |

---

## Data Sources Inventory

### Primary Data Sources

#### Payroll Data
- **Source:** [System/File Name]
- **Location:** [Path/System]
- **Format:** [CSV/Excel/Database/API]
- **Key Fields:** Employee ID, Pay Date, Gross Pay, Deferral Amount, Match Amount
- **Update Frequency:** [Frequency]
- **Data Quality Issues:** [Known issues]

#### Recordkeeper Data
- **Source:** [System/File Name]
- **Location:** [Path/System]
- **Format:** [Format]
- **Key Fields:** Participant ID, Transaction Date, Contribution Type, Amount, Account Balance
- **Update Frequency:** [Frequency]
- **Data Quality Issues:** [Known issues]

#### Bank/Custodian Data
- **Source:** [System/File Name]
- **Location:** [Path/System]
- **Format:** [Format]
- **Key Fields:** Deposit Date, Amount, Reference Number, Clearing Date
- **Update Frequency:** [Frequency]
- **Data Quality Issues:** [Known issues]

### Supporting Data Sources

| Data Source | Type | Purpose | Availability |
|-------------|------|---------|--------------|
| [Source] | [Type] | [Purpose] | [Available/Partial/Missing] |
| [Source] | [Type] | [Purpose] | [Available/Partial/Missing] |

---

## System Interfaces & Dependencies

### Critical Dependencies
1. [Dependency 1 - e.g., Payroll system must complete processing before recordkeeper import]
2. [Dependency 2]
3. [Dependency 3]

### Known System Issues
| System | Issue | Impact | Status |
|--------|-------|--------|--------|
| [System] | [Issue description] | [Impact] | [Resolved/Open] |
| [System] | [Issue description] | [Impact] | [Resolved/Open] |

---

## Data Mapping

### Key Field Mappings

| Payroll Field | Recordkeeper Field | Transformation | Notes |
|---------------|-------------------|----------------|-------|
| Employee_ID | Participant_ID | [Direct/Transform] | [Notes] |
| Pay_Date | Transaction_Date | [Calculation] | [Notes] |
| Deferral_Amt | Contribution_Amount | [Direct/Transform] | [Notes] |

---

## Access & Security

| System | Access Method | Credentials Location | Access Level |
|--------|--------------|---------------------|--------------|
| [System] | [Method] | [Location] | [Level] |
| [System] | [Method] | [Location] | [Level] |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | [Date] | [Name] | Initial creation |
