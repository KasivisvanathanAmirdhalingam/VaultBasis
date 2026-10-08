# VaultBasis Canonical Production Release Gates (PROD-GATES)
**Document ID:** VB-SPEC-GATE-001  
**Classification:** NORMATIVE  
**Authority:** Release Engineering Authority  
**Status:** FROZEN  
**Applies To:** VaultBasis Edge v1.5.0 and subsequent production releases  
**Last Reviewed:** 2026-10-08  

---

## 1. Executive Rule

The 18 Canonical Production Release Gates (`PROD-GATE-01` through `PROD-GATE-18`) define the absolute, non-negotiable exit criteria for general customer distribution of VaultBasis Edge. 

> **Immutability Invariant:** Gate IDs and their canonical definitions are **strictly frozen**. Supporting checks (such as catalog integrity, pricing parity, zero token bleed, and Vercel route parity) must exist as subrequirements and evidence controls that feed into these gates, and must never redefine or replace the canonical gate meanings.

---

## 2. Canonical Gate Registry

| Gate ID | Frozen Canonical Meaning | Authority Level | Verification Standard | Supporting Subrequirements & Evidence |
|---|---|---|---|---|
| **`PROD-GATE-01`** | **Distribution Authorization / Token Gate** | NORMATIVE / SECURITY | Distribution endpoints serve artifacts only upon validated token presentation; unauthorized requests receive 401/403 with zero token or byte bleed. | `SUBREQ-SEC-TOKEN-001` (Zero Token Bleed)<br>`SUBREQ-WEB-ROUTE-001` (Vercel Route Parity)<br>`SUBREQ-HOST-BIND-001` (Loopback Auth) |
| **`PROD-GATE-02`** | **Commercial Plan / Mailer Copy** | NORMATIVE / COMMERCIAL | Pricing tiers, case capacity, mailer templates, and commercial terms are 100% synchronized across website, edge UI, and delivery emails. | `SUBREQ-COMM-CATALOG-001` (Catalog Integrity)<br>`SUBREQ-COMM-PRICE-001` (Pricing Parity)<br>`SUBREQ-COMM-MAILER-001` (Mailer Contract) |
| **`PROD-GATE-03`** | **Air-Gapped License Provisioning** | NORMATIVE / COMMERCIAL | Paid license tokens can be generated, issued, delivered, and provisioned onto a clean offline machine without requiring edge network access. | `SUBREQ-LIC-OFFLINE-001` (Offline License Protocol v1.0)<br>`evidence/license_protocol_audit.json` |
| **`PROD-GATE-04`** | **Monotonic Revision** | NORMATIVE / SECURITY | License tokens, database schemas, and state updates enforce strictly monotonic sequence counters; downgrade and replay attacks are rejected. | `SUBREQ-SEC-REV-001` (Monotonic Revision)<br>`tests/security/test_deploy_sec_002_rollback_prevention.py` |
| **`PROD-GATE-05`** | **In-App Activation** | NORMATIVE / COMMERCIAL | In-app license token entry transitions the local edge engine from Evaluation (3-case cap) to Paid tier immediately with zero data loss or case corruption. | `SUBREQ-COMM-ACT-001` (In-App Activation)<br>`tests/unit/test_mmp15_entitlement_enforcement.py` |
| **`PROD-GATE-06`** | **Restart Persistence** | NORMATIVE / PERSISTENCE | Complete application state (cases, transactions, findings, receipts, license tier, installation identity) survives abrupt shutdown, restart, and version upgrades. | `SUBREQ-DATA-WAL-001` (SQLite FULL Sync & WAL)<br>`SUBREQ-DATA-REINSTALL-001` (Data Preservation) |
| **`PROD-GATE-07`** | **Windows Signing (Authenticode)** | NORMATIVE / PLATFORM TRUST | Windows installer (`VaultBasis-Setup-1.5.0-rc3.exe`) and inner binaries are signed with a valid Microsoft-trusted Authenticode certificate and RFC 3161 timestamp. | Azure Artifact Signing (Public Trust / Basic)<br>`evidence/windows_authenticode_cert.json` |
| **`PROD-GATE-08`** | **macOS Signing / Notarization** | NORMATIVE / PLATFORM TRUST | macOS bundle (`VaultBasis.app`) and DMG are signed with Apple Developer ID Application certificate, Hardened Runtime enabled, notarized by Apple, and stapled. | Apple Developer Program<br>`evidence/macos_notarization_ticket.json` |
| **`PROD-GATE-09`** | **Clean-Machine Launch (Physical UAT)** | OPERATIONAL / UAT | Signed candidate binaries launch cleanly on pristine Windows 11 and macOS Sequoia hardware without developer tooling, runtime overrides, or terminal intervention. | Physical Clean OS UAT Execution Protocol<br>`evidence/physical_uat_signoff.json` |
| **`PROD-GATE-10`** | **Release Manifest Immutability / Commit Binding** | NORMATIVE / RELEASE OPS | Release manifest (`release-manifest.json`) binds exact git commit SHA, source tree hash, and pre-sign / post-sign SHA-256 digests for all distributables. | `evidence/release_manifest.json`<br>`docs/qualification/mmp15_traceability_matrix.md` |
| **`PROD-GATE-11`** | **Distribution Active / Anti-Rollback** | NORMATIVE / DISTRIBUTION | Public distribution gateway is armed and active; historical revoked or superseded builds cannot be served or verified as current. | Web Distribution Router Configuration<br>`tests/quality/production_deployment/test_vercel_route_parity.py` |
| **`PROD-GATE-12`** | **SPF / DKIM / DMARC** | OPERATIONAL / INFRASTRUCTURE | Production DNS records for `vaultbasis.com` strictly enforce SPF (`v=spf1`), DKIM 2048-bit, and DMARC (`p=reject`) to eliminate transactional mail spoofing. | DNS Dig / Auth Records Verification<br>`evidence/dns_email_security_proof.json` |
| **`PROD-GATE-13`** | **UAT Platform Quota** | OPERATIONAL / UAT | Evaluation mode strictly enforces 3-case creation capacity across full user journey; quota exhaustion triggers polite upgrade CTA with zero silent overflow. | `SUBREQ-COMM-QUOTA-001` (3-Case Evaluation Invariant)<br>`tests/unit/test_mmp15_entitlement_enforcement.py` |
| **`PROD-GATE-14`** | **Unassisted Intake / Provenance** | NORMATIVE / INTAKE | Engine automatically ingests Form 1099-DA (CSV/PDF) and Ledger records without human schema mapping; records complete source file hashes and row provenance. | `SUBREQ-INTK-AUTO-001` (Unassisted Ingestion)<br>`tests/quality/release_1_5/test_adversarial_reconciliation_vectors.py` |
| **`PROD-GATE-15`** | **Deterministic Reconciliation & Decimal Precision** | NORMATIVE / RECONCILIATION | Engine executes exact Base-10 Decimal arithmetic (sub-cent preserved, zero IEEE 754 float drift) and resolves all 13 canonical outcome states deterministically. | `SEM-ROUND-002` (Exact Decimal Matching)<br>`SEM-ING-001` (Malformed Intake Failsafe)<br>`evidence/recon_golden_matrix.json` |
| **`PROD-GATE-16`** | **Signed Export & Integrity** | NORMATIVE / EVIDENCE | Engine issues immutable Ed25519-signed cryptographic receipts conforming to `receipt-v0.1.json` with embedded installation public key; any byte alteration causes verification failure. | `SUBREQ-RCPT-ED25519-001` (Cryptographic Receipt)<br>`tests/quality/release_1_5/test_receipt_contract_exhaustiveness.py` |
| **`PROD-GATE-17`** | **Standalone Offline Verifier** | NORMATIVE / VERIFIER | Independent zero-dependency script ([`apps/verifier/verify_receipt.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/apps/verifier/verify_receipt.py)) verifies receipt integrity, calculations, and signatures in an air-gapped environment. | `SUBREQ-VERIF-OFFLINE-001` (Zero-Dependency Verifier)<br>`tests/quality/golden/test_verifier.py` |
| **`PROD-GATE-18`** | **Final Launch Authorization / MMP2** | NORMATIVE / GOVERNANCE | Formal release sign-off by Release Authority certifying all 17 precursor gates are verified and closed; unlocks production distribution. | `VB-AUTH-MMP15-RELEASE`<br>`evidence/production_authorization_receipt.json` |

---

## 3. Qualification Prefix Standards

To prevent premature or ambiguous claims of closure, gate statuses must always use explicit stage-aware prefixes:

* **`NOT_RUN_PRE_SIGN`**: Gate requires platform signing credentials or physical execution not yet performed.
* **`OPEN`**: Operational or external gate pending active distribution window.
* **`OPEN_EXTERNAL`**: External infrastructure check (e.g. DNS SPF/DKIM) pending live domain verification.
* **`OPEN_PHYSICAL_UAT`**: Gate requires physical clean-machine hardware execution.
* **`SOURCE_PASS` / `SOURCE_QUALIFIED`**: Implementation and unit/integration/adversarial test vectors pass at the source repository layer.
* **`MAC_PRE_SIGN_PASS` / `MAC_PRE_SIGN_QUALIFIED`**: Verified against the mounted and extracted customer-shaped macOS candidate artifact (`VaultBasis-RC3-macOS-arm64.dmg`).
* **`WIN_PRE_SIGN_PASS` / `WIN_PRE_SIGN_QUALIFIED`**: Verified against the installed Windows candidate artifact (`VaultBasis-Setup-1.5.0-rc3.exe`).
* **`SIGNED_ARTIFACT_PASS`**: Verified against the post-signing, notarized/stapled binary.
* **`PHYSICAL_PASS`**: Verified on clean physical hardware.
* **`CLOSED`**: Fully certified and authorized by Release Authority.
* **`BLOCKED`**: Release prohibited due to open precursor gates.
