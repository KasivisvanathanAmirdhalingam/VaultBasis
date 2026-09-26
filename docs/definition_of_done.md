# VaultBasis — Matured Definition of Done (DoD)

> **Document Version**: v2.0.0-INDUSTRIAL  
> **Status**: NORMATIVE / MANDATORY GATING POLICY  
> **Scope**: All Vertical Slices & Production Release Gates for MMP-1  
> **Authority**: PRD §41 (Acceptance Criteria), §42 (Definition of Done), §44 (Evidence & Cryptography), §71 (Product Quality Scorecard — 9/10 Gate)  

---

## 1. Governance Principles & Invariant Baselines

VaultBasis is an **independent outcome-verification and assurance edge**. In financial reconciliation, an undetected inaccuracy, a silent presumption, or a floating-point rounding artifact destroys institutional credibility. 

A feature, module, or vertical slice is **DONE** only when implementation, mathematical proofs, cryptographic evidence, test validation, human-agency UI, and failure behaviors are fully aligned.

### The Five Granite Invariants (Never Compromised)

1. **Exact Decimal Arithmetic (PRD §15.1)**:
   - Binary floating point (`float`, `double`) is strictly forbidden for financial values.
   - All amounts (proceeds, cost basis, gain/loss, variances, fractional quantities) must be stored, computed, and serialized as exact `Decimal` or atomic integer strings.
2. **Unknown is a First-Class State (PRD §2.2, §15.8, §15.9)**:
   - Missing basis, price, acquisition date, or asset precision must explicitly produce `UNRESOLVED` states.
   - Missing values **never** default to `$0.00`, empty strings, or estimated guesses.
   - The outcome state becomes `UNRESOLVED_DATA` if missing facts materially affect the financial conclusion.
3. **Zero Token Bleed & Zero Egress (PRD §2.4, §21)**:
   - No customer transaction rows, cost basis numbers, or evidence payloads leave the local customer environment.
   - All deterministic computation runs on local CPU. Cloud inference and telemetry leakage are strictly blocked.
4. **Evidence Contract Normative Precedence (PRD §6.5, §13.2)**:
   - The Evidence Contract v0.1 (`receipt-v0.1.json`, `canonicalization-v0.1.md`, `signing-v0.1.md`, `verification-v0.1.md`) is normative.
   - No application layer may redefine receipt schemas or canonicalization rules.
5. **Fail-Closed Safety (PRD §41 AC-04)**:
   - Corrupted, malformed, or schema-drifted inputs must fail closed to `UNSUPPORTED` or `REJECTED`. Silent fallback or optimistic recovery is prohibited.

---

## 2. Six-Layer Definition of Done (Evaluation Framework)

Every engineering deliverable must pass verification across all six dimensions:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      SIX-LAYER DoD ARCHITECTURE                        │
├────────────────────────────────────────────────────────────────────────┤
│ Layer 1: Regulatory & Tax Domain Alignment (IRC §6045, 1099-DA, Scope) │
├────────────────────────────────────────────────────────────────────────┤
│ Layer 2: Accounting & Deterministic Arithmetic (Exact Decimal, Invariants)│
├────────────────────────────────────────────────────────────────────────┤
│ Layer 3: Security & Zero-Egress Privacy (POSIX 0600, Airgap, SAST)     │
├────────────────────────────────────────────────────────────────────────┤
│ Layer 4: Cryptographic Evidence & Verification (RFC 8785, Ed25519, CLI)│
├────────────────────────────────────────────────────────────────────────┤
│ Layer 5: Industrial UX & Human Agency (3 Screens, No Fake Badges)      │
├────────────────────────────────────────────────────────────────────────┤
│ Layer 6: Operational & Left-Shift Pipeline (CI/CD, 100% Tests, Docker) │
└────────────────────────────────────────────────────────────────────────┘
```

### Layer 1: Regulatory & Tax Domain Alignment
- [x] **Source Authority Recorded**: Regulatory source (e.g., IRC §6045, 2026 Form 1099-DA, IRS Notice 2024-56, Rev. Proc. 2024-28) is explicitly referenced in rulesets.
- [x] **Tax Year Distinction**: Distinct rules applied for 2025 transition reporting (gross proceeds mandatory; basis non-covered) versus 2026+ covered reporting.
- [x] **Reporting Scope Difference**: Omission of basis on 1099-DA Box 2 is classified as `REPORTING_SCOPE_DIFFERENCE`, never mislabeled as a "broker error."
- [x] **No Liability Immunity Claims**: Marketing and UI surfaces carry statutory limitation disclaimers (PRD §27.4, §37.3); forbidden phrases ("IRS certified," "audit-proof," "zero risk") are strictly prohibited.

### Layer 2: Accounting & Deterministic Arithmetic
- [x] **Zero Floating-Point**: 100% of financial comparisons use `Decimal` with explicit rounding modes and tolerances (`0.01` USD).
- [x] **13 Bounded Outcome States**: Engine maps exclusively into one of the 13 defined states: `MATCHED`, `PROCEEDS_DIFFERENCE`, `BASIS_DIFFERENCE`, `ACQUISITION_DATE_DIFFERENCE`, `DISPOSITION_DATE_DIFFERENCE`, `MISSING_FROM_1099DA`, `MISSING_FROM_LEDGER`, `AMBIGUOUS_MATCH`, `AGGREGATED_LINE`, `TRANSFER_RELATED`, `REPORTING_SCOPE_DIFFERENCE`, `SOURCE_ERROR_SUSPECTED`, `UNRESOLVED_DATA`.
- [x] **Conservation of Lots**: Asset quantities and proceeds are conserved across matched pairs; no silent lot creation or deletion.
- [x] **Deficit & Missing Price Invariants**: Negative balances or unavailable prices produce `UNRESOLVED_DATA` with explicit itemized reason codes.

### Layer 3: Security & Zero-Egress Privacy
- [x] **POSIX 0600 Key Permissions**: Local Ed25519 private keys stored on disk with file mode `0600` (readable/writable only by owner process).
- [x] **Zero Transaction Egress**: Packet capture or network audit proves zero outbound HTTP/DNS traffic containing customer transaction or evidence payloads.
- [x] **Local Persistence Boundary**: Database (SQLite) operates in WAL mode on local customer storage; zero cloud sync.
- [x] **Static Security Scans**: Clean results from SAST, secret leak scanners, and dependency vulnerability audits (0 critical, 0 high).

### Layer 4: Cryptographic Evidence & Verification
- [x] **Strict Schema Conformance**: Receipt documents validate against normative Draft-07 JSON Schema `schemas/receipt/receipt-v0.1.json`.
- [x] **Deterministic Canonicalization**: Serialization adheres byte-for-byte to RFC 8785 (JCS) with lexicographically sorted keys, UTF-8 normalization, and signature field exclusion.
- [x] **Ed25519 Signature Validity**: Receipts carry verifiable Ed25519 signatures over the 32-byte SHA-256 canonical digest.
- [x] **Signer Key Fingerprinting**: `signer_key_id` exactly matches `SHA-256(RawPublicKeyBytes)`.
- [x] **Offline Independent Verifier**: Standalone CLI (`apps/verifier/verify_receipt.py`) verifies receipts on clean machines with zero network access and zero external services.
- [x] **Tamper Rejection Proof**: Modifying any financial value by `$0.01` or changing the outcome state immediately causes verification failure.

### Layer 5: Industrial UX & Human Agency
- [x] **Three-Screen Minimalist Scope**: Interface strictly bounded to Screen 1 (Case List), Screen 2 (Case Review), and Screen 3 (Receipt / Export).
- [x] **Control Instrument Aesthetics**: Minimalist, professional, dark-mode styling with clear typography and zero decorative fluff.
- [x] **No Misleading Green Badges**: Unresolved or scope-divergent cases are highlighted with amber/warning badges; green badges are reserved exclusively for verified `MATCHED` states.
- [x] **Shallow Provenance Links**: Every difference and matched line exposes clickable provenance links to the exact source row and content SHA-256 digest.
- [x] **One-Click Evidence Bundle**: Customer can download a self-contained ZIP bundle containing the signed receipt, source documents, normative schema, and standalone verifier CLI.

### Layer 6: Operational & Left-Shift Pipeline
- [x] **Automated Pre-Commit Script**: `scripts/validate_before_commit.sh` runs syntax checks, schema checks, pytest unit tests, golden verifier tests, and security audits; exits 0 only on all gates green.
- [x] **Industrial Launch Script**: `scripts/launch.sh` starts the service, performs automated port conflict resolution, healthcheck polling, and graceful signal handling (`SIGINT`/`SIGTERM`).
- [x] **Idempotency**: All ingestion and case operations satisfy PRD §62.2 idempotency constraints.
- [x] **100% Test Pass**: All automated tests execute cleanly with zero errors or unhandled exceptions.

---

## 3. Seven Blocking Preview Gates (Acceptance Criteria §41)

Before any release candidate or design-partner preview is certified, the Seven Blocking Gates must be evaluated:

| Gate | Criterion | Metric / Test | Current Status |
| :--- | :--- | :--- | :--- |
| **AC-01** | Edge starts & ingests inputs | Docker/process starts; 1099-DA and Koinly CSV ingested; case ID assigned | **GREEN** |
| **AC-02** | Bounded reconciliation produced | Output maps deterministically into 1 of 13 declared outcome states | **GREEN** |
| **AC-03** | Unknown values preserved | Missing basis/date remains `UNRESOLVED`; never converted to `$0.00` | **GREEN** |
| **AC-04** | Malformed input fails safely | Truncated/corrupted inputs rejected with explicit error; zero crashes | **GREEN** |
| **AC-05** | Signed Outcome Receipt emitted | Emits canonical receipt conforming to Evidence Contract v0.1 signed with Ed25519 | **GREEN** |
| **AC-06** | Independent verifier confirms receipt | Offline CLI verifies signature, digest, and schema on clean machine | **GREEN** |
| **AC-07** | Zero transaction-data egress | Zero outbound packets carrying transaction/evidence payloads | **GREEN** |

---

## 4. Slice Sign-Off Protocol

After completing any slice:
1. Run `bash scripts/validate_before_commit.sh`.
2. Verify all tests pass with exit code 0.
3. Verify live operational state via `scripts/launch.sh`.
4. Update `docs/master_tasks_ledger.md` task statuses.
5. Update `docs/audit/status.md` with latest verification evidence.
