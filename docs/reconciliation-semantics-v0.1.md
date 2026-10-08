# VaultBasis Reconciliation Semantics (v0.1)

**Status:** FROZEN for Design-Partner Preview (MMP-1)
**Scope:** Deterministic financial reconciliation between Form 1099-DA (Broker) and Koinly Capital Gains CSV (Ledger).
**Goal:** Serve as the executable specification for the Golden Test Corpus and Evidence Contract.

---

## 1. Time & Timezone Normalization

### Definitions
* `source_timestamp`: The exact literal string supplied by the source.
* `source_timezone`: The explicitly defined offset. If absent, the state is `UNKNOWN`.
* `normalized_instant`: A UTC instant (ISO 8601). Produced *only* when deterministic normalization is possible.

### Rules
**SEM-TIME-001**
An absent timezone MUST NOT be inferred solely to cause two records to match.

**SEM-TIME-002**
An offset-aware timestamp MUST be normalized deterministically to the canonical comparison representation (UTC instant).

**SEM-TIME-003**
If timezone context is insufficient to determine the definitive reporting year, the engine MUST NOT guess. The engine MUST preserve the uncertainty and emit an `UNRESOLVED` outcome state with the reason code `TIMEZONE_CONTEXT_MISSING`. *(Note: Do not overload `SCOPE_DIFFERENCE` unless explicitly defined for reporting-period mismatches by the Evidence Contract).*

**SEM-TIME-004**
The engine MUST NOT apply fuzzy matching heuristics (e.g., `±N minutes -> same transaction`).

---

## 2. Currency, Precision, and Rounding Tolerances

### Rules
**SEM-NUM-001**
Financial values MUST use exact decimal/integer representation (e.g., Python `decimal.Decimal`) in the authoritative reconciliation path. Float coercion is STRICTLY PROHIBITED.

**SEM-ROUND-001**
A monetary tolerance (e.g., `abs(A-B) <= $0.01`) MUST NOT be silently interpreted as financial equality. Any applied tolerance MUST be explicit, versioned, deterministic, and evidenced in the Receipt schema.

**SEM-ROUND-002**
For all monetary comparisons in Release 1.5:
1. **Internal Numeric Representation:** Exact `decimal.Decimal` arithmetic across the entire pipeline.
2. **Source Preservation:** Source-supplied precision is preserved without pre-comparison rounding (sub-cent values are never truncated/rounded for matching).
3. **Comparison Precision:** Exact Decimal matching with zero implicit tolerance ($0.00000000). Any non-zero difference between supported sources triggers a deterministic difference outcome (`PROCEEDS_DIFFERENCE` or `BASIS_DIFFERENCE`).
4. **Rounding Mode:** No rounding is applied during reconciliation matching.
5. **Receipt & Evidence Precision:** Preserved as exact canonical string representation per RFC 8785 in generated receipts.
6. **Display Precision:** UI display formatting preserves the underlying exact Decimal in data attributes and verified receipts, with clear visual notation for sub-cent micro-variances ($< \$0.01$).

### 2.1 Canonical Decimal-String Grammar & Lexical Contract

To eliminate cryptographic ambiguity during RFC 8785 JSON canonicalization, all monetary values in receipts and canonical transactions follow this normative grammar:

* **Base-10 Only:** Scientific/exponent notation (e.g. `1e-5`, `2.5E4`) is strictly forbidden.
* **No Leading Plus:** Positive values MUST NOT contain a leading `+` sign (e.g. `100.00`, never `+100.00`).
* **Zero Normalization:** Negative zero (`"-0"`, `"-0.00"`) is prohibited and normalized to unsigned zero (`"0"`).
* **No Redundant Integer Zeros:** Values $\ge 1$ MUST NOT have leading zeros (e.g. `"1"`, never `"01"`). Values $< 1$ MUST have exactly one leading zero before the decimal point (e.g. `"0.004"`, never `".004"`).
* **Trailing Zero Normalization in Canonical Numbers:** In `canonical_numeric_value`, redundant trailing zeros in fractional parts are normalized away (e.g., `1.00` $\to$ `"1"`, `0.00400` $\to$ `"0.004"`, `-0.00` $\to$ `"0"`), ensuring exactly one canonical representation per mathematical quantity.
* **Three-Layer Lexical Separation:**
  1. `source_lexical_value`: Raw literal string extracted from source CSV/JSON (e.g., `"1.00"` or `"0.00400"`), preserved verbatim in provenance references.
  2. `canonical_numeric_value`: Normalized Base-10 Decimal string adhering to canonical normalization (e.g., `"1"` or `"0.004"`), embedded in RFC 8785 signed receipts.
  3. `display_value`: Formatted currency for practitioner UI with explicit micro-variance annotation (**"Micro-variance — review if relevant"** for sub-cent differences $< \$0.01$). Avoids calling sub-cent differences "material differences" unless applying an approved materiality policy.

---

## 3. Data Integrity & Missing Fields

### Rules
**SEM-ING-001**
Negative proceeds, negative basis, or structurally malformed CSV rows MUST immediately trigger a safe failure or `UNRESOLVED` state without producing silent financial output.

**SEM-MISS-001**
Missing cost basis MUST NOT be converted to zero.

**SEM-MISS-002**
Missing quantity MUST NOT be converted to zero.

**SEM-DUP-001**
Identical rows MUST be grouped deterministically based on an explicit index. Conflicting counts between sources MUST trigger `UNRESOLVED` or the appropriate missing state.

---

## 4. Outcome-State Transition Logic

### Rules
**SEM-STATE-001**
The reconciliation engine MUST emit only outcome states declared by the frozen MMP-1 13-state outcome taxonomy.

**SEM-STATE-002**
An unresolved required fact MUST remain represented as an unresolved fact in the resulting evidence/receipt, preserving the exact reason code.

**SEM-MATCH-001**
A `MATCHED` outcome MUST require exact identity and exact values post-normalization.

**SEM-EVID-001**
The resulting receipt MUST preserve sufficient provenance to identify the source artifacts and reconciliation semantics version used.

---

## 5. Rule Registry

| Rule ID | Status | Category | Preview Gate |
| :--- | :--- | :--- | :--- |
| SEM-ING-001 | ACTIVE | Intake | AC-04 / PROD-GATE-14 |
| SEM-TIME-001 | ACTIVE | Timezone | AC-02 / AC-03 |
| SEM-TIME-002 | ACTIVE | Timezone | AC-02 |
| SEM-TIME-003 | ACTIVE | Timezone | AC-03 |
| SEM-TIME-004 | ACTIVE | Timezone | AC-02 |
| SEM-NUM-001 | ACTIVE | Numeric | AC-02 / PROD-GATE-15 |
| SEM-ROUND-001 | ACTIVE | Rounding | AC-02 / PROD-GATE-15 |
| SEM-ROUND-002 | ACTIVE | Rounding | AC-02 / PROD-GATE-15 |
| SEM-MISS-001 | ACTIVE | Missing Fact | AC-03 |
| SEM-MISS-002 | ACTIVE | Missing Fact | AC-03 |
| SEM-DUP-001 | ACTIVE | Duplicates | AC-02 |
| SEM-STATE-001 | ACTIVE | Outcome | AC-02 |
| SEM-STATE-002 | ACTIVE | Outcome | AC-03 |
| SEM-MATCH-001 | ACTIVE | Matching | AC-02 |
| SEM-EVID-001 | ACTIVE | Evidence | AC-05 |
