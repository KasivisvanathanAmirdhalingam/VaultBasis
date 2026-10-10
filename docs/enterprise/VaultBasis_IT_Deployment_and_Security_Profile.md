# VaultBasis Enterprise IT Deployment & Security Profile

> **Target Audience:** Enterprise IT Administrators, CISO Teams, Security Reviewers, Compliance Officers  
> **Document Version:** 1.0 (Production Candidate)  
> **Scope:** VaultBasis Edge Application Runtime (Windows x64 & macOS Apple Silicon / Intel)  
> **Classification:** Public / IT Evaluation Package  

---

## 1. Executive Summary & Architectural Overview

VaultBasis is a professional, local-first tax workpaper and digital-asset tax basis reconciliation engine designed specifically for CPAs, Enrolled Agents (EAs), and tax controversy practitioners.

Unlike SaaS compliance platforms that require uploading confidential taxpayer transaction histories and wallet balances to third-party cloud infrastructure, **VaultBasis operates 100% locally on the practitioner's endpoint**. All transaction parsing, lot matching, tax basis math, and cryptographic receipt generation occur strictly in local memory and local persistence.

---

## 2. Technical Profile & System Specifications

| Architectural Dimension | Specification & Boundary |
|---|---|
| **Binary Executable Names** | `VaultBasis.exe` (Windows x64) / `VaultBasis.app` (macOS Universal) |
| **Supported Operating Systems** | Windows 10/11 (64-bit), macOS 13+ (Ventura, Sonoma, Sequoia) |
| **Installation Footprint** | ~120 MB self-contained binary distribution |
| **Execution Privileges** | **Standard User Space Only** (No Administrator / root elevation required) |
| **Installation Location** | Windows: `%LOCALAPPDATA%\VaultBasis\` or extracted standalone folder<br>macOS: `/Applications/VaultBasis.app` or `~/Applications/VaultBasis.app` |
| **Application Data Location** | Windows: `%LOCALAPPDATA%\VaultBasis\`<br>macOS: `~/Library/Application Support/VaultBasis/` |
| **Network Listeners** | Loopback interface only (`127.0.0.1:8000` default, dynamic ephemeral fallback) |
| **Outbound Network Access** | **Zero required outbound connections during case reconciliation or receipt verification.** |
| **Background Services / Daemons** | **None.** Process terminates fully upon window close; zero persistent system daemons. |
| **Registry / System Modifications**| **Zero.** No kernel drivers, system-wide proxies, browser extensions, or scheduled tasks. |

---

## 3. Binary Provenance & Code Signing Architecture

Every production release of VaultBasis is cryptographically signed and independently verifiable prior to execution:

### Windows Executable Signing
- **Certificate Standard:** Authenticode X.509 Code Signing Certificate issued by a trusted Commercial Certificate Authority.
- **Timestamping Authority:** RFC 3161 compliant timestamping server ensuring signatures remain valid post certificate expiration.
- **Verification Command:**
  ```powershell
  Get-AuthenticodeSignature -FilePath ".\VaultBasis.exe"
  ```
- **Expected Status:** `Valid`, Publisher: `VaultBasis LLC / TecTixBase Commercial Operations`.

### macOS Application Signing & Notarization
- **Developer ID Signing:** Apple Developer ID Application certificate.
- **Hardened Runtime:** Compiled with Apple Hardened Runtime flags (`--options runtime`).
- **Apple Notarization:** Scanned and notarized by Apple Notary Service with stapled notarization ticket.
- **Verification Command:**
  ```bash
  spctl -a -vvv -t install /Applications/VaultBasis.app
  ```
- **Expected Status:** `accepted`, source=`Notarized Developer ID`.

---

## 4. Network Boundary & Egress Denial

```
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                      LOCAL ENDPOINT SECURITY BOUNDARY                       │
  │                                                                             │
  │  ┌───────────────────────┐         Local Loopback        ┌──────────────┐   │
  │  │   Practitioner UI     │ ◄───────────────────────────► │ Local Core   │   │
  │  │ (Embedded Web Engine) │      (127.0.0.1:8000 +        │ SQLite Store │   │
  │  └───────────────────────┘    Ephemeral Session Token)   └──────────────┘   │
  │                                                                             │
  │  ───────────────────────────────── FIREWALL ──────────────────────────────  │
  │                                                                             │
  │   [ ZERO OUTBOUND TELEMETRY ]  [ ZERO CLOUD DATABASE ]  [ ZERO AI EGRESS ]  │
  └─────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼ (PHYSICALLY DENIED)
                                   [ EXTERNAL INTERNET ]
```

1. **Loopback Isolation:** The internal service interface binds exclusively to `127.0.0.1`. It rejects any interface binding to `0.0.0.0` or external LAN IP addresses.
2. **Session Authentication:** Communication between the UI front-end and the local core is authenticated via an ephemeral token (`X-VaultBasis-Session-Token`) generated randomly at startup.
3. **Zero Case Telemetry:** VaultBasis does **not** transmit taxpayer identification, wallet addresses, transaction rows, capital gains calculations, or receipt contents to VaultBasis servers or third parties.

---

## 5. Filesystem Access & Least Privilege Model

VaultBasis adheres strictly to the principle of least privilege:
- **Files Read:** The application reads files **only** when explicitly selected by the practitioner via OS file picker dialogs (e.g., Form 1099-DA CSVs, broker tax-lot exports, license `.lic` tokens).
- **Files Written:**
  - Local database: `vaultbasis.db` and temporary WAL files inside the designated user application data directory using **`SQLite WAL mode (PRAGMA synchronous = FULL)`** for enterprise-grade write durability.
  - User-directed exports: Reconciled Form 8949 CSVs, audit workpapers, and cryptographic evidence packages saved strictly to practitioner-selected folders.
  - Sanitized support diagnostics: User-initiated `diagnostic.zip` exports (zero transaction rows, zero client PII, zero unmasked PTIN/EFIN).
- **Independent Offline Verification:** Evidence bundles can be verified on an air-gapped machine using the frozen standalone verifier script (`apps/verifier/verify.py`), completely independent of the VaultBasis runtime.

---

## 6. Software Bill of Materials (SBOM) & Vulnerability Management

- **SBOM Standard:** CycloneDX JSON and SPDX formats generated at build time for every qualified release.
- **Dependency Isolation:** All Python and native runtime components are packaged into the standalone application container, preventing conflicts with enterprise Python or DLL environments.
- **Vulnerability Scanning:** Automated CI pipelines execute dependency CVE analysis and multi-engine malware scanning prior to release signing.

---

## 7. Enterprise Allowlisting & Deployment Guidelines

### Microsoft Intune / Defender for Endpoint Allowlisting
- **Rule Type:** Publisher Rule (Recommended) or Path Rule.
- **Publisher Name:** `CN=VaultBasis LLC, O=VaultBasis LLC, L=New York, S=NY, C=US` (Exact DN from certificate).
- **File Path:** `%LOCALAPPDATA%\VaultBasis\VaultBasis.exe`.
- **Silent Install Flags:** `VaultBasis-Setup-1.5.0-rc3.exe` (user-space self-extractor into `%LOCALAPPDATA%\VaultBasis`).

### Jamf Pro / macOS MDM Configuration
- **Payload:** Application Restriction / Gatekeeper Bypass Exception.
- **Team ID:** Provided upon enterprise contract execution.
- **Bundle Identifier:** `com.vaultbasis.desktop`.

---

## 8. Responsible Security Disclosure

VaultBasis operates a dedicated, responsible vulnerability disclosure program:
- **Security Contact:** `security@vaultbasis.com`
- **PGP Key:** Available at `https://www.vaultbasis.com/.well-known/security.txt`
- **Policy:** We acknowledge vulnerability reports within 24 business hours and coordinate responsible mitigation prior to public disclosure.
