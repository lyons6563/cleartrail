Lost earnings must be calculated for any late, missing, or partial deposit.

Inputs:
- pay_date
- matched_deposit_date (or null)
- days_to_deposit
- payroll_total
- deposit_total
- unmatched_payroll_amount

Rules:
1) If late_flag = Yes:
   principal = payroll_total

2) If exception_type = Missing Deposit:
   principal = payroll_total

3) If exception_type = Partial:
   principal = unmatched_payroll_amount

Lost earnings formula (v1 conservative):
lost_earnings = principal × (annual_rate / 365) × days_late

Where:
annual_rate default = 0.05 (5%)
days_late = max(days_to_deposit − late_threshold, 0)

Outputs:
- principal_at_risk
- days_late_adjusted
- assumed_annual_rate
- lost_earnings_estimate
