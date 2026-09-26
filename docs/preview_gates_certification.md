# VaultBasis — Seven Blocking Preview Gates Certification

> **Release Target**: v0.1.0-preview (MMP-1 Design-Partner Preview)  
> **Evaluation Date**: 2026-09-26  
> **Authority**: PRD §41 (Acceptance Criteria), §71 (Product Quality Scorecard)  
> **Sign-Off Status**: **ALL 7 GATES CERTIFIED GREEN**  

---

## Formal Gate Certification Matrix

### Gate 1: AC-01 — Edge starts and accepts input
* **Requirement**: In a supported local environment, VaultBasis Edge boots deterministically, accepts supported 1099-DA and Koinly CSV inputs, and creates a local case ID.
* **Test Verification**: `tests/quality/bdd/test_bdd_acceptance_gates.py::test_bdd_ac01_edge_starts_and_accepts_input`
* **DoD Standard**: HTTP 200/201 on case creation, non-zero parsed rows, strict schema classification.
* **Disposition**: **CERTIFIED GREEN**

### Gate 2: AC-02 — Reconciliation produces a bounded result
* **Requirement**: When valid inputs are provided, reconciliation maps deterministically into one of the 13 declared outcome states and never invents accounting behavior.
* **Test Verification**: `tests/quality/bdd/test_bdd_acceptance_gates.py::test_bdd_ac02_bounded_reconciliation_result`
* **DoD Standard**: Exact Decimal arithmetic with $0.01 tolerance; discrete outcome mapping.
* **Disposition**: **CERTIFIED GREEN**

### Gate 3: AC-03 — Unknown states do not become zero
* **Requirement**: Missing basis, date, quantity, or price remains explicitly unresolved; it is not replaced by zero, empty text, or assumed values.
* **Test Verification**: `tests/quality/bdd/test_bdd_acceptance_gates.py::test_bdd_ac03_unknown_states_do_not_become_zero`
* **DoD Standard**: `is_unresolved = True`, `unresolved_reason` tracked, case state maps to `UNRESOLVED_DATA` when material.
* **Disposition**: **CERTIFIED GREEN**

### Gate 4: AC-04 — Malformed input fails safely
* **Requirement**: Corrupted, truncated, or schema-drifted inputs fail closed with explicit typed errors; zero silent crashes or corrupt financial outputs.
* **Test Verification**: `tests/quality/bdd/test_bdd_acceptance_gates.py::test_bdd_ac04_malformed_input_fails_safely`
* **DoD Standard**: Typed `ValueError` / HTTP 422 returned; no unhandled exceptions.
* **Disposition**: **CERTIFIED GREEN**

### Gate 5: AC-05 — Receipt is generated and signed
* **Requirement**: Completed bounded case produces an Outcome Receipt conforming to Draft-07 JSON Schema `receipt-v0.1.json`, carrying an Ed25519 signature from local installation key.
* **Test Verification**: `tests/quality/bdd/test_bdd_acceptance_gates.py::test_bdd_ac05_receipt_is_generated_and_signed`
* **DoD Standard**: 128-char hex signature, 64-char hex public key, 64-char key fingerprint.
* **Disposition**: **CERTIFIED GREEN**

### Gate 6: AC-06 — Independent verifier confirms receipt
* **Requirement**: Independent verifier verifies signature, RFC 8785 canonical digest, and declared state on a clean machine without network connectivity.
* **Test Verification**: `tests/quality/bdd/test_bdd_acceptance_gates.py::test_bdd_ac06_independent_verifier_confirms_receipt`
* **DoD Standard**: `verify_outcome_receipt` returns `is_valid: True` and passes golden verification test.
* **Disposition**: **CERTIFIED GREEN**

### Gate 7: AC-07 — No transaction-data egress
* **Requirement**: No customer transaction rows, cost basis numbers, or evidence payloads leave the local customer Edge environment.
* **Test Verification**: `tests/quality/bdd/test_bdd_acceptance_gates.py::test_bdd_ac07_no_transaction_data_egress`
* **DoD Standard**: Service binds exclusively to local interface; `egress_policy: STRICT_LOCAL_ONLY`.
* **Disposition**: **CERTIFIED GREEN**

---

## Certification Conclusion

All seven blocking gates defined in PRD §41 have passed verification. VaultBasis Edge v0.1.0-preview meets the granite-standard Definition of Done for customer design-partner deployments.
