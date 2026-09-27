# GAP-001 — Asset Quantity Comparison

**Status:**
DEFERRED — NOT PART OF MMP-1 AUTHORITATIVE RECONCILIATION

**Discovered by:**
Proposed Golden Fixture `G004_quantity_difference`

**Observation:**
The frozen MMP-1 reconciliation taxonomy does not define `QUANTITY_DIFFERENCE` and the authoritative reconciliation engine does not independently compare asset quantity between sources.

**Required decision before implementation:**
- Canonical quantity representation (strings vs decimals)
- Asset/source-specific quantity precision and representation rules.
- Source precision preservation
- Normalization rules
- Aggregation semantics
- Lot-vs-transaction comparison semantics
- Matching interaction (does a quantity difference break a match?)
- Missing quantity behavior (already covered by semantic rules: preserve uncertainty, do not coerce to zero)
- Resulting outcome-state behavior
- Evidence Contract compatibility impact

**MMP-1 behavior:**
No `QUANTITY_DIFFERENCE` outcome may be invented.
Missing quantity is handled independently by the existing unknown/missing-fact semantics (`SEM-MISS-002`) and must never be coerced to zero, resulting in `UNRESOLVED_DATA`. Two present but different quantities are not currently diffed.

**Disposition:**
Candidate for post-preview semantic-contract revision.
