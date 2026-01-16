# Demo: Generic Reconciliation

## What the two systems represent
- **System A**: A source system export with record-level amounts by date and entity.
- **System B**: A downstream deposits ledger with posted totals by date.

## What problems exist in this demo
- **Inconsistent column names**: Source and deposits use different header conventions.
- **Partial matches**: One deposit is lower than the source total for a date.
- **Timing differences**: One deposit posts several business days after the source date.
- **Missing rows**: One source date has no corresponding deposit.
- **Amount mismatches**: Aggregate differences appear across the run.

## What ClearTrail surfaces
- Reconciled totals per source date
- Match status and confidence
- Timeliness flags for late postings
- Exception classification and variance details
