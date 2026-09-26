# ADR-002: Strict Decimal Arithmetic and First-Class Unresolved State

* **Status**: ACCEPTED / FROZEN  
* **Date**: 2026-09-23  
* **Deciders**: VaultBasis Architecture Group  
* **PRD Reference**: §2.1 (Deterministic Core), §2.2 (Unknown is First-Class), §15.1 (Canonical Arithmetic), §15.8 (Missing Price), §15.9 (Deficits)  

---

## Context and Problem Statement

IEEE 754 binary floating-point representations (`float`, `double` in Python, C, Go, JS) suffer from precision loss and binary rounding discrepancies (e.g. `0.1 + 0.2 = 0.30000000000000004`). In digital-asset tax accounting, sub-satoshi quantities and multi-million-dollar basis computations cannot tolerate floating-point drift.

Furthermore, traditional tax software frequently assumes `$0.00` basis or guesses values when historical cost data or pricing feeds are missing, converting an unknown fact into a false declaration of 100% taxable gain.

## Decision Drivers

* Financial reconciliation outputs must be reproducible to the exact penny or atomic unit across different platforms and CPU architectures.
* Missing facts must never be masked as zeroes, defaults, or assumed dates.
* Downstream audits must be able to distinguish between an actual `$0.00` basis gift/fork versus missing acquisition records.

## Decision Outcome

1. **Binary Floating Point is Strictly Prohibited**:
   - All accounting-critical amounts (proceeds, cost basis, gain/loss, variance, quantities) must be stored and computed exclusively using Python's `Decimal` type or exact integer representations.
   - Serialization to JSON or receipts must format monetary values as exact decimal strings (e.g., `"18400.00"`).
2. **First-Class `UNRESOLVED` State**:
   - When a required fact (cost basis, acquisition date, price, precision) is absent or ambiguous, the engine must mark `is_unresolved = True` with an explicit reason code (`BASIS_UNAVAILABLE`, `PRICE_UNAVAILABLE`, etc.).
   - The overall case state becomes `UNRESOLVED_DATA` if the missing fact materially impacts the financial disposition.
   - Missing data **never** becomes `$0.00`.

### Positive Consequences
* Zero floating-point divergence between local Edge and independent third-party verifiers.
* Prevents silent taxpayer overpayment or erroneous penalty assessments stemming from assumed zero basis.

### Negative Consequences
* Slower computational throughput compared to raw hardware floating-point registers (acceptable given case volumes in MMP-1).
* Requires strict type coercion and custom serialization handling across all connectors.
