# VaultBasis Release Revocation & Compromised Key Incident Runbook
**Document ID:** VB-RUN-REVOKE-001  
**Classification:** OPERATIONAL  
**Authority:** Security Lead / Release Authority  
**Status:** IMPLEMENTATION_ALIGNED  
**Applies To:** Emergency Binary Revocation, Signing Key Compromise, or Key Lifecycle Incidents  
**Last Reviewed:** 2026-10-08  

---

## 1. Incident Severity & Trust Domain Separation

VaultBasis maintains strict cryptographic domain separation across five distinct trust domains. Revocation procedures must target the specific affected domain without cross-wire assumptions:

| Trust Domain | Scope & Artifact | Authority / Infrastructure | Domain-Specific Revocation Mechanism |
|---|---|---|---|
| **Windows Authenticode** | `VaultBasis-Setup.exe` Windows binaries | Microsoft Azure / CA (DigiCert) | CA-level certificate revocation via CRL / OCSP; Microsoft SmartScreen reputation invalidation. |
| **macOS Developer ID** | `VaultBasis.app` / `.dmg` bundles | Apple Developer Program / Notary | Revoke Apple Notarization ticket via `xcrun notarytool revoke <submission-id>`; revoke Developer ID certificate via Apple Developer Portal. |
| **Commercial License Key** | Paid Ed25519 License Tokens | VaultBasis Commercial Authority | VaultBasis commercial signing key rotation & monotonic revision sequence bump (`revision_seq` counter); no generic CRL/OCSP. |
| **Local Evidence Signing Key** | Ed25519 Installation Keys | Local CPA Endpoint | Local key regeneration upon clean wipe; historical receipts remain valid and verifiable because the original public key is permanently bound to the receipt. |
| **Release Distributable** | Pre-sign / Post-sign Binaries | Public Distribution Router | Distribution state update to `status: REVOKED` / `SUPERSEDED` in `release-manifest.json` and web gateway disarm. |

---

## 2. Emergency Revocation Protocols by Domain

### 2.1 Release Artifact Compromise or Critical Defect
1. **Disarm Gateway:** Update web distribution router to immediately stop serving the affected build.
2. **Revoke Manifest:** In `release-manifest.json`, set the affected artifact SHA-256 state to `"status": "REVOKED"`.
3. **Advisory Notice:** Publish cryptographic advisory listing the exact revoked and replacement SHA-256 digests.

### 2.2 Platform Signing Key Compromise
* **Windows Authenticode:** Notify Azure Artifact Signing and Certificate Authority to revoke compromised signing certificate. Re-sign release with newly provisioned certificate.
* **macOS Developer ID:** Revoke compromised certificate in Apple Developer Account; revoke notary tickets for affected submissions; re-sign and re-notarize with new Developer ID credentials.

### 2.3 Commercial License Signing Key Compromise
1. Generate new Ed25519 Commercial License Authority keypair.
2. Bump `license_protocol_version` or root key lineage identifier.
3. Issue replacement license tokens to active commercial customers using the new key.
4. Old tokens with superseded root keys are rejected once edge engines update their bundled root public key.

### 2.4 Evidence & Historical Receipt Integrity
* **Immutability Guarantee:** Compromise of an operating system signing certificate or commercial license key does **not** invalidate historical customer evidence receipts, as each receipt is independently signed by the CPA's local installation key and verified offline.
