# VaultBasis MMP-1.5 Commercial Operations & Control Plane — Master Tasks Ledger

> **Release Phase:** MMP-1.5 — Commercial Operations & Control Plane  
> **Directive:** Bounded commercial operations, firm identity, licensing/entitlement state, and administrative control plane.  
> **Governance Isolation Rule:** MMP-1.5 workstreams MUST NOT modify or destabilize core deterministic reconciliation math (`edge/reconcile/`, `schemas/canonical/`), cryptographic evidence hashing (`edge/receipts/`), or qualified distribution packages (`VaultBasis-RC3-*`).  
> **Explicit MMP-2 Exclusions:** All intelligence, natural language generation, RAG, automated client-question drafting, evidence-gap investigation, and LLM-assisted features belong strictly in MMP-2 and are excluded from this ledger.

---

## 1. Governance & Architectural Boundaries

1. **Air-Gap & Offline Safety First:** Entitlement evaluation and local commercial state MUST function in fully air-gapped / disconnected practitioner environments using cryptographically signed, offline-verifiable license tokens.
2. **Strict Privacy Boundary:** Firm/account identity, license keys, seat assignments, and operational diagnostic bundles MUST NEVER contain client financial data, raw broker/ledger rows, or PII.
3. **No Metering on Verification:** Offline receipt verification (`apps/edge-offline-verifier/`, `apps/verifier/`) remains 100% free, unmetered, and unencumbered by license state.
4. **Independent Branching:** All MMP-1.5 work is developed on dedicated `feat/mmp15-*` branches and merged only when 100% green without impacting MMP-1.1 qualification.

---

## 2. Master Tasks Ledger Schema & Catalog

| Task ID | Feature | Commercial Blocker | Target User | Scope | Out of Scope | Acceptance Criteria | Security Boundary | Dependencies | Target Tests | Branch | Commit | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **MMP15-ENT-001** | Offline Entitlement & License State Model | Blocker 1: Inability to enforce licensed capacity / tiers without cloud reliance | Solo CPA, Multi-preparer Firm | Ed25519-signed local license token schema, tier states (`TRIAL`, `ESSENTIAL`, `PRACTICE`, `ENTERPRISE`), capacity counter, expiry/grace periods, tamper detection | Online phone-home DRM, hardware dongles, automated credit card charging | Valid signed license activates tier and capacity; expired/tampered license gracefully transitions to read-only/verify-only state; zero float drift | License signed with TecTixBase commercial root key; private key never stored on edge client | Evidence Contract v0.1 | `tests/unit/test_mmp15_license_engine.py` | `feat/mmp15-entitlement-001` | — | `READY_FOR_DEV` |
| **MMP15-ENT-002** | Local Entitlement Enforcement Middleware | Blocker 2: Preventing unauthorized case creation without breaking verification | Practitioner, Auditor | API middleware gating `POST /api/cases` and `POST /api/sample-case/load` behind active entitlement check; unauthenticated verify/export remains open | Remote revocation check; blocking reading existing historical cases | Exceeded capacity or expired license returns structured `402 Payment Required` / `403 Entitlement Expired` with clear upgrade guidance | Zero case data emitted during entitlement errors | MMP15-ENT-001 | `tests/unit/test_mmp15_entitlement_middleware.py` | `feat/mmp15-entitlement-001` | — | `PLANNED` |
| **MMP15-ORG-001** | Firm & Workspace Identity Domain Model | Blocker 3: Lack of firm-level provenance on workpapers and multi-seat context | Firm Managing Partner, Staff CPA | Organization metadata schema (Firm Name, Office ID, Preparer ID, EFIN/PTIN optional ref, Environment Tag: `SANDBOX` / `PRODUCTION`) | Centralized multi-tenant cloud sync, user directory SSO/SAML | Organization identity stored in local SQLite `workspaces` table; rendered on UI header & audit receipts | Strict local isolation; firm metadata separated from financial calculations | MMP11-CASE-001 | `tests/unit/test_mmp15_workspace_identity.py` | `feat/mmp15-org-identity-001` | — | `PLANNED` |
| **MMP15-OPS-001** | Air-Gapped Diagnostic & Support Bundle Packager | Blocker 4: Support unable to diagnose runtime errors without violating PII boundaries | Firm IT, Support Engineer | Sanitized diagnostic exporter: OS, Python/PyInstaller versions, SQLite schema version, error logs, license state (zero customer records, zero transaction rows, zero PII) | Automated remote log streaming, telemetry agents | Single-click export of `VaultBasis_Support_Diagnostic.json` with positive PII-scrub verification gate | Guaranteed zero transaction or client data inclusion (negative regex & schema audit) | None | `tests/unit/test_mmp15_support_packager.py` | `feat/mmp15-ops-control-001` | — | `PLANNED` |
| **MMP15-OPS-002** | Version & Release Channel Compatibility Service | Blocker 5: Practitioners running mismatched schema/runtime versions across team | Firm Managing Partner, IT Admin | Version metadata endpoint (`GET /api/system/version`), channel awareness (`STABLE`, `CANDIDATE`), migration safety checks | Background auto-updater, silent binary downloads | System reports build SHA, channel, schema compatibility matrix; warns on outdated offline schema | Read-only local inspection | None | `tests/unit/test_mmp15_version_channel.py` | `feat/mmp15-ops-control-001` | — | `PLANNED` |
| **MMP15-ADM-001** | Commercial License Generator CLI (Internal Tooling) | Blocker 6: Inability for TecTixBase ops to issue cryptographically signed customer licenses | Commercial Ops, Support | CLI tool `tools/issue_license.py` generating signed license tokens given Customer ID, Tier, Max Cases, Expiry Date using private root key | Public web dashboard for customer self-service | Tool outputs deterministic Base64/JSON license tokens verifiable by MMP15-ENT-001 | Root signing key isolated in air-gapped / CI secret env | MMP15-ENT-001 | `tests/unit/test_mmp15_license_generator.py` | `feat/mmp15-entitlement-001` | — | `PLANNED` |
| **MMP15-AUD-001** | Commercial & Administrative Audit Event Log | Blocker 7: Lack of non-repudiable log for license activation, tier change, and support actions | Compliance Officer, Managing Partner | Append-only SQLite `commercial_audit_log` table tracking: license key applied, tier changed, diagnostic exported, seat registered | Centralized remote SIEM export | Tamper-evident hash-chained audit log for administrative events | Audit log stored locally with restricted table access; no transaction data | MMP15-ENT-001, MMP15-ORG-001 | `tests/unit/test_mmp15_audit_log.py` | `feat/mmp15-audit-001` | — | `PLANNED` |

---

## 3. Critical Path Ranking (First 7 Items)

Ranked by **Commercial Necessity**, **Implementation Risk**, **Coupling to MMP-1.1**, **Security/Privacy Boundary**, and **Offline Safety**:

1. **MMP15-ENT-001 (P0): Offline Entitlement & License State Model**  
   - *Why first:* Forms the root cryptographic contract for all commercial operations without modifying any core reconciliation logic. 100% offline verifiable.
2. **MMP15-ADM-001 (P0): Commercial License Generator Tooling**  
   - *Why second:* Directly pairs with ENT-001 to generate test vectors and production license keys.
3. **MMP15-ENT-002 (P0): Local Entitlement Enforcement Middleware**  
   - *Why third:* Enforces capacity limits and tier behaviors at the API boundary, keeping the UI and verifier fail-safe.
4. **MMP15-ORG-001 (P1): Firm & Workspace Identity Domain Model**  
   - *Why fourth:* Establishes professional context (firm name, preparer ID) for practice workpapers.
5. **MMP15-OPS-001 (P1): Air-Gapped Diagnostic & Support Bundle Packager**  
   - *Why fifth:* Critical for enterprise and CPA support triage while strictly preventing PII egress.
6. **MMP15-OPS-002 (P2): Version & Release Channel Compatibility Service**  
   - *Why sixth:* Ensures multi-seat consistency and controlled upgrade readiness.
7. **MMP15-AUD-001 (P2): Commercial & Administrative Audit Event Log**  
   - *Why seventh:* Completes enterprise auditability and non-repudiation for administrative actions.
