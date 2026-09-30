# VaultBasis Master Tasks Ledger

> Historical ledger: task IDs assigned by VB-GOV-001; missing commit attribution remains unresolved. See [current registry](docs/task_registry.json), [active MMP-1.1 ledger](docs/mmp11_task_ledger.md), and [execution standard](docs/task_execution_standard.md). Historical COMPLETED does not establish present qualification.

| Task ID | Task Description | Status | Layer | Commit ID | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| LEGACY-001 | **L1.1 / L1.2 Canonicalization & Hashing** | COMPLETED | L1 | (Previous) | Implemented deterministic UTF-8 bytes and SHA-256 digests. 12 Normative vectors locked. |
| LEGACY-002 | **Verify payload integrity decoupled from external truth** | COMPLETED | L1 | (Previous) | Verifier modified to declare "PAYLOAD & SIGNATURE VERIFIED" rather than asserting external truth. |
| LEGACY-003 | **L2.1 Preflight Implementation** | COMPLETED | L2 | `3b5ef2e5c1b934ed5e54e106e7cff17fcab75bda` | Deterministic PreflightReport (profile detection, row/condition stats, readiness state) in `IntakeDispatcher`. No inferring/coercion. |
| LEGACY-004 | **L2.2 Finding Why Explanations** | COMPLETED | L2 | `3b5ef2e5c1b934ed5e54e106e7cff17fcab75bda` | Standardized `render_explanation` engine. 6-question boundary rules applied. Golden tests implemented for semantic snapshot. |
| LEGACY-005 | **Legal Entity Check (TecTixBase EURL)** | COMPLETED | L2 | `3b5ef2e5c1b934ed5e54e106e7cff17fcab75bda` | Replaced "VaultBasis Inc." with TecTixBase EURL across public assets. Sealed RC1 distribution restored. |
| LEGACY-006 | **L2.3 Provenance Mapping** | PENDING | L2 | | (Next up) Must trace material findings to source rows/hashes without violating privacy boundaries. |
