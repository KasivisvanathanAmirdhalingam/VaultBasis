# VaultBasis MMP-1.5 Commercial Operations & Control Plane — Master Tasks Ledger

> **Release Phase:** MMP-1.5 — Commercial Operations & Control Plane  
> **Directive:** Bounded commercial operations, firm identity, licensing/entitlement state, and administrative control plane.  
> **Governance Isolation Rule:** MMP-1.5 workstreams MUST NOT modify or destabilize core deterministic reconciliation math (`edge/reconcile/`, `schemas/canonical/`), cryptographic evidence hashing (`edge/receipts/`), or qualified distribution packages (`VaultBasis-RC3-*`).  
> **Explicit MMP-2 Exclusions:** All intelligence, natural language generation, RAG, automated client-question drafting, evidence-gap investigation, and LLM-assisted features belong strictly in MMP-2 and are excluded from this ledger.

---

## 1. Governance & Architectural Boundaries

1. **Air-Gap & Offline Safety First:** Entitlement evaluation and local commercial state MUST function in fully air-gapped / disconnected practitioner environments using cryptographically signed, offline-verifiable license tokens.
2. **Entitlement vs. Authorization vs. Verification Boundary:**
   - **Independent Verification:** Free, public, unmetered, and unencumbered by license state (`apps/edge-offline-verifier/`, `apps/verifier/`).
   - **Commercial Entitlement:** Evaluates whether this local installation/customer is commercially permitted to perform case creation / reconciliation within licensed boundaries (`max_cases_per_installation`, tier, validity period).
   - **Access / Case Security:** Bounded by local workspace identity and data ownership; evidence export is governed by case access rules, never unauthenticated.
3. **Offline Enforceability Realism:**
   - *Enforceable Offline:* `max_cases_per_installation`, `license_tier`, `not_before`, `expires_at`, `grace_until`, optional `installation_id` binding, and local tamper-evident event logs.
   - *Non-Enforceable Offline without Consensus:* Global cross-machine concurrent seat counters or real-time revocation across disconnected machines.
4. **Cryptographic Key Isolation:**
   - **Commercial License Signing Key (Private):** Air-gapped / isolated commercial operations tooling ONLY. NEVER committed to Git, packaged into binaries, or shipped to client edge.
   - **Commercial License Verification Key (Public):** Embedded in edge runtime for local cryptographic signature validation.
5. **Regulated & Professional Identity Isolation:**
   - **Organization Identity:** `organization_id`, `firm_name`, `office_id`, `workspace_id`.
   - **Practitioner Identity:** `preparer_id`, `display_name`.
   - **Regulated Identifiers:** `PTIN`, `EFIN` — strictly local, never in portable receipts, redacted from support/diagnostic bundles.

---

## 2. Master Tasks Ledger Schema & Catalog

| Task ID | Feature | Commercial Blocker | Target User | Scope | Out of Scope | Acceptance Criteria | Security Boundary | Dependencies | Target Tests | Branch | Commit | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **MMP15-ENT-001** | Offline Entitlement & License State Model | Blocker 1: Inability to enforce licensed capacity / tiers without cloud reliance | Solo CPA, Multi-preparer Firm | Ed25519-signed local license token schema, `LicenseTier` (`TRIAL`, `ESSENTIAL`, `PRACTICE`, `ENTERPRISE`), `LicenseState` (`ACTIVE`, `GRACE`, `EXPIRED`, `NOT_YET_VALID`, `INVALID_SIGNATURE`, `MALFORMED`, `UNSUPPORTED_VERSION`, `INSTALLATION_MISMATCH`), local `max_cases_per_installation`, validity dates (`not_before`, `expires_at`, `grace_until`), tamper rejection | Online phone-home DRM, global multi-machine seat synchronization, hardware dongles | Valid signed token evaluates to `ACTIVE`; payload/signature tampering deterministically rejected; clock boundaries and grace windows strictly verified; zero network access; zero private key material in verifier | Signed with isolated Commercial License Signing Key; verified via embedded public key | Evidence Contract v0.1 | `tests/unit/test_mmp15_license_engine.py` | `feat/mmp15-entitlement-001` | `f852a15` | `BASELINED / CLOSED` |
| **MMP15-ADM-001** | Commercial License Generator CLI (Internal Tooling) | Blocker 6: Inability for TecTixBase ops to issue cryptographically signed customer licenses | Commercial Ops, Support | Standalone tool `tools/issue_license.py` generating signed license tokens given Customer ID, Tier, Max Cases per Installation, Validity Dates using isolated Commercial License Signing Key | Client-facing GUI, automated billing webhooks | Tool outputs deterministic Base64/JSON license tokens verifiable by `MMP15-ENT-001`; asserts required fields and valid date sequences | Private key isolated; script strictly excluded from distribution packages | MMP15-ENT-001 | `tests/unit/test_mmp15_license_engine.py` | `feat/mmp15-entitlement-001` | `f852a15` | `BASELINED / CLOSED` |
| **MMP15-ENT-002** | Local Entitlement Enforcement Service & Policy | Blocker 2: Preventing unauthorized case creation while preserving unmetered verification | Practitioner, Auditor | Policy/service boundary (`CommercialPolicyService`) gating case creation and reconciliation behind active entitlement check; independent verification (`/verify`) remains unmetered and open; existing cases & evidence export remain accessible under local case access controls | Remote revocation check; blocking reading existing historical cases; modifying reconciliation math | Exceeded capacity or expired license returns structured machine-readable error codes (`CASE_CAPACITY_REACHED`, `LICENSE_EXPIRED`, `ENTITLEMENT_REQUIRED`, etc.); zero financial payload leakage during errors | Zero case data emitted during entitlement rejections | MMP15-ENT-001 | `tests/unit/test_mmp15_entitlement_enforcement.py` | `feat/mmp15-entitlement-enforcement-002` | `843e55c` | `BASELINED / CLOSED` |
| **MMP15-DATA-001** | Local Persistence Durability & Recovery Contract | Blocker 8: Unqualified database corruption risk, crash recovery, and undefined migration contract | Firm IT, Practitioner | SQLite WAL mode, `PRAGMA synchronous = FULL/NORMAL`, `PRAGMA foreign_keys = ON`, atomic transactions, versioned migrations schema, backup/restore CLI/API, startup integrity check (`PRAGMA integrity_check`), crash recovery tests | Remote multi-node database clustering | Corrupted DB safely detected at startup; backups restorable deterministically; WAL prevents partial writes on crash; migrations run transactionally | Local database files restricted to OS user data path; zero secret leakage | None | `tests/unit/test_mmp15_data_durability.py` | `feat/mmp15-data-durability-001` | `e7e7d35` | `BASELINED / CLOSED` |
| **MMP15-ORG-001** | Firm & Workspace Identity Domain Model | Blocker 3: Lack of firm-level provenance on workpapers and multi-seat context | Firm Managing Partner, Staff CPA | Organization metadata schema (`organization_id`, `firm_name`, `office_id`, `workspace_id`), Practitioner metadata (`preparer_id`, `display_name`), Regulated metadata (`PTIN`, `EFIN`), local SQLite storage, deterministic redaction rules | Centralized multi-tenant cloud sync, user directory SSO/SAML | Firm identity rendered on UI header & audit receipts; PTIN/EFIN stored with local encryption and explicitly scrubbed from diagnostics | Regulated IDs (PTIN/EFIN) never exported in diagnostic bundles or public logs | MMP11-CASE-001 | `tests/unit/test_mmp15_workspace_identity.py` | `feat/mmp15-org-identity-001` | `951a89e` | `BASELINED / CLOSED` |
| **MMP15-OPS-001** | Air-Gapped Diagnostic & Support Bundle Packager | Blocker 4: Support unable to diagnose runtime errors without violating PII boundaries | Firm IT, Support Engineer | Sanitized diagnostic exporter: OS, Python/PyInstaller versions, SQLite schema version, error logs, license state (zero customer records, zero transaction rows, zero PII, zero PTIN/EFIN) | Automated remote log streaming, telemetry agents | Single-click export of `VaultBasis_Support_Diagnostic.json` with positive PII-scrub verification gate (regex + schema audit) | Guaranteed zero transaction, client, or regulated identifier inclusion | None | `tests/unit/test_mmp15_support_packager.py` | `feat/mmp15-ops-control-001` | — | `PLANNED` |
| **MMP15-OPS-002** | Version & Release Channel Compatibility Service | Blocker 5: Practitioners running mismatched schema/runtime versions across team | Firm Managing Partner, IT Admin | Version metadata endpoint (`GET /api/system/version`), channel awareness (`STABLE`, `CANDIDATE`), migration safety checks | Background auto-updater, silent binary downloads | System reports build SHA, channel, schema compatibility matrix; warns on outdated offline schema | Read-only local inspection | None | `tests/unit/test_mmp15_version_channel.py` | `feat/mmp15-ops-control-001` | — | `PLANNED` |
| **MMP15-AUD-001** | Commercial & Administrative Audit Event Log | Blocker 7: Lack of non-repudiable log for license activation, tier change, and support actions | Compliance Officer, Managing Partner | Append-only SQLite `commercial_audit_log` table tracking: license key applied, tier changed, diagnostic exported, seat registered | Centralized remote SIEM export | Tamper-evident hash-chained audit log for administrative events | Audit log stored locally with restricted table access; no transaction data | MMP15-ENT-001, MMP15-ORG-001 | `tests/unit/test_mmp15_audit_log.py` | `feat/mmp15-audit-001` | — | `PLANNED` |

---

## 3. Critical Path Ranking (First 8 Items)

Ranked by **Commercial Necessity**, **Implementation Risk**, **Coupling to MMP-1.1**, **Security/Privacy Boundary**, and **Offline Safety**:

1. **MMP15-ENT-001 (P0): Offline Entitlement & License State Model** `[CLOSED]`  
   - *Why first:* Forms the root cryptographic contract for all commercial operations without modifying any core reconciliation logic. 100% offline verifiable.
2. **MMP15-ADM-001 (P0): Commercial License Generator Tooling** `[CLOSED]`  
   - *Why second:* Directly pairs with ENT-001 to generate test vectors and production license keys.
3. **MMP15-ENT-002 (P0): Local Entitlement Enforcement Service & Policy** `[CLOSED]`  
   - *Why third:* Enforces capacity limits and tier behaviors at the API boundary, keeping the UI and verifier fail-safe.
4. **MMP15-DATA-001 (P0): Local Persistence Durability & Recovery Contract** `[ACTIVE]`  
   - *Why fourth:* Establishes WAL mode, synchronous reliability, schema migration history, startup integrity checks, and crash recovery before expanding commercial tables.
5. **MMP15-ORG-001 (P1): Firm & Workspace Identity Domain Model** `[ACTIVE]`  
   - *Why fifth:* Establishes professional context (firm name, preparer ID, workspace) and regulated ID redaction rules.
6. **MMP15-OPS-001 (P1): Air-Gapped Diagnostic & Support Bundle Packager**  
   - *Why sixth:* Critical for enterprise and CPA support triage while strictly preventing PII egress.
7. **MMP15-OPS-002 (P2): Version & Release Channel Compatibility Service**  
   - *Why seventh:* Ensures multi-seat consistency and controlled upgrade readiness.
8. **MMP15-AUD-001 (P2): Commercial & Administrative Audit Event Log**  
   - *Why eighth:* Completes enterprise auditability and non-repudiation for administrative actions.


