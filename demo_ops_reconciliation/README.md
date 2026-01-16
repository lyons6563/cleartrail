# Demo: Ops Reconciliation

## What each file represents
- `system_a_transactions.csv`: Operational transaction records (source system).
- `system_b_cash.csv`: Cash ledger postings (bank/payments system).

## Data issues included
- Inconsistent column names and ID formats
- Mixed date formats
- Batched deposits (one cash row maps to multiple source rows)
- Partial matches and amount mismatches
- Timing delays between source and cash dates
- Missing rows on both sides
- Ambiguous matches with similar amounts/references

## What the engine should detect
- Exact matches for clean records
- Many-to-one batch matches and resulting exceptions
- Late postings based on date gaps
- Missing cash or missing source entries
- Ambiguous cases that require review
