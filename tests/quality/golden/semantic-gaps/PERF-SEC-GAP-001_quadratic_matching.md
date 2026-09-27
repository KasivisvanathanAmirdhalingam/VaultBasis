# PERF/SEC-GAP-001: Quadratic Reconciliation Matching

## Context
The current `DeterministicReconciliationEngine` executes an $O(N^2)$ matching loop when mapping transactions between source documents. It iterates over every unmatched ledger transaction for every broker transaction.

## The Gap
For exact duplicates (`SEM-DUP-001`), the semantics require deterministic grouping based on an explicit index. While the current engine produces the correct functional output (perfectly paired matches and isolated leftovers), it does so implicitly through greedy $O(N^2)$ iteration rather than an explicit $O(N)$ hash/grouping index. 

## Security and Performance Risk
For attacker-controlled or unexpectedly large inputs, this quadratic matching becomes a resource-exhaustion vector. An input with 10,000 identical transactions in both documents will require $100,000,000$ iterations in the core loop.

## Required Remediation (MMP-1)
1. Bound the preview engine: Define strict limits for max file size, max rows, max field lengths, and max case transactions. 
2. Refuse to process cases exceeding these bounds to fail safely and prevent denial of service.
3. (Future) Refactor the reconciliation engine to group transactions into a hash map before comparison, achieving $O(N)$ complexity and fulfilling the "explicit index" requirement of `SEM-DUP-001`.
