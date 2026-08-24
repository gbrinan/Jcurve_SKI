---
name: sourcing-review-brief
owner: buyer
inputs: variance_flags
outputs: sourcing_review_brief
reads: comparison-table.csv
writes: (none)
next: human
---

# Sourcing Review Brief

Summarize ordinary rows, flagged rows, evidence, and unresolved questions in `sourcing-review-brief.md`. Stop and request buyer confirmation. Complete when the brief names every quote and the buyer's next action. Do not select a supplier, send a purchase order, or write to an ERP.
