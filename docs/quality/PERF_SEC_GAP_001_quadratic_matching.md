# VaultBasis — Performance Characterization & Remediation Report
## ID: PERF-SEC-GAP-001 — Algorithmic Scaling Remediation & Semantic Invariance

**Standard:** Left-Shift Granite Industrial Standard (PRD §64, §71)  
**Target Engine:** `edge.assurance.reconciliation_engine.DeterministicReconciliationEngine`  
**Evaluation Date:** 2026-10-09  
**Candidate Evolution:** Candidate 7 (Superseded) $\rightarrow$ **Candidate 8** (Active Pre-Sign Baseline)  
**Status:** **REMEDIATED & VERIFIED — READY FOR CLOSURE**

---

### 1. Empirical Scaling Matrix: Before vs. After Optimization

The remediation replaced the nested linear candidate scan and repeated ISO string date parsing with asset-partitioned candidate indexing and single-pass parsed date structures, while maintaining 100% exact Decimal arithmetic, ambiguity detection, duplicate handling, and RFC 8785 canonical serialization.

| $N$ (Broker Rows) | Total Rows ($2N$) | Candidate 7 Baseline ($O(N^2)$) | Candidate 8 Optimized ($O(N)$) | Speedup Factor | Candidate 8 $\text{Time}/N$ | Candidate 8 $\text{Time}/N^2$ | Candidate 8 Peak RAM |
|---|---|---|---|---|---|---|---|
| **1,000** | 2,000 | **11.0237 s** | **0.1725 s** | **63.9×** | 0.1725 ms | 0.1725 µs | 1.14 MB |
| **2,500** | 5,000 | **76.7748 s** | **0.4303 s** | **178.4×** | 0.1721 ms | 0.0688 µs | 2.81 MB |
| **5,000** | 10,000 | **282.9238 s** (~4.7 min) | **0.8620 s** | **328.2×** | 0.1724 ms | 0.0345 µs | 5.90 MB |
| **10,000** | 20,000 | **1,346.9570 s** (~22.4 min) | **2.1414 s** | **629.0×** | 0.2141 ms | 0.0214 µs | 11.46 MB |

---

### 2. Algorithmic Complexity Elimination

1. **Eradication of Quadratic Behavior:**
   - Candidate 7 exhibited a constant $\text{Time}/N^2 \approx 11.0 - 13.5\,\mu\text{s}$, confirming $O(N^2)$.
   - Candidate 8 exhibits a flat per-record cost $\text{Time}/N \approx 0.17 - 0.21\,\text{ms}$, while $\text{Time}/N^2$ drops toward zero ($0.1725 \rightarrow 0.0214\,\mu\text{s}$), demonstrating an approximately linear $O(N)$ profile.
2. **20,000-Record Throughput:**
   - Throughput increased from $14.8\,\text{rows/sec}$ to **$9,340\,\text{rows/sec}$**.
3. **Memory Footprint:**
   - Peak memory for 20,000 rows dropped from $37.09\,\text{MB}$ to **$11.46\,\text{MB}$**.

---

### 3. Verification of Non-Negotiable Invariants

All semantic invariants were validated across `test_reconciliation_engine_semantic_equivalence.py` and the 31-suite `UAT-05..28` integration suite:
- **Zero Float Drift:** 100% exact `Decimal` calculations across all differences and agreed records.
- **Ambiguity Detection:** Multi-candidate pairings without distinct facts remain strictly flagged as `AMBIGUOUS_MATCH`.
- **Deterministic Ordering:** Identical duplicate rows are paired strictly in index order.
- **Box 2 Reporting Scope:** Unreported basis (`basis_reported_to_irs=NO`) consistently generates `REPORTING_SCOPE_DIFFERENCE`.
- **Micro-Variance:** Sub-cent/cent differences ($0.01) are preserved without implicit tolerance.
- **Contract Integrity:** JCS hash calculation and Ed25519 signatures remain byte-for-byte canonical.

---

### 4. Milestone Disposition

- **`PERF-01`:** **PASS — 20,000 transactions reconciled in 2.14s with exact precision**
- **`PERF-SEC-GAP-001`:** **REMEDIATED & CLOSED ON CANDIDATE 8**
