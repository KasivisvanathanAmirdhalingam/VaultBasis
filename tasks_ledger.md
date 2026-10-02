# VaultBasis Master Tasks Ledger

| Task Description | Status | Layer | Commit ID | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **L1.1 / L1.2 Canonicalization & Hashing** | COMPLETED | L1 | (Previous) | Implemented deterministic UTF-8 bytes and SHA-256 digests. 12 Normative vectors locked. |
| **Verify payload integrity decoupled from external truth** | COMPLETED | L1 | (Previous) | Verifier modified to declare "PAYLOAD & SIGNATURE VERIFIED" rather than asserting external truth. |
| **L2.1 Preflight Implementation** | COMPLETED | L2 | `3b5ef2e5c1b934ed5e54e106e7cff17fcab75bda` | Deterministic PreflightReport (profile detection, row/condition stats, readiness state) in `IntakeDispatcher`. No inferring/coercion. |
| **L2.2 Finding Why Explanations** | COMPLETED | L2 | `3b5ef2e5c1b934ed5e54e106e7cff17fcab75bda` | Standardized `render_explanation` engine. 6-question boundary rules applied. Golden tests implemented for semantic snapshot. |
| **Legal Entity Check (TecTixBase EURL)** | COMPLETED | L2 | `3b5ef2e5c1b934ed5e54e106e7cff17fcab75bda` | Replaced "VaultBasis Inc." with TecTixBase EURL across public assets. Sealed RC1 distribution restored. |
| **L2.3 Provenance Mapping** | PENDING | L2 | | (Next up) Must trace material findings to source rows/hashes without violating privacy boundaries. |
| **Test Inventory: Critical Invariants** | COMPLETED | QA | | Mapped critical VaultBasis invariants to existing tests to ensure deterministic behavior without writing new code. |

## Critical Invariants Test Inventory

| Critical Invariant | Production Owner | Test(s) | Golden vector? | Gap? |
| :--- | :--- | :--- | :--- | :--- |
| Float rejection & Decimal safety | Canonical model | `test_ddd_domain_models.py` | — | No |
| Unknown ≠ zero | Reconciliation | `test_slice2_intake_and_reconciliation.py` | Yes | No |
| Missing evidence → UNRESOLVED | Reconciliation | `test_slice2_intake_and_reconciliation.py` | Yes | No |
| Deterministic canonical bytes | Canonicalization | `test_canonicalization_vectors.py` | CJCS vectors | No |
| Same evidence → same outcome | Engine | `test_golden_corpus.py` | Golden Corpus | No |
| Provenance traceability | Provenance | `test_slice2_intake_and_reconciliation.py` | — | No |
| Receipt/result consistency | Receipt | `test_slice1_evidence_contract.py` | — | No |
| Tampering → INVALID | Verifier | `test_verifier.py` | Tampered Samples | No |
| Tax Correctness → NOT DETERMINED | Verifier/UI | `test_verifier.py` | — | No |
| Unsupported semantics don't silently PASS | Engine | `test_atdd_l2_preflight_and_findings.py` | — | No |
