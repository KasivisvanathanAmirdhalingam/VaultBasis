# VaultBasis MMP-1.5 End-to-End Traceability Matrix
**Document ID:** VB-TRACE-MMP15-001  
**Release Target:** VaultBasis Edge v1.5.0 (MMP-1.5)  
**Classification:** NORMATIVE  
**Authority:** Release Engineering Authority  
**Status:** ACTIVE / BASELINE ESTABLISHED  
**Last Reviewed:** 2026-10-08  

---

## 1. Traceability Architecture

The VaultBasis Traceability Matrix establishes a strict 1-to-1-to-1 chain of custody from user requirement through source implementation, automated source tests, packaged binary artifact verification, physical environment validation, and formal release gate certification.

```
Requirement (PRD / MMP-1.5)
       ↓
Implementation Code
       ↓
Source-Level Automated Tests (pytest)
       ↓
Packaged Artifact Qualification (DMG / EXE)
       ↓
Physical OS Clean Machine Qualification (Windows / macOS)
       ↓
PROD-GATE Certification & Evidence Artifact
```

---

## 2. Requirement → Implementation → Test → Gate Matrix

| Req ID | Requirement Statement | Implementation Path | Source Test Suite | Artifact Test Suite | Physical OS Test | PROD-GATE | Evidence Artifact | Owner | Status |
|---|---|---|---|---|---|---|---|---|---|
| **REQ-COMM-001** | Commercial Plan & Mailer Copy parity | [`apps/web-marketing/api/delivery-mailer.js`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/apps/web-marketing/api/delivery-mailer.js) | `test_commercial_catalog_contract.py` | Live web catalog smoke | Physical email delivery test | **PROD-GATE-02** | `evidence/commercial_catalog_proof.json` | Commercial Lead | **SOURCE_PASS** |
| **REQ-COMM-002** | Monotonic revision & anti-rollback protection | [`edge/commercial/policy.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/edge/commercial/policy.py) | `test_deploy_sec_002_rollback_prevention.py` | Upgrade/downgrade boundary fuzzing | Monotonic revision vector injection | **PROD-GATE-04** | `evidence/monotonic_revision_proof.json` | Core Engine Lead | **SOURCE_PASS** |
| **REQ-COMM-003** | In-app license activation & capability unlock | [`edge/commercial/engine.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/edge/commercial/engine.py) | `test_mmp15_entitlement_enforcement.py` | Evaluation to Paid in packaged runtime | Air-gapped license activation test | **PROD-GATE-05** | `evidence/in_app_activation_proof.json` | Commercial Lead | **SOURCE_PASS** |
| **REQ-DATA-001** | SQLite durability & restart persistence (WAL mode, FULL sync) | [`edge/storage/sqlite_store.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/edge/storage/sqlite_store.py) | `test_mmp15_data_durability.py` | Packaged database schema & restart test | Crash & force-kill durability test | **PROD-GATE-06** | `evidence/wal_durability_evidence.json` | Persistence Lead | **SOURCE_PASS** / **MAC_PRE_SIGN_ARTIFACT_PASS** |
| **REQ-DATA-002** | Customer data & key preservation across upgrade/uninstall | [`scripts/installer_windows.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/scripts/installer_windows.py) | `test_mmp15_data_durability.py` | Install → Case → Uninstall → Reinstall | Physical registry & AppData inspection | **PROD-GATE-06** / **PROD-GATE-09** | `evidence/uninstall_reinstall_trace.json` | Platform Lead | **PENDING** (Physical Windows Execution) |
| **REQ-SIGN-001** | Windows Authenticode signing via Azure Artifact Signing (Public Trust) | `scripts/sign_windows_azure.py` | Signature verification tests | SignTool & Authenticode check on `VaultBasis-Setup.exe` | Clean Windows 11 SmartScreen install test (Feeds Gate 09) | **PROD-GATE-07** | `evidence/windows_authenticode_cert.json` | Release Ops Lead | **NOT_RUN_PRE_SIGN** (Awaiting Azure Org Verification) |
| **REQ-SIGN-002** | macOS Developer ID signing, Hardened Runtime, notarization & stapling | `scripts/sign_macos_apple.py` | `spctl` & `codesign` verification tests | `spctl --assess --type exec -vv` on packaged `.app` & `.dmg` | Clean macOS Gatekeeper execution test (Feeds Gate 09) | **PROD-GATE-08** | `evidence/macos_notarization_ticket.json` | Release Ops Lead | **NOT_RUN_PRE_SIGN** (Awaiting Apple Org Enrollment) |
| **REQ-INTK-001** | Unassisted intake, schema detection, and provenance tracking | [`edge/connectors/validator.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/edge/connectors/validator.py) | `test_slice2_intake_and_reconciliation.py` | Hostile and unassisted intake fuzzing | Ingestion smoke on Win/Mac | **PROD-GATE-14** | `evidence/unassisted_intake_report.json` | Intake Lead | **SOURCE_PASS** / **MAC_PRE_SIGN_ARTIFACT_PASS** |
| **REQ-RECON-001** | Deterministic reconciliation of Form 1099-DA vs crypto tax ledger | [`edge/assurance/reconciliation_engine.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/edge/assurance/reconciliation_engine.py) | `test_adversarial_reconciliation_vectors.py` | `test_artifact_qualification_suite.py` | Golden case execution on clean Win/Mac | **PROD-GATE-15** | `evidence/recon_golden_matrix.json` | Core Engine Lead | **SOURCE_PASS** / **MAC_PRE_SIGN_ARTIFACT_PASS** |
| **REQ-RECON-002** | Exact decimal arithmetic (no IEEE 754 floats; trailing zero normalization) | [`schemas/canonical/transaction.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/schemas/canonical/transaction.py) | `test_golden_corpus.py` (G017) | Binary inspection for Decimal parser | Decimal boundary injection | **PROD-GATE-15** | `evidence/decimal_arithmetic_proof.json` | Core Engine Lead | **SOURCE_PASS** / **MAC_PRE_SIGN_ARTIFACT_PASS** |
| **REQ-RECON-003** | Disambiguate Box 2 NO vs $0.00 basis vs missing basis | [`edge/assurance/reconciliation_engine.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/edge/assurance/reconciliation_engine.py) | `test_adversarial_reconciliation_vectors.py` | Box 2 NO sample evaluation | Unreported basis test case | **PROD-GATE-15** | `evidence/box2_unreported_proof.json` | Assurance Lead | **SOURCE_PASS** / **MAC_PRE_SIGN_ARTIFACT_PASS** |
| **REQ-RCPT-001** | Normative receipt schema v0.1 conformance & immutability | [`schemas/receipt/receipt-v0.1.json`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/schemas/receipt/receipt-v0.1.json) | `test_receipt_contract_exhaustiveness.py` | Bundled verifier validation of packaged receipts | Receipt export & external verification | **PROD-GATE-16** (Feeds Gate 15) | `evidence/receipt_schema_v01_audit.json` | Protocol Lead | **SOURCE_PASS** / **MAC_PRE_SIGN_ARTIFACT_PASS** |
| **REQ-RCPT-002** | Ed25519 cryptographic receipt signing with local key | [`edge/receipts/signer.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/edge/receipts/signer.py) | `test_slice1_evidence_contract.py` | Keygen & sign in packaged runtime | Offline signature verification CLI | **PROD-GATE-16** | `evidence/ed25519_offline_sig_proof.json` | Security Lead | **SOURCE_PASS** / **MAC_PRE_SIGN_ARTIFACT_PASS** |
| **REQ-VERIF-001** | Standalone offline verifier requiring no VaultBasis installation, account, subscription, or network access | [`apps/verifier/verify_receipt.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/apps/verifier/verify_receipt.py) | `test_verifier.py` | Run verify_receipt.py against packaged artifacts | Packaged verifier execution on target OS | **PROD-GATE-17** | `evidence/offline_verifier_report.json` | Tools Lead | **SOURCE_PASS** / **MAC_PRE_SIGN_ARTIFACT_PASS** |
| **REQ-SEC-001** | Zero network egress during core case reconciliation | [`edge/api/app.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/edge/api/app.py) | `test_deploy_sec_001_behavioral.py` | Packet capture / socket audit on packaged runtime | Air-gapped network disabled execution | **PROD-GATE-09** / **PROD-GATE-18** (Feeds Gate 03) | `evidence/egress_packet_capture.pcap` | Security Lead | **SOURCE_PASS** / **MAC_PRE_SIGN_ARTIFACT_PASS** |
| **REQ-SEC-002** | Localhost binding only & Host/Origin/CORS/Capability defense | [`edge/api/app.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/edge/api/app.py) | `test_edge_security_qualification.py` | External curl hostile Host/Origin against running binary | LAN scan / 0.0.0.0 bind probe | **PROD-GATE-09** / **PROD-GATE-18** (Feeds Gate 01) | `evidence/network_boundary_audit.json` | Security Lead | **SOURCE_PASS** / **MAC_PRE_SIGN_ARTIFACT_PASS** |
| **REQ-LIFE-001** | Safe Quit lifecycle: SQLite WAL checkpoint, sockets closed, clean exit | [`edge/api/app.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/edge/api/app.py) | `test_edge_security_qualification.py` | Launch → Reconcile → Quit → Verify sockets freed | Task Manager / Activity Monitor inspection | **PROD-GATE-06** / **PROD-GATE-13** / **PROD-GATE-09** | `evidence/quit_lifecycle_evidence.json` | Frontend/Runtime Lead | **SOURCE_PASS** / **MAC_PRE_SIGN_ARTIFACT_PASS** |

---

## 3. Pre-Sign Candidate Artifact Ledgers & Supersession

| Artifact Name | Platform | SHA-256 Digest | Status | Lifecycle Qualification | Platform Signing Status |
|---|---|---|---|---|---|
| `VaultBasis-RC2-macOS-arm64.dmg` | macOS (arm64) | `18ebead1...` (RC2 build) | **SUPERSEDED** | Replaced by RC3 build | Obsolete |
| `VaultBasis-RC3-macOS-arm64.dmg` | macOS (arm64) | `1ce6fba1193ebbef60d0834b4dad1f83781129dfda2c91b6d7339138155b9204` | **CURRENT_PRE_SIGN_CANDIDATE** | **PASS** (MMP15-SEC-ARTIFACT-QUAL-001) | `NOT_RUN_PRE_SIGN` (Pending Apple Org Enrollment) |
| `VaultBasis-Setup-1.5.0-rc3.exe` | Windows (x64) | Staged (`scripts/installer_windows.py` SHA: `d5677dee...`) | **CURRENT_STAGED_PACKAGER** | **INCOMPLETE** (Awaiting Windows host compilation & execution) | `NOT_RUN_PRE_SIGN` (Pending Azure Public Trust validation) |

---

## 4. Installation Key & Data Durability Semantics Across Uninstall/Reinstall

1. **Standard Uninstall/Reinstall:** Preserves user data directory (`%LOCALAPPDATA%\VaultBasis` on Windows, `~/Library/Application Support/VaultBasis` on macOS), including SQLite database (`vaultbasis.db`), key material (`ed25519_key.json`), and issued receipts.
   * **Verification Criterion:** Pre-uninstall installation public-key fingerprint **must equal** post-reinstall installation public-key fingerprint (`fingerprint_pre == fingerprint_post`).
2. **Clean-Wipe Reinstall:** If the user manually removes the data directory prior to reinstallation, a new unguessable installation keypair is generated on first launch.
   * **Verification Criterion:** Old fingerprint **does not equal** new fingerprint (`fingerprint_old != fingerprint_new`), while previously exported historical receipts remain fully verifiable via standalone verifier because public keys are permanently bound to receipts.

---

## 5. PROD-GATE Status Summary & Release Control

### Aggregate Lifecycle Status
```json
{
  "source_qualification": "PASS",
  "macos_pre_sign_artifact_qualification": "PASS",
  "windows_pre_sign_artifact_qualification": "INCOMPLETE",
  "cross_platform_pre_sign_status": "INCOMPLETE",
  "platform_signing_status": "NOT_RUN",
  "physical_pre_sign_status": "NOT_RUN",
  "physical_post_sign_status": "NOT_RUN",
  "production_release_status": "BLOCKED"
}
```

### Frozen Canonical Gate Dispositions

| Gate | Frozen Canonical Meaning | Status | Subrequirement & Evidence Controls |
|---|---|---|---|
| **PROD-GATE-01** | **Distribution Authorization / Token Gate** | `FUNCTIONALLY_QUALIFIED` | Zero Token Bleed (`SOURCE_PASS`), Vercel Route Parity (`SOURCE_PASS`), Loopback Auth (`SOURCE_PASS`) |
| **PROD-GATE-02** | **Commercial Plan / Mailer Copy** | `SOURCE_QUALIFIED` | Catalog Integrity (`SOURCE_PASS`), Pricing Parity (`SOURCE_PASS`), Delivery Mailer (`SOURCE_PASS`) |
| **PROD-GATE-03** | **Air-Gapped License Provisioning** | `OPEN` | Offline License Activation Protocol (`SOURCE_PASS`), End-to-End Physical Journey (`PENDING`) |
| **PROD-GATE-04** | **Monotonic Revision** | `SOURCE_QUALIFIED` | Monotonic Revision & Anti-Rollback Vectors (`SOURCE_PASS`) |
| **PROD-GATE-05** | **In-App Activation** | `SOURCE_QUALIFIED` | In-App License Activation Engine (`SOURCE_PASS`), Physical Packaged Test (`PENDING`) |
| **PROD-GATE-06** | **Restart Persistence** | `SOURCE_QUALIFIED + MAC_ARTIFACT_QUALIFIED` | WAL Checkpoint & Restart Verification (`MAC_PRE_SIGN_PASS`), Windows Runtime (`PENDING`) |
| **PROD-GATE-07** | **Windows Signing (Authenticode)** | `NOT_RUN_PRE_SIGN` | Azure Artifact Signing Public Trust Identity Validation (`IN_FLIGHT`) |
| **PROD-GATE-08** | **macOS Signing / Notarization** | `NOT_RUN_PRE_SIGN` | Apple Developer ID Application Signing, Hardened Runtime, Notarization & Stapling (`IN_FLIGHT`) |
| **PROD-GATE-09** | **Clean-Machine Launch (Physical UAT)** | `NOT_RUN_PRE_SIGN` | Clean OS Execution Smoke on Unsigned Pre-Sign RC3 (`PENDING`) |
| **PROD-GATE-10** | **Release Manifest Immutability / Commit Binding** | `PRE_SIGN_EVIDENCE_AVAILABLE` | Commit Hash Binding, Pre-Sign SHA-256 Catalog (`MAC_PASS`, `WIN_PENDING`) |
| **PROD-GATE-11** | **Distribution Active / Anti-Rollback** | `OPEN` | Web Distribution Gateway Activation (`BLOCKED_UNTIL_RELEASE`) |
| **PROD-GATE-12** | **SPF / DKIM / DMARC** | `OPEN_EXTERNAL` | DNS Records Verification on production domain (`OPEN_EXTERNAL`) |
| **PROD-GATE-13** | **UAT Platform Quota** | `OPEN_PHYSICAL_UAT` | Evaluation Capacity & Quota Smoke on Clean Hardware (`PENDING`) |
| **PROD-GATE-14** | **Unassisted Intake / Provenance** | `SOURCE_QUALIFIED` | Intake Validation, Schema Fuzzing, Provenance Tracking (`SOURCE_PASS`, `MAC_PRE_SIGN_PASS`) |
| **PROD-GATE-15** | **Deterministic Reconciliation & Decimal Precision** | `SOURCE_QUALIFIED + MAC_ARTIFACT_QUALIFIED` | Exact Decimal Arithmetic, Box 2 NO, Adversarial Reconciliation Vectors (`SOURCE_PASS`, `MAC_PRE_SIGN_PASS`) |
| **PROD-GATE-16** | **Signed Export & Integrity** | `MAC_PRE_SIGN_QUALIFIED` | Ed25519 Cryptographic Receipt Generation, Anti-Tamper Verification (`SOURCE_PASS`, `MAC_PRE_SIGN_PASS`) |
| **PROD-GATE-17** | **Standalone Offline Verifier** | `MAC_PRE_SIGN_QUALIFIED` | Standalone `verify_receipt.py` Execution against packaged artifacts (`SOURCE_PASS`, `MAC_PRE_SIGN_PASS`) |
| **PROD-GATE-18** | **Final Launch Authorization / MMP2** | `BLOCKED` | Distribution Activation Prohibited until all 17 precursor gates are closed |

---

## 6. Windows Pre-Sign Artifact Qualification Protocol (`MMP15-WIN-ARTIFACT-QUAL-001`)

### 6.1 Dual-Binding & Dependency-Aware Invalidation Invariants
1. **Dual Cryptographic Binding:** Windows qualification binds both the customer installer (`VaultBasis-Setup-1.5.0-rc3.exe` SHA-256) and the installed runtime (`%LOCALAPPDATA%\VaultBasis\VaultBasis.exe` SHA-256).
2. **Dependency-Aware Invalidation Rule:**
   - Any shared-source code modification made to resolve a Windows issue immediately invalidates previously qualified macOS artifact evidence, requiring complete macOS re-qualification.
   - Windows-only packaging, installer metadata, or script changes invalidate Windows qualification only, unless modifying shared runtime code or shared release inputs.

### 6.2 Binary Failure-Stop Conditions (Any Occurrence $\implies$ `WIN_PRE_SIGN_FAIL`)
* Visible CMD / PowerShell / console window during launch or execution
* LAN socket binding or `0.0.0.0` listening interface
* Cross-origin or unauthenticated `Origin: null` mutation succeeds (403 required)
* Port collision routes traffic to the wrong process or allows duplicate background servers
* Unexpected outbound network egress connection during reconciliation
* Reconciliation output diverges from golden source baseline
* Generated receipt fails validation against bundled standalone offline verifier
* Routine uninstall removes client database (`vaultbasis.db`) or key storage (`ed25519_key.json`)
* Reinstall fails to restore access to existing historical cases
* Binary loads any DLL from untrusted/writable search paths (DLL hijacking vulnerability)
* Undispositioned Windows Defender detection
* Secret or private key material found in installation package
* Crash or restart leaves database corruption, half-issued evidence, or inconsistent case state
* SBOM / CVE scan contains an unresolved exploitable Critical/High release blocker
* Installed runtime hash does not match the hash recorded by the qualification packet
* Installation footprint contains undeclared service, scheduled task, startup item, firewall rule, or PATH mutation

### 6.3 Machine-Readable Qualification Schema
```json
{
  "qualification_id": "MMP15-WIN-ARTIFACT-QUAL-001",
  "installer_name": "VaultBasis-Setup-1.5.0-rc3.exe",
  "installer_sha256": "...",
  "installed_executable_sha256": "...",
  "source_commit": "...",
  "sbom_sha256": "...",
  "qualification_report_sha256": "...",
  "platform": "windows-x64",
  "source_qualification": "PASS",
  "installer_qualification": "PASS",
  "runtime_security": "PASS",
  "network_egress": "PASS",
  "air_gap": "PASS",
  "golden_reconciliation": "PASS",
  "receipt_roundtrip": "PASS",
  "tamper_detection": "PASS",
  "restart_persistence": "PASS",
  "crash_consistency": "PASS",
  "uninstall_reinstall": "PASS",
  "secret_scan": "PASS",
  "sbom_cve": "PASS",
  "defender": "PASS",
  "dll_hijack_negative": "PASS",
  "mandatory_not_run": [
    "PROD-GATE-07_WINDOWS_SIGNING"
  ],
  "overall": "WIN_PRE_SIGN_PASS"
}
```
