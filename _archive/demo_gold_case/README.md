# ClearTrail  
Operational Evidence Engine for Payroll → Benefits → Bank Reconciliation

ClearTrail is a specialized reconciliation and evidence-generation engine designed to reconstruct, test, and document the flow of employee benefit contributions from payroll systems to trust accounts (and optionally to recordkeepers).

It replaces manual, error-prone Excel workflows used in benefit plan audits, compliance reviews, and operational controls testing.

ClearTrail is not a payroll system.  
It is not a recordkeeper.  
It is an independent evidence and exception engine.

---

## What ClearTrail Does

ClearTrail ingests payroll and bank/trust exports, normalizes inconsistent data, matches contribution activity across systems, detects failures, and generates audit-ready evidence packs.

Specifically, it:

• Normalizes payroll and bank data with inconsistent formats  
• Reconstructs payroll-to-deposit contribution flows  
• Calculates objective timeliness metrics  
• Detects late, missing, and partial deposits  
• Quantifies principal at risk  
• Generates standardized reconciliation schedules  
• Produces structured exception and correction registers  
• Creates full evidence indexes for audit and regulatory support  

All outputs are CSV-based and designed for direct use in audit workpapers, compliance files, and remediation workflows.

---

## Regulatory Alignment

ClearTrail evaluates contribution activity under **29 CFR §2510.3-102** (participant contributions as plan assets) and produces objective measurements that support both:

• **Small plan safe-harbor testing** (7-business-day framework)  
• **“As soon as reasonably possible” analysis** for larger plans (facts-and-circumstances)

ClearTrail does not provide legal conclusions.  
It produces the structured evidence, metrics, and exception classifications required to support:

• Timely remittance testing  
• Prohibited transaction analysis  
• Correction documentation  
• Audit workpapers  
• DOL inquiry response packages  

Each detected exception is tagged with its governing regulatory reference and standardized defect classification.

---

## Core Exception Types Detected

• Late deposits  
• Missing deposits  
• Partial/short deposits  
• Amount mismatches  
• Missing participant postings (optional recordkeeper file)  
• Data quality failures  

For each exception, ClearTrail calculates:

• Business days to deposit  
• Principal at risk  
• Pattern and confidence metrics  
• Estimated lost-earnings exposure (supporting correction workflows)  

---

## Outputs Produced

ClearTrail generates four primary artifacts:

1. **remittance_schedule.csv**  
   Pay-period level reconstruction showing payroll totals, matched deposits, business-day timing, match confidence, and exception status.

2. **timeliness_report.csv**  
   Isolated late-deposit analysis with days-late calculations and exposure indicators.

3. **exception_log.csv**  
   Structured exception ledger including defect type, severity, variance, regulatory basis, and remediation signals.

4. **evidence_index.csv**  
   Full inventory of source files, date ranges, record counts, and relevance descriptions supporting audit trail requirements.

Optional outputs may include correction registers and lost-earnings schedules.

---

## Real-World Conditions Supported

ClearTrail is built to handle the conditions that break manual workflows:

• Combined deposits covering multiple payrolls  
• Partial and corrective deposits  
• Trust-account noise (fees, reversals, interest)  
• Inconsistent employee identifiers  
• Mixed date and currency formats  
• Out-of-sequence recordkeeper postings  

---

## Who ClearTrail Is For

### Employee Benefit Plan Auditors
• Full-population remittance testing  
• Standardized workpapers  
• Reduced audit hours  
• Lower deficiency risk  
• Defensible reconstruction methodology  

### Plan Sponsors / Payroll & Finance Leaders
• Early detection before audits  
• Objective proof of operational controls  
• Reduced correction cost  
• Lower fiduciary exposure  
• Faster audit cycles  

### TPAs / ERISA & Compliance Firms
• Scalable reconstruction capability  
• Repeatable client deliverables  
• Faster engagement turnaround  
• Differentiated evidence layer  
• Reduced manual labor dependency  

---

## Explicit Non-Goals

ClearTrail does NOT:

• Process payroll  
• Post participant contributions  
• Perform general ledger reconciliation  
• Monitor plans in real time  
• Replace payroll-recordkeeper integrations  
• Provide legal or fiduciary opinions  

ClearTrail is an independent evidence and reconstruction layer for high-risk contribution flows.

Nothing more. Nothing less.

---

## Typical Impact

• 80–90% reduction in manual reconciliation time  
• Full-population testing instead of sampling  
• Early detection of remittance failures  
• Structured support for correction workflows  
• Audit-ready evidence in minutes instead of weeks  

---

ClearTrail v1 is a wedge product focused exclusively on payroll → benefits → bank reconciliation.

If this wedge succeeds, the same evidence-engine architecture may later be applied to other high-risk financial flows.
