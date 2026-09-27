# VaultBasis Reconciliation Semantics (v0.1)

**Status:** FROZEN for Design-Partner Preview (MMP-1)
**Scope:** Deterministic financial reconciliation between Form 1099-DA (Broker) and Koinly Capital Gains CSV (Ledger).
**Goal:** Serve as the executable specification for the Golden Test Corpus and Evidence Contract.

---

## 1. Time & Timezone Normalization

**Core Philosophy:** VaultBasis does not invent or infer timezones merely to make records match (violates PRD AC-02/AC-03).

### Definitions
* `source_timestamp`: The exact literal string supplied by the source (e.g., `2025-12-31 23:58:00`).
* `source_timezone`: The explicitly defined offset (e.g., `Z`, `-05:00`). If absent, the state is `UNKNOWN`.
* `normalized_instant`: A UTC instant (ISO 8601). Produced *only* when deterministic normalization is possible.

### Matching Rules
1. **Known Timezone on Both Sides:** Deterministically normalize both to `normalized_instant` and compare. 
2. **Timezone Missing/Ambiguous:** If one or both sources lack an explicit timezone offset, the engine **will not** assume UTC or local time. The system will rely on matching the explicit string date component (YYYY-MM-DD). If the strings differ, it falls back to the defined Outcome State rules.
3. **Year-Boundary Discrepancy:** If the deterministic `normalized_instant` or the literal string comparison places the transaction in two different reporting years (e.g., Dec 31 2025 vs Jan 1 2026), the engine will preserve both classifications and emit a **`SCOPE_DIFFERENCE`** state.
4. **Heuristics Banned:** The engine will **never** apply a `±N minutes -> same transaction` fuzzy matching heuristic.

---

## 2. Currency, Precision, and Rounding Tolerances

**Core Philosophy:** Distinguish representation normalization from financial tolerance. A $0.01 difference is neither automatically a `BASIS_DIFFERENCE` nor automatically `MATCHED`.

### Definitions
* `raw_delta`: Absolute mathematical difference (`abs(A - B)`) between exact Decimals.
* `normalized_delta`: Difference after applying explicitly declared rounding rules for the input formats.
* `source_precision`: The decimal places natively supplied by the input (e.g., 2 for USD, 8 for BTC).
* `normalization_rule`: The documented rule applied (e.g., "Koinly rounds fiat to 2 decimal places using HALF_UP").
* `tolerance_applied`: The explicitly configured and evidenced threshold allowed for matching.

### Matching Rules
1. **Representation Normalization:** If a broker reports `$10.005` (defined as 3 decimal places) and Koinly reports `$10.01` (defined as rounded to 2 places), the engine canonicalizes the broker to `$10.01` using standard accounting rounding (HALF_UP). If the `normalized_delta` is `0`, they match.
2. **Tolerance Application:** General fuzzy tolerances (`abs(A-B) <= $0.01 -> MATCHED`) are explicitly banned. Any applied tolerance must be:
   - Versioned
   - Deterministic
   - Evidenced natively in the Receipt schema.
3. **Precision Preservation:** The engine uses Python `decimal.Decimal`. Float coercion is prohibited.

---

## 3. Data Integrity & Missing Fields

**Core Philosophy:** Missing facts must remain unresolved. The engine will not silently inject `0`, `""`, or default assumptions.

### Matching Rules
1. **Missing Basis:** A missing cost basis on either side will **never** be coerced to `$0.00`. It will trigger an `UNRESOLVED` outcome with reason code `MISSING_BASIS`.
2. **Missing Quantity:** A missing quantity will **never** be coerced to `0`. It will trigger an `UNRESOLVED` outcome.
3. **Duplicate Rows:** Identical rows (same asset, same exact time, same amounts) are grouped deterministically based on an explicit index. If the counts of duplicates differ between 1099-DA and Ledger, the surplus items fall to `UNRESOLVED` or `MISSING_FROM_BROKER`.
4. **Malformed/Negative Values:** Negative proceeds/basis or structurally malformed CSV rows immediately trigger a safe failure (rejected at the parsing boundary).

---

## 4. Outcome-State Transition Logic

Every matched or unmatched pair must resolve cleanly into one of the **13 Bounded Outcome States**.

| Condition (1099-DA vs Ledger) | Target State |
| :--- | :--- |
| Exact Identity & Exact Values (post-normalization) | `MATCHED` |
| Same Identity, Cost Basis differs > Tolerance | `BASIS_DIFFERENCE` |
| Same Identity, Proceeds differ > Tolerance | `PROCEEDS_DIFFERENCE` |
| Reporting Year crosses boundary | `SCOPE_DIFFERENCE` |
| Asset string mismatch (but value identity matches) | `ASSET_MISMATCH` |
| Ledger item missing from 1099-DA | `MISSING_FROM_BROKER` |
| 1099-DA item missing from Ledger | `MISSING_FROM_LEDGER` |
| Field missing or parsing fails | `UNRESOLVED` |

*Note: If an edge case does not fit cleanly into a substantive error state (like `SCOPE_DIFFERENCE`), it must fall back to `UNRESOLVED` with a machine-readable reason string (e.g., `TIMEZONE_CONTEXT_MISSING`). The 13-state vocabulary is frozen to protect Evidence Contract verifier compatibility.*
