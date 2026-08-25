# Fictional procurement packaging input

All organizations, identifiers, values, and tables in this directory are fictional.

- Team: Sourcing Operations Lab
- Mission: Reduce weekly manual comparison of supplier quotes while preserving buyer approval.
- Cadence: Weekly and on-demand.
- Lv4: Strategic sourcing
- Lv5: Supplier quote evaluation
- Primary input: `incoming-quotes.csv` plus `sourcing-policy.csv`
- Primary output: `sourcing-review-brief.md`
- Canonical tables:
  - `incoming-quotes.csv`: quote_id, supplier_code, item_code, unit_price, lead_days, currency
  - `normalized-quotes.csv`: quote_id, supplier_code, item_code, unit_price_krw, lead_days, parse_status
  - `comparison-table.csv`: quote_id, price_variance_pct, lead_variance_days, policy_status, evidence
- Human responsibility: A buyer confirms policy exceptions and selects a supplier. The agent never sends a purchase order.
- Thresholds: price variance above 12% or lead-time variance above 7 days requires human review.
- Integration: currently independent; no ERP write connector is approved.
- Confirmation: the facts in this file and the supplied WFDATA are approved fictional test inputs.
