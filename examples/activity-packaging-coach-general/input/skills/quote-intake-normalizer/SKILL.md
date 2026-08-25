---
name: quote-intake-normalizer
owner: sourcing-analyst
inputs: quote_bundle
outputs: normalized_quotes
reads: incoming-quotes.csv
writes: normalized-quotes.csv
next: quote-variance-analyzer
---

# Quote Intake Normalizer

Start when a fictional quote bundle arrives. Normalize currency and required fields into `normalized-quotes.csv`. Preserve failed parses with `parse_status=review`; never drop a row or infer a missing price. Complete when every input quote ID appears once in the output. Do not contact suppliers or select a quote.
