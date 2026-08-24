# Canonical contract

```contract
tables:
  incoming-quotes.csv: quote_id, supplier_code, item_code, unit_price, lead_days, currency
  sourcing-policy.csv: (미확인)
  normalized-quotes.csv: quote_id, supplier_code, item_code, unit_price_krw, lead_days, parse_status
  comparison-table.csv: quote_id, price_variance_pct, lead_variance_days, policy_status, evidence
writers:
  incoming-quotes.csv: none
  sourcing-policy.csv: none
  normalized-quotes.csv: quote-intake-normalizer
  comparison-table.csv: quote-variance-analyzer
chain: quote-intake-normalizer -> quote-variance-analyzer -> buyer-variance-review-hold -> sourcing-review-brief -> buyer-confirmation-hold
payloads: quote_bundle, normalized_quotes, variance_flags, sourcing_review_brief
threshold: price variance above 12% or lead-time variance above 7 days requires human review
halt_at: missing-input-hold, buyer-variance-review-hold, buyer-confirmation-hold, external-action-hold
```
