---
name: quote-variance-analyzer
owner: sourcing-analyst
inputs: normalized_quotes
outputs: variance_flags
reads: normalized-quotes.csv, sourcing-policy.csv
writes: comparison-table.csv
next: sourcing-review-brief
---

# Quote Variance Analyzer

Compare normalized quotes with the fictional sourcing policy. Flag price variance above 12%, lead-time variance above 7 days, failed parses, and missing policy matches for human review. Write evidence for every flag to `comparison-table.csv`. Complete when every normalized quote has a policy status. Do not approve a supplier or modify policy.
