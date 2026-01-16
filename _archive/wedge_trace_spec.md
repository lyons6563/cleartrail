For every exception row, generate a trace pack containing:

1) payroll_components.csv
   All payroll rows used in this reconciliation window

2) deposit_components.csv
   All trust transactions used in this reconciliation window

3) trace_summary.txt
   - Pay date
   - Payroll total
   - Deposit total
   - Variance
   - Exception type
   - Days to deposit
   - Severity
   - Recommended action
   - Source files
   - Component record counts
