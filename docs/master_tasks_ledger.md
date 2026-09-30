# VaultBasis — Master Tasks Ledger (MMP-1 Scope)

> Every task now follows [VB-GOV-001](task_execution_standard.md); full implementation identities and historical attribution gaps are indexed in [task registry](task_registry.json).

> Scope clarification (2026-09-30): retain this ledger as historical implementation evidence. The [current roadmap](roadmap/VAULTBASIS_PRODUCT_ROADMAP.md) and [audit index](audit/README.md) govern current/future planning. Commercialization, billing, analytics and future intelligence/workflows are not authorized MMP-1.1 stabilization work. Historical PASS language is not current release qualification.

> **Document Version**: v1.0.0-MMP1  
> **PRD Source**: `VaultBasis — Product Requirements Document v26.1 (v26.0 Reference)`  
> **Status**: APPROVED EXECUTION CONTROL PLANE  
> **Standard**: Granite-Grade / Left-Shift Maximum / Zero-Drift / Deterministic Assurance  

---

## 1. Executive Summary & MMP-1 Scope Definition

VaultBasis is an **independent outcome-verification and assurance edge** operating inside the customer's declared trust boundary. It independently compares, recomputes, explains, and evidences consequential financial outputs without requiring sensitive transaction data to leave customer premises.

The first proving ground is **U.S. Digital-Asset Financial & Tax Reconciliation (Tax Year 2025/2026 Form 1099-DA reporting vs. Tax Software Output)**.

### 1.1 The "Need of the Hour" Problem
Brokers, exchanges, and tax preparation systems produce diverging gain/loss calculations, cost basis treatments, and proceeds reports. With the rollout of Form 1099-DA (gross proceeds for 2025 sales; basis reporting phased), CPAs and filers face massive review backlogs, scope discrepancies, and unverified broker claims. VaultBasis provides the missing deterministic verification layer that checks the claim and produces a portable, cryptographically signed **Outcome Receipt** that any third party can independently verify offline.

### 1.2 MMP-1 Bounded Scope (Exactly 5 Workstreams)

| Workstream | MMP-1 Capability | Scope Boundary |
| :--- | :--- | :--- |
| **WS-1: Edge Runtime & API** | Single Docker/OCI local runtime with local FastAPI service | No Kubernetes, private VPC orchestration, or multi-tenant cloud in preview |
| **WS-2: Intake & Parsers** | Form 1099-DA PDF/JSON + Koinly Capital Gains CSV (with VaultBasis CSV fallback) | No broad exchange API connectors, on-chain scraping, DeFi, or NFT protocols |
| **WS-3: Deterministic Assurance** | Canonicalization, bounded reconciliation, 13 outcome states, exact decimal math | No universal FIFO reconstruction engine, automated filing, or tax advice |
| **WS-4: Evidence & Receipts** | Shallow provenance, Evidence Contract v0.1, signed Ed25519 Outcome Receipt | No deep multi-party attestation mesh, zero-knowledge proofs, or blockchain gas |
| **WS-5: Verification & UI** | 3-Screen Local Dashboard, Independent Offline Verifier CLI/Web, Export Bundle | No complex user management, billing, notifications, or settings console |

### 1.3 Strict MMP-1 Non-Goals & Exclusions
- **Zero Cloud Inference / Zero Token Bleed**: No remote transmission of customer transaction rows or tax data.
- **No LLM / RAG / MCP in MMP-1 Core**: Deferred to MMP-2. Interfaces are stubbed/scaffolded only.
- **No Automated Legal/Tax Advice**: VaultBasis provides evidence of comparison; it does not issue tax advice or filing instructions.
- **No Floating Point Arithmetic**: 100% exact integer / decimal arithmetic.
- **Unknown is a First-Class State**: Missing prices, basis, or dates remain `UNRESOLVED` and never default to zero.

---

## 2. Mandatory Evidence Contract Dependency Order

Per PRD §6.5, the engineering implementation order is non-negotiable:
1. **Evidence Contract v0.1** (Normative schema, canonicalization rules, signing spec, verification spec)
2. **Independent Verifier** (Clean-machine offline validation of signature, digest, and schema)
3. **Receipt Signer** (Local per-installation Ed25519 signing engine)
4. **Canonical Case Model** (Internal representation of assets, lots, sources, and transactions)
5. **Reconciliation Engine** (Deterministic difference classification and outcome state machine)
6. **Edge API** (Local REST endpoints: cases, sources, reconcile, receipt, verify)
7. **Three-Screen UI & Export Bundle** (Case List, Case Review, Receipt/Export screens)

---

## 3. Seven Blocking Preview Gates (Acceptance Criteria)

| Gate ID | Gate Name | PRD Criterion | Blocking Condition |
| :--- | :--- | :--- | :--- |
| **AC-01** | Edge Starts & Ingests | Edge starts deterministically via Docker; ingests 1099-DA and Koinly CSV; generates unique case ID | Failure to boot or parse supported inputs |
| **AC-02** | Bounded Reconciliation | Reconciles inputs into one of 13 declared outcome states without inventing accounting behavior | Undefined state or floating point drift |
| **AC-03** | Unknown Values Preserved | Missing basis, date, price, or precision remains explicitly `UNRESOLVED`; never replaced by `$0.00` | Any silent zeroing or assumed value |
| **AC-04** | Fail-Closed Input Safety | Malformed, truncated, or malicious schema input fails safely to `UNSUPPORTED`/`REJECTED` | Unhandled crash or silent corrupt output |
| **AC-05** | Signed Outcome Receipt | Emits canonical receipt conforming to Evidence Contract v0.1 signed with local Ed25519 key | Schema mismatch or invalid signature |
| **AC-06** | Independent Verifier Pass | Receipt verified offline on clean machine without network, LLM, or cloud dependencies | Verifier fails or requires remote ping |
| **AC-07** | Zero Transaction Egress | Packet capture / network audit proves zero transaction rows or evidence payloads leave Edge | Any network payload containing case data |

---

## 4. Vertical Slice Roadmap (MMP-1)

```
[Slice 1: Thinnest Vertical Slice]
Evidence Contract v0.1 ───> Canonical Serialization ───> Keygen & Signer ───> Offline Verifier CLI
         │
         ▼
[Slice 2: Intake & Canonical Models]
1099-DA Parser + Koinly CSV Adapter ───> SHA-256 Source Hashing ───> Canonical Transaction Model
         │
         ▼
[Slice 3: Deterministic Reconciliation]
Exact Decimal Engine ───> 13 Outcome States ───> Difference Classifier ───> Shallow Provenance
         │
         ▼
[Slice 4: Edge Runtime & Local REST API]
FastAPI Local Daemon ───> SQLite Case Store ───> Egress Barrier ───> Idempotent Endpoints
         │
         ▼
[Slice 5: Three-Screen Local Dashboard]
Screen 1 (Case List) ───> Screen 2 (Case Review) ───> Screen 3 (Receipt/Export Bundle)
         │
         ▼
[Slice 6: Public Web Verifier & Marketing Surface]
Client-side Web Verifier ───> Landing Page & Sample Receipt ───> Trust Center Blueprint
         │
         ▼
[Slice 7: Left-Shift QA & Production Readiness]
Golden Test Suite ───> Fuzz Suite ───> Zero-Egress Net Audit ───> 7 Gates Green Sign-Off
         │
         ▼
[Slice 8: Incremental Cloud Infrastructure & Vercel Production Deployment]
vercel.json & Packager ───> Localhost Airgap Bridge ───> WebCrypto Verifier ───> Prod Deploy Gates
```

---

## 5. Master Granular Tasks Ledger

### Workstream 1: Governance & Evidence Contract Foundation (Slice 1)

| Task ID | Component | Task Description | PRD Ref | Priority | DoD Exit Criterion | Status | Commit ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GOV-01** | Evidence Contract | Draft normative JSON Schema `schemas/receipt/receipt-v0.1.json` specifying all 23 core fields | §13.2, §13.3 | P0 | Strict JSON Schema draft-07 validated | **COMPLETED** | `b5a3e5f` |
| **GOV-02** | Canonicalization | Define `schemas/receipt/canonicalization-v0.1.md` (UTF-8, sorted keys, strict decimal strings, UTC ISO 8601) | §44.1, §13.2 | P0 | Deterministic byte-for-byte serialization spec | **COMPLETED** | `b5a3e5f` |
| **GOV-03** | Signing Spec | Define `schemas/receipt/signing-v0.1.md` for Ed25519 installation key signing over SHA-256 digest | §13.5, §44.3 | P0 | Exact signing and signature verification algorithm | **COMPLETED** | `b5a3e5f` |
| **GOV-04** | Verifier Spec | Define `schemas/receipt/verification-v0.1.md` governing offline, zero-network verification rules | §13.8, §44.7 | P0 | Verifier pass/fail rules & limitation statements | **COMPLETED** | `b5a3e5f` |
| **GOV-05** | Vocabulary Spec | Formalize 13 reconciliation states, 5 assurance levels, and authority classes | §14.3, §7.5 | P0 | Normative enums documented with zero ambiguity | **COMPLETED** | `b5a3e5f` |
| **GOV-06** | Golden Fixtures | Generate initial valid and tampered golden receipts for test automation | §43.2, §51.3 | P0 | At least 3 valid + 3 invalid test fixtures committed | **COMPLETED** | `b5a3e5f` |

### Workstream 2: Core Cryptographic & Verifier Engine (Slice 1)

| Task ID | Component | Task Description | PRD Ref | Priority | DoD Exit Criterion | Status | Commit ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ENG-10A**| Key Management | Implement local Ed25519 keypair generation and secure file-permission storage | §13.5, §23.2 | P0 | Key generated with 0600 permissions, unique installation ID | **COMPLETED** | `b5a3e5f` |
| **ENG-10B**| Canonical Serializer| Implement deterministic JSON canonicalizer conforming to `canonicalization-v0.1.md` | §44.1, §44.5 | P0 | 100% deterministic SHA-256 hash across runs | **COMPLETED** | `b5a3e5f` |
| **ENG-10C**| Receipt Signer | Implement receipt builder and signer producing `receipt-v0.1.json` | §13.3, §13.5 | P0 | Generates compliant signed receipt document | **COMPLETED** | `b5a3e5f` |
| **ENG-11A**| Offline Verifier CLI| Build standalone zero-dependency Python/CLI verifier checking signature, schema, hash | §13.8, §34.3 | P0 | CLI validates valid receipt as PASS, tampered as FAIL | **COMPLETED** | `b5a3e5f` |
| **ENG-11B**| Clean-Machine Test | Verify offline verifier works in disconnected container with no network access | §41 (AC-06) | P0 | 100% pass on clean offline environment | **COMPLETED** | `b5a3e5f` |

### Workstream 3: Intake Parsers & Canonical Data Models (Slice 2)

| Task ID | Component | Task Description | PRD Ref | Priority | DoD Exit Criterion | Status | Commit ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ENG-05A**| Canonical Schema | Implement `CanonicalTransaction` and `CanonicalCase` data models with Decimal math | §17.1, §17.2 | P0 | Pydantic v2 / strict typed schemas with unit tests | **COMPLETED** | `b5a3e5f` |
| **ENG-06A**| Source Hasher | Implement streaming SHA-256 hasher for ingested files with metadata capture | §15.5, §17.1 | P0 | Repeatable SHA-256 digest + byte length tracking | **COMPLETED** | `b5a3e5f` |
| **ENG-03A**| 1099-DA Parser | Build parser for Form 1099-DA representation (proceeds, basis, dates, box 2 indicator) | §14.1, §14.2 | P0 | Golden fixtures for 2025/2026 reporting formats pass | **COMPLETED** | `b5a3e5f` |
| **ENG-04A**| Koinly CSV Adapter | Build adapter for Koinly Capital Gains Report CSV with version detection | §6.4 (A) | P0 | Accurately extracts asset, dates, costs, proceeds, gains | **COMPLETED** | `b5a3e5f` |
| **ENG-04B**| Fallback Adapter | Implement generic `VaultBasis Reconciliation CSV v0.1` fallback adapter | §6.4 (A) | P0 | Documented CSV specification + parser tests | **COMPLETED** | `b5a3e5f` |
| **ENG-03B**| Fail-Closed Intake | Implement malformed input validation rejecting invalid headers or corrupted rows | §41 (AC-04) | P0 | Graceful rejection with explicit error log; zero crashes | **COMPLETED** | `b5a3e5f` |

### Workstream 4: Deterministic Assurance & Reconciliation Engine (Slice 3)

| Task ID | Component | Task Description | PRD Ref | Priority | DoD Exit Criterion | Status | Commit ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ENG-07A**| Bounded Matcher | Implement transaction matching hierarchy (date proximity, asset, quantity, proceeds) | §15.7, §15.4 | P0 | Matcher produces deterministic 1-to-1 or 1-to-N links | **COMPLETED** | `b5a3e5f` |
| **ENG-08A**| Diff Classifier | Build deterministic difference classifier implementing 13 outcome states | §14.3, §15.1 | P0 | Correctly classifies basis diff, proceeds diff, scope diff | **COMPLETED** | `b5a3e5f` |
| **ENG-08B**| Unknown Handler | Implement explicit `UNRESOLVED` state tracking (missing basis/date/price never becomes $0) | §15.8, §15.9 | P0 | Meets AC-03 invariant across all edge cases | **COMPLETED** | `b5a3e5f` |
| **ENG-08C**| Scope Classifier | Implement 2025 vs 2026 reporting scope difference classifier (Box 2 logic) | §14.2, §59.1 | P0 | Differentiates broker omission from basis mismatch | **COMPLETED** | `b5a3e5f` |
| **ENG-09A**| Shallow Provenance | Build provenance linker connecting source hashes, rows, and differences | §16.1, §17.1 | P0 | Traceable graph from receipt to source rows | **COMPLETED** | `b5a3e5f` |

### Workstream 5: Edge Runtime & Zero-Egress Local REST API (Slice 4)

| Task ID | Component | Task Description | PRD Ref | Priority | DoD Exit Criterion | Status | Commit ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ENG-01A**| Local FastAPI App | Build Edge REST service with `/cases`, `/sources`, `/reconcile`, `/receipt`, `/verify` | §62.1, §18.1 | P0 | All endpoints typed, documented via OpenAPI, 100% local | **COMPLETED** | `b5a3e5f` |
| **ENG-01B**| SQLite Store | Implement local SQLite database for case metadata, sources, and receipts | §18.2, §22.1 | P0 | ACID persistence, WAL mode, zero remote leakage | **COMPLETED** | `b5a3e5f` |
| **ENG-01C**| Dockerfile | Package single Docker/OCI container image (`vaultbasis-edge:preview`) | §6.1, §18.1 | P0 | Non-root user, slim base, minimal attack surface | **COMPLETED** | `bf8a795` |
| **ENG-02A**| Egress Controls | Configure zero-egress container profile and verify with packet capture tests | §21.1, §41 (AC-07)| P0 | Zero outbound packets detected during execution | **COMPLETED** | `bf8a795` |
| **SEC-01A**| Security Scan | Execute SAST, dependency vulnerability scan, and secret leak detection | §23.1, §64.1 | P0 | 0 critical / 0 high vulnerabilities | **COMPLETED** | `b5a3e5f` |

### Workstream 6: Three-Screen Local Dashboard & UI Surfaces (Slice 5 & 6)

| Task ID | Component | Task Description | PRD Ref | Priority | DoD Exit Criterion | Status | Commit ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **UX-01A** | Screen 1: Case List | Build Case List view (Create Case, Ingest Status, Case ID, Outcome State) | §34.2, §35.1 | P0 | Clean, industrial UI rendering all local cases | **COMPLETED** | `b5a3e5f` |
| **UX-01B** | Screen 2: Case Review| Build Case Review view (Source Integrity, Differences, Unresolved Items, Provenance) | §34.2, §35.2 | P0 | Displays exact differences without misleading green badges | **COMPLETED** | `b5a3e5f` |
| **UX-01C** | Screen 3: Receipt | Build Receipt & Export view (Receipt ID, Signer ID, Hash, Download Bundle) | §34.2, §13.3 | P0 | One-click ZIP bundle download (Receipt + Evidence + Verifier) | **COMPLETED** | `b5a3e5f` |
| **UX-02A** | Web Verifier | Build client-side standalone HTML/JS verifier (drag-and-drop receipt verification) | §34.3, §13.8 | P0 | Runs 100% in browser client with zero server calls | **COMPLETED** | `b5a3e5f` |
| **WEB-01A**| Preview Marketing | Create single-page preview marketing site explaining trust proposition & receipt demo | §34.1, §50.4 | P0 | Fast, responsive, institutional aesthetics, no hype | **COMPLETED** | `73a7a75` |

### Workstream 7: Left-Shift QA, Documentation & Launch Certification (Slice 7)

| Task ID | Component | Task Description | PRD Ref | Priority | DoD Exit Criterion | Status | Commit ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **QA-01A** | Unit Test Suite | Comprehensive unit tests for math, parsing, serializing, signing, hashing | §43.1, §64.1 | P0 | >90% code coverage on core deterministic engine | **COMPLETED** | `b5a3e5f` |
| **QA-02A** | Golden Test Suite | Reference test vectors with realistic 1099-DA and Koinly CSV cases | §43.2, §59.1 | P0 | 100% match on all reference scenarios | **COMPLETED** | `b5a3e5f` |
| **QA-ATDD**| Acceptance Suite | End-to-end customer & CPA workflows (`test_atdd_cpa_user_journey.py`) | §4.1, §50.4 | P0 | CPA full reconciliation journey verified (5 scenarios) | **COMPLETED** | `835a91c` |
| **QA-BDD** | BDD Feature Suite| Given-When-Then criteria for 7 preview gates (`test_bdd_acceptance_gates.py`)| §41 | P0 | All 7 blocking preview gates verified (11 scenarios) | **COMPLETED** | `835a91c` |
| **QA-TDD** | Invariant Suite  | Low-level exact decimal & RFC 8785 tests (`test_tdd_invariants.py`) | §15.1, §44.1 | P0 | Decimal math & canonicalization determinism verified (8 scenarios) | **COMPLETED** | `835a91c` |
| **QA-DDD** | Domain Invariants| Entity, value object & case aggregate tests (`test_ddd_domain_models.py`) | §17.1, §17.2 | P0 | Case lifecycle & transaction invariants verified (5 scenarios) | **COMPLETED** | `835a91c` |
| **QA-03A** | Differential Tests | Differential testing against independent reference calculation scripts | §43.3, §15.1 | P0 | Zero divergence against ground truth math | **COMPLETED** | `b5a3e5f` |
| **QA-04A** | Property/Fuzz Tests| Fuzz tests with corrupted, truncated, and random byte inputs | §43.4, §41 (AC-04)| P0 | Zero unhandled exceptions or crashes | **COMPLETED** | `b5a3e5f` |
| **QA-05A** | Industrial Gates   | Python-based Categorical Runner for 11 validation gates | §64, §71 | P0 | Structured 11-gate execution matrix and summary | **COMPLETED** | `7763c9b` |
| **QA-06A** | Extended DDD/TDD   | Extended invariant coverage (11 DDD, 14 TDD) for boundary testing | §43.1 | P0 | 100% pass on exactness and edge cases | **COMPLETED** | `7763c9b` |
| **DOC-01A**| Operator Guide | Write Edge Deployment Guide (`docs/edge_deployment_guide.md`) | §51.3, §63 | P0 | Step-by-step instructions tested on fresh machine | **COMPLETED** | `bf8a795` |
| **DOC-02A**| Verifier Guide | Write Independent Verifier Guide (`docs/verifier_guide.md`) | §51.3, §13.8 | P0 | Detailed third-party verification runbook | **COMPLETED** | `bf8a795` |
| **DOC-03A**| Manual QA Runbook | Create Manual Validation Scenarios Runbook (`docs/manual_validation_scenarios.md`)| §41, §50.4 | P0 | 10 exhaustive manual scenarios for periodic human auditing | **COMPLETED** | `835a91c` |
| **REL-01A**| Gate Certification | Review and certify all 7 preview gates in `docs/preview_gates_certification.md` | §41, §71 | P0 | All 7 gates signed off with test evidence | **COMPLETED** | `bf8a795` |
| **REL-02A**| ADR Documentation  | Document execution strategy in ADR-006 & Audit Status Updates | §64 | P0 | ADR-006 approved and Audit Status reflects Python matrix | **COMPLETED** | `7763c9b` |

### Workstream 8: Incremental Cloud Infrastructure & Vercel Production Deployment (Slice 8)

| Task ID | Component | Task Description | PRD Ref | Priority | DoD Exit Criterion | Status | Commit ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DEP-01A**| Cloud Config | Define `vercel.json` and `package.json` for incremental static deployment with strict security headers | §34.1, §50.4 | P0 | Validated Vercel config with cleanUrls, rewrites, and security headers | **COMPLETED** | `1424697` |
| **DEP-02A**| Static Packager | Build deterministic packager `scripts/build_public_web.js` with zero-leakage security audit | §21.1, §41 (AC-07)| P0 | Packages public web distribution with 0 keys and 0 DBs | **COMPLETED** | `1424697` |
| **DEP-03A**| Public Bridge | Build client-side localhost bridge in marketing site and WebCrypto verifier | §34.1, §34.3 | P0 | Public internet visitor discovers local edge or verifies receipts client-side | **COMPLETED** | `1424697` |
| **DEP-04A**| Left-Shift CI | Implement automated production deployment test suite (`test_vercel_incremental_build.py`) | §41, §64.1 | P0 | 100% pass on deployment test + pre-commit pipeline step 6 | **COMPLETED** | `1424697` |
| **DEP-05A**| Infra Operations| Comprehensive Operations & Deployment Runbook (`docs/infrastructure_and_deployment_guide.md`) | §6.1, §51.3 | P0 | End-to-end multi-tier infrastructure runbook documented | **COMPLETED** | `3cd422c` |
| **UX-03A** | Standard Web Nav| Standardized enterprise headers, multi-column footers, live sample receipts & anchor links | §34.1, §34.3 | P0 | 100% working links/buttons with statutory limitation notices | **COMPLETED** | `3cd422c` |
| **DEP-06A**| Web Link Gates | Regression test suite for web navigation, headers, footers & endpoints (`test_web_navigation_and_links.py`)| §41, §64.1 | P0 | 51 tests green across comprehensive suite | **COMPLETED** | `3cd422c` |
| **FIX-01A**| Anchor Offset  | Resolve sticky header occlusion using `scroll-padding-top`, `scroll-margin-top` and smooth offset handler | §34.1 | P0 | Headings scroll with full clearance beneath sticky header | **COMPLETED** | `e9500d4` |

### Workstream 9: Commercialization, Paddle Licensing & Cloud Distribution (Slice 9 - Upcoming)

| Task ID | Component | Task Description | PRD Ref | Priority | DoD Exit Criterion | Status | Commit ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **COM-01A**| Cloud Object Storage | Configure GCP/AWS/Scaleway bucket to securely store the obfuscated Desktop Executable bundles | Future | P0 | Automated push of `Release.zip` from CI/CD to secure cloud bucket | **NOT STARTED** | |
| **COM-02A**| Paddle Checkout UI | Integrate Paddle Billing overlay into the Public Marketing Site (`web-marketing`) | Future | P0 | Users can add VaultBasis to cart and trigger a test payment | **NOT STARTED** | |
| **COM-03A**| License Generator API| Deploy a cloud webhook (Serverless function) to catch Paddle `transaction.completed` events | Future | P0 | Webhook generates and emails a cryptographically signed license key | **NOT STARTED** | |
| **COM-04A**| Local License Validator | Update VaultBasis Edge (`app.py`) to cryptographically verify the user's purchased license key | Future | P0 | Dashboard requires a valid license key before allowing Case Creation | **NOT STARTED** | |
| **COM-05A**| Authenticated Download | Implement secure, time-limited, signed download URLs for buyers to download the desktop bundle | Future | P0 | Only verified purchasers can download the actual Desktop Bundle | **NOT STARTED** | |

---

## 6. Execution Protocol: Slice 1 Immediate Kickoff

Per instruction:
1. **Master Tasks Ledger** is established in `docs/master_tasks_ledger.md`.
2. **Begin with the first task**: Task **GOV-01** / **Slice 1**:
   - Establish the canonical folder scaffold (`schemas/receipt/`, `edge/`, `docs/`, `tests/`).
   - Create normative **Evidence Contract v0.1**:
     - `schemas/receipt/receipt-v0.1.json` (strict JSON schema for Outcome Receipt v0.1)
     - `schemas/receipt/canonicalization-v0.1.md` (normative byte-level canonicalization specification)
     - `schemas/receipt/signing-v0.1.md` (Ed25519 signing & verification protocol)
     - `schemas/receipt/verification-v0.1.md` (independent verification rules & limits)
   - Implement the cryptographic primitives & standalone offline verifier (`edge/receipts/` and `apps/verifier/`).
   - Deliver end-to-end working demonstration of Slice 1 with clean tests before initiating Slice 2.
