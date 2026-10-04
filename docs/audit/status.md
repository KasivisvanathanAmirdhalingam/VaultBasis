# VaultBasis — Status Under Audit

> **System**: VaultBasis Edge (Independent Outcome Verification Edge)  
> **Release Target**: v0.1.0-preview (MMP-1 Design-Partner Preview)  
> **Audit Date**: 2026-09-26  
> **Evaluation Standard**: Granite-Grade Industrial Assurance (PRD §41, §42, §44, §71)  
> **Overall Audit Disposition**: **ALL SEVEN PREVIEW GATES GREEN (CERTIFIED FOR DESIGN-PARTNER PREVIEW)**  

---

## 1. Executive Summary

This document certifies the current audit and verification status of VaultBasis Edge v0.1.0-preview against the Product Requirements Document (PRD v26.1). 

VaultBasis functions as an **independent outcome-verification edge** operating inside the customer's declared trust boundary. It independently verifies Form 1099-DA broker reporting against tax software (Koinly) outputs and generates a cryptographically signed, portable **Outcome Receipt** that any third party can verify offline without contacting VaultBasis servers.

---

## 2. Seven Blocking Preview Gates Audit (§41)

All seven blocking preview gates have been audited against concrete implementation code and test evidence:

| Gate | Title | Requirement | Verification Evidence | Audit Status |
| :--- | :--- | :--- | :--- | :--- |
| **AC-01** | **Edge Starts & Ingests** | Docker/process starts; ingests Form 1099-DA and Koinly CSV; generates unique Case ID | `edge/api/app.py` boots cleanly; `POST /api/cases` and `POST /api/cases/{id}/sources` verified in `test_fastapi_e2e_endpoints` | **PASS (GREEN)** |
| **AC-02** | **Bounded Reconciliation** | Produces one of 13 declared outcome states; exact Decimal math; no invented accounting | `edge/assurance/reconciliation_engine.py` maps differences into 13 discrete states; verified in `test_deterministic_reconciliation_basis_difference` | **PASS (GREEN)** |
| **AC-03** | **Unknown Preserved** | Missing basis, date, or price remains explicitly `UNRESOLVED`; never replaced by `$0.00` | Invariant verified in `test_unknown_basis_preservation_not_zero`; `unresolved_reason = "BASIS_UNAVAILABLE"` explicitly tracked | **PASS (GREEN)** |
| **AC-04** | **Fail-Closed Safety** | Malformed, truncated, or schema-drifted inputs fail closed; zero silent crashes | `edge/connectors/validator.py` enforces strict validation; invalid headers raise typed `ValueError` returning HTTP 422 | **PASS (GREEN)** |
| **AC-05** | **Signed Outcome Receipt** | Emits canonical receipt conforming to Evidence Contract v0.1 signed with local Ed25519 key | Draft-07 schema validated against `schemas/receipt/receipt-v0.1.json`; Ed25519 signature over SHA-256 digest in `test_slice1_end_to_end_receipt_flow` | **PASS (GREEN)** |
| **AC-06** | **Offline Verifier Pass** | Independent verifier confirms signature and canonical digest on clean machine without network | Standalone CLI `apps/verifier/verify_receipt.py` executes offline on golden fixture with `REPORT — PASS` | **PASS (GREEN)** |
| **AC-07** | **Zero Egress** | Zero outbound network packets containing customer transaction rows or evidence payloads | Local SQLite persistence in `data/vaultbasis.db`; local FastAPI service binds to `127.0.0.1`; zero remote telemetry calls | **PASS (GREEN)** |

---

## 3. Cryptographic Security Audit

### 3.1 Key Management & Permissions
- **Algorithm**: Ed25519 (RFC 8032) using OS CSPRNG (`os.urandom`).
- **Storage**: Local filesystem (`data/keys/installation_ed25519.key`).
- **File Permissions**: Enforced POSIX mode `0600` (read/write only by owner process). Verified in `test_key_generation_and_permissions`.
- **Key Fingerprint**: `signer_key_id` computed as `SHA-256(RawPublicKeyBytes)`. Verified match on every signing and verification run.

### 3.2 Canonicalization Integrity
- **Standard**: RFC 8785 (JSON Canonicalization Scheme - JCS) implemented in `edge/receipts/canonicalizer.py`.
- **Rules**: UTF-8 without BOM, lexicographical key sorting, strict Decimal string formatting, explicit nulls, exclusion of signature property.
- **Determinism**: Verified in `test_canonicalization_determinism` (identical byte sequences generated regardless of dict insertion order).

### 3.3 Tamper Rejection Proof
- **Financial Alteration**: Modifying variance from `$4200.00` to `$4200.01` causes instant cryptographic signature failure (`FAIL_SIGNATURE_TAMPERED`).
- **State Falsification**: Modifying outcome state from `BASIS_DIFFERENCE` to `MATCHED` causes instant rejection.
- **Key Substitution**: Replacing public key with unauthorized key causes key fingerprint mismatch failure.
- **Evidence**: Verified in `test_tamper_detection_financial_value` and `test_tamper_detection_outcome_state`.

---

## 4. Regulatory & Legal Positioning Audit

| Dimension | Standard Required (PRD §27, §37) | Implementation Status |
| :--- | :--- | :--- |
| **Form 1099-DA Scope** | Distinguish 2025 non-covered basis from 2026+ mandatory covered basis | `edge/assurance/reconciliation_engine.py` classifies Box 2 omission as `REPORTING_SCOPE_DIFFERENCE`, avoiding false broker error claims |
| **Safe Harbor (Rev. Proc. 2024-28)** | Terminology bounded to "Eligibility Assessment" and "Allocation Record" | No invented claims ("IRS Certified Report" strictly avoided) |
| **No Immunity Claims** | Avoid "audit-proof," "zero risk," "guaranteed compliant" | Full statutory limitation notices rendered on all CLI, API, and Web UI surfaces |

---

## 5. Software Quality & Test Suite Audit

Automated pre-commit validation pipeline executes via `scripts/validate_before_commit.sh` delegating to `scripts/run_validation_gates.py`.

```
=============================================================================================================================================================================================================
                                                                            VAULTBASIS — INDUSTRIAL VALIDATION GATES AUDIT REPORT                                                                            
                                                    Timestamp: 2026-10-04T21:29:30Z | Standard: Left-Shift Maximum (PRD §64, §71) | Enforce Level: Granite                                                   
+===========+============================+==========================+==========================================+==========================================+==========+============================================+
| GATE ID   | CATEGORY                   | METRICS / NUMBERS        | EXPECTED RESULT                          | ACTUAL RESULT                            | STATUS   | POTENTIAL CAUSE / DIAGNOSTIC               |
+===========+============================+==========================+==========================================+==========================================+==========+============================================+
| GATE-01   | Static Code Quality        | 65 files compiled        | 0 syntax or AST errors                   | 0 errors in 65 files (100% clean)        | [PASS]  | N/A (AST parsed cleanly)                   |
| GATE-02   | Normative Contract         | 24 required / 25 prop... | Draft-07 compliant schema with >= 23 ... | Draft-07 valid (24 required / 25 props)  | [PASS]  | N/A (Schema normative and compliant)       |
| GATE-03   | Domain Invariants (DDD)    | 11/11 tests passed       | All domain aggregate invariants hold     | 11/11 passed (100% green)                | [PASS]  | N/A (All suite invariants hold)            |
| GATE-04   | Precision Math & Crypto... | 14/14 tests passed       | Zero float drift & valid Ed25519 sign... | 14/14 passed (100% green)                | [PASS]  | N/A (All suite invariants hold)            |
| GATE-05   | Acceptance Criteria (BDD)  | 17/17 tests passed       | 100% pass on bounded outcomes, air-gap   | 17/17 passed (100% green)                | [PASS]  | N/A (All suite invariants hold)            |
| GATE-06   | User Journeys (ATDD)       | 17/17 tests passed       | Multi-lot, provenance & audit journey... | 17/17 passed (100% green)                | [PASS]  | N/A (All suite invariants hold)            |
| GATE-07   | Parser Invariants (Unit)   | 173/173 tests passed     | Lossless parsing across broker CSV fo... | 173/173 passed (100% green)              | [PASS]  | N/A (All suite invariants hold)            |
| GATE-08   | Production Navigation      | 71/71 tests passed       | 100% working links, no anchor occlusion  | 71/71 passed (100% green)                | [PASS]  | N/A (All suite invariants hold)            |
| GATE-09   | Independent Verification   | 2/2 fixtures verified    | Valid=PASS (exit 0) | Tampered=FAIL (... | Valid=PASS (exit 0) | Tampered=FAIL (... | [PASS]  | N/A (Cryptographic & schema verificatio... |
| GATE-10   | Production Build           | 15 distribution files    | Clean build, zero egress/secret leaks... | Bundle built cleanly (15 artifacts, 0... | [PASS]  | N/A (Public bundle isolated and audited)   |
| GATE-11   | Security & Air-Gap         | 1 keyfiles audited (0... | All Ed25519 private keys strictly chm... | All private keys enforce 0o600 POSIX ... | [PASS]  | N/A (Security boundary intact)             |
+-----------+----------------------------+--------------------------+------------------------------------------+------------------------------------------+----------+--------------------------------------------+

CATEGORICAL EXECUTION BREAKDOWN & METRICS:
  • Total Validation Gates   : 11
  • Gates Passed (Green)     : 11
  • Gates Failed (Red)       : 0
  • Gates Warning (Yellow)   : 0
  • Total Automated Tests    : 376 tests across ATDD, BDD, DDD, TDD, Prod, Unit
  • Total Execution Time     : 7.13s
  • Pipeline Pass Rate       : 100.0%
+===========+============================+==========================+==========================================+==========================================+==========+============================================+
✓ ALL PRE-COMMIT GATES SATISFIED — ZERO DRIFT — READY FOR PUSH TO REMOTE.
```

---

## 6. Live Runtime Endpoints Audit

Live service verified via `scripts/launch.sh` on `http://127.0.0.1:8000`:

| Surface | Path / Port | Verified Capabilities | Audit Status |
| :--- | :--- | :--- | :--- |
| **Health API** | `GET /api/health` | Service status, key ID, zero-egress policy confirmation | **OPERATIONAL** |
| **Customer Dashboard** | `GET /` | Screen 1 (Case List), Screen 2 (Case Review), Screen 3 (Receipt/Export) | **OPERATIONAL** |
| **Public Verifier** | `GET /verifier` | Standalone browser drag-and-drop verification with zero server dependencies | **OPERATIONAL** |
| **Case Ingestion API** | `POST /api/cases/{id}/sources` | 1099-DA, Koinly CSV, VaultBasis fallback CSV auto-detection & SHA-256 hashing | **OPERATIONAL** |
| **Reconciliation API** | `POST /api/cases/{id}/reconcile` | Deterministic comparison, 13 outcome states, Ed25519 signed receipt emission | **OPERATIONAL** |
| **Evidence Export API**| `GET /api/cases/{id}/export` | Self-contained ZIP bundle (receipt, source evidence, offline verifier CLI) | **OPERATIONAL** |

---

## 7. Known Audit Scope Boundaries (MMP-2 Roadmap)

The following capabilities are deliberately excluded from MMP-1 per PRD §6.2 and are reserved for MMP-2:
1. **Local LLM & RAG Integration**: MMP-1 core is 100% deterministic arithmetic on CPU; LLM explanations deferred to MMP-2.
2. **Read-Only MCP Server**: Deferred to MMP-2 (§12).
3. **Enterprise PKI Attestation**: MMP-1 relies on per-installation keypairs; customer PKI / HSM integration deferred to MMP-2.
4. **Universal Exchange Webhooks**: Ingestion in MMP-1 is bounded to Form 1099-DA, Koinly CSV, and VaultBasis CSV fallback.
