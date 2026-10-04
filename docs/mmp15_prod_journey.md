# VaultBasis MMP-1.5 Production Practitioner Journey & Enterprise Trust Architecture (MMP15-PROD-001)

> **MMP-2 IMPLEMENTATION INVARIANT:**  
> **MMP-2 implementation remains blocked until VaultBasis proves the complete MMP-1.5 production journey—from first web visit through trusted installation, licensed case completion, evidence export, independent verification, persistence, and support—on production-equivalent infrastructure with first-time practitioners.**

---

## 1. The Commercial Dilemma & The Four Pillars of Trust

When an unfamiliar CPA, Enrolled Agent (EA), or tax professional downloads VaultBasis, their primary hesitation is never: *"Is the reconciliation math sound?"*  
Their immediate fear is:
> **"Will this executable harm my laptop, trigger corporate IT alerts, leak confidential client workpapers, or install hidden background services?"**

If VaultBasis cannot answer this fear visibly, frictionlessly, and with cryptographic certainty, commercial adoption stalls regardless of core technical excellence.

```
                      ┌─────────────────────────────────────────────────────────┐
                      │              THE FOUR PILLARS OF TRUST                  │
                      └─────────────────────────────────────────────────────────┘
                                                   │
         ┌───────────────────┬─────────────────────┴─────────────────────┬───────────────────┐
         ▼                   ▼                                           ▼                   ▼
┌─────────────────┐ ┌─────────────────┐                         ┌─────────────────┐ ┌─────────────────┐
│  BINARY TRUST   │ │  RUNTIME TRUST  │                         │ENTERPRISE TRUST │ │COMMERCIAL TRUST │
├─────────────────┤ ├─────────────────┤                         ├─────────────────┤ ├─────────────────┤
│• Authenticode   │ │• 127.0.0.1 loop │                         │• IT Deploy Pack │ │• Trust Center   │
│  (RFC 3161)     │ │• No case egress │                         │• CycloneDX SBOM │ │• Clear pricing  │
│• Apple Developer│ │• No admin rights│                         │• Allowlist spec │ │• Auth'd emails  │
│  ID Notarization│ │• Zero case      │                         │• Intune/MDM doc │ │• Signed dl URLs │
│• SHA-256 Digest │ │  telemetry      │                         │• Silent install │ │• EULA & Privacy │
│• CI Malware Scan│ │• Never asks for │                         │  specification  │ │  commitments    │
│                 │ │  crypto keys/pwd│                         │                 │ │                 │
└─────────────────┘ └─────────────────┘                         └─────────────────┘ └─────────────────┘
```

---

## 2. Trust Claims Lifecycle & Evidence States

To maintain strict engineering and brand integrity, **VaultBasis never publishes a marketing or security claim on its website or documentation merely because the architecture intends it.** Every public statement must progress through five verifiable evidence states:

```
[ PLANNED ] ──► [ IMPLEMENTED ] ──► [ VERIFIED ] ──► [ PRODUCTION_QUALIFIED ] ──► [ PUBLICLY_CLAIMABLE ]
```

| State | Definition | Gate Requirement |
|---|---|---|
| **`PLANNED`** | Architectural goal or documented specification. | Internal RFC / Ledger task defined. |
| **`IMPLEMENTED`** | Code written and merged into `main`. | Unit and automated domain tests passing. |
| **`VERIFIED`** | Proven in clean local automated environments. | 11/11 Industrial Validation Gates passing. |
| **`PRODUCTION_QUALIFIED`** | Proven on physical target OS without development tooling or bypasses. | Clean-machine Gatekeeper / SmartScreen acceptance; physical air-gap receipt verification. |
| **`PUBLICLY_CLAIMABLE`** | Formally authorized for display on `vaultbasis.com` and public Trust Center. | Signed release artifact digest published in immutable release manifest. |

### Evidence State Matrix for Core Commercial Claims
| Public Claim | Required Evidence Level | Current State | Evidence Reference |
|---|---|---|---|
| *"Digitally signed Windows executable"* | `PRODUCTION_QUALIFIED` | `IMPLEMENTED` | `MMP15-PROD-WIN-SIGN-001` (RFC 3161 Authenticode CI pipeline) |
| *"Apple Developer ID Notarized & Stapled"* | `PRODUCTION_QUALIFIED` | `IMPLEMENTED` | `MMP11-DIST-MAC-004` (Notarization ticket stapling) |
| *"No case-data egress during processing"* | `VERIFIED` | `VERIFIED` | `AC07_OS_Level_Egress_Evidence.md` (Zero non-loopback sockets) |
| *"No administrator privileges required"* | `PRODUCTION_QUALIFIED` | `VERIFIED` | Standard user context execution test on Windows & macOS |
| *"Malware & vulnerability scanned"* | `PRODUCTION_QUALIFIED` | `PLANNED` | Multi-engine AV scan & CycloneDX SBOM generation in CI |
| *"No runtime telemetry from case processing"*| `VERIFIED` | `VERIFIED` | Codebase audit: zero telemetry hooks in `edge/` runtime |
| *"Never requests private keys or passwords"* | `VERIFIED` | `VERIFIED` | Zero seed phrase/credential inputs in domain schemas |
| *"Authenticated temporary download links"* | `PRODUCTION_QUALIFIED` | `PLANNED` | `MMP15-PROD-DL-001` (HMAC-signed expiring URLs) |

---

## 3. Empirical UAT Finding: Pre-Installation Trust Barrier

```
FINDING ID:      UAT-FINDING-001
DATE:            2026-10-04
STAGE:           Pre-Installation & Download
TEST SUBJECT:    External Professional Associate (First-Time User Simulation)

OBSERVATION:
The test subject hesitated and declined to launch the downloaded VaultBasis executable on their
primary work laptop, citing concerns about whether the unverified binary could harm their machine,
trigger corporate endpoint security alarms, or violate firm software policies.

ROOT CAUSE ANALYSIS:
1. Binary Provenance Gap: Unsigned direct ZIP distribution triggers OS reputation warnings.
2. Context Vacuum: Lack of a pre-download "Why this download is safe" panel explaining local execution.
3. Enterprise IT Friction: Absence of an IT-ready deployment pack (SBOM, allowlisting guide) for firm-governed PCs.
4. Transparency Gap: Missing public Trust Center explaining network, filesystem, and privilege boundaries.

MAPPED REMEDIATIONS:
• MMP15-PROD-TRUST-001:  Windows Authenticode & macOS Developer ID signing/notarization.
• MMP15-PROD-TRUSTWEB-001: Pre-download Trust Panel & Trust Center at vaultbasis.com/trust.
• MMP15-PROD-ENT-001:     Enterprise IT Deployment & Security Profile artifact.
• MMP15-PROD-SEC-002:     Published SHA-256 digests, SBOM, and recorded CI malware scans.
```

---

## 4. Dual Customer Persona Journeys

### Path A: Self-Managed Practitioner (Solo CPA / Independent EA)
```
[ www.vaultbasis.com ] ──► [ Value & Pricing ] ──► [ "Why It's Safe" Panel ] ──► [ Request / Buy License ]
                                                                                         │
[ Open Application ] ◄── [ Extract & Launch ] ◄── [ OS Validates Signature ] ◄── [ Transactional Email ]
        │                                                                                │
        ▼                                                                                ▼
[ Privacy Screen ] ──► [ Onboarding / Sample A ] ──► [ Real Case Intake ] ──► [ Reconcile & Verify Receipt ]
```

### Path B: Firm-Managed Practitioner (Enterprise / Multi-Seat CPA Firm)
```
[ www.vaultbasis.com ] ──► [ "Managed Work Computer?" ] ──► [ Send to IT: Enterprise Security Pack ]
                                                                            │
┌───────────────────────────────────────────────────────────────────────────┴───────────────────────┐
│                                ENTERPRISE IT ASSESSMENT & APPROVAL                                │
│  • Review Publisher Identity & RFC 3161 Certificate                                               │
│  • Inspect CycloneDX SBOM & Vulnerability Profile                                                 │
│  • Verify Localhost-Only Network Boundary (127.0.0.1) & Zero Admin Elevation                      │
│  • Configure Endpoint Allowlisting (Intune / Defender / SentinelOne / Jamf)                       │
└───────────────────────────────────────────────────────────────────────────┬───────────────────────┘
                                                                            ▼
[ Firm License Activation ] ◄── [ Practitioner Receives Installed App ] ◄── [ IT Managed Deployment ]
        │
        ▼
[ Workspace Identity Setup ] ──► [ Multi-Lot Reconciliation ] ──► [ Workpaper Export & Independent Verification ]
```

---

## 5. Five Parallel Execution Lanes for MMP15-PROD-001

To prevent serial bottlenecks, commercial launch qualification is organized into five parallel execution tracks:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   MMP15-PROD-001 EXECUTION LANES                                        │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
        │                     │                     │                     │                     │
        ▼                     ▼                     ▼                     ▼                     ▼
  ┌───────────┐         ┌───────────┐         ┌───────────┐         ┌───────────┐         ┌───────────┐
  │  LANE A   │         │  LANE B   │         │  LANE C   │         │  LANE D   │         │  LANE E   │
  │Production │         │Acquisition│         │   Trust   │         │  Product  │         │   Human   │
  │ Artifacts │         │ & Delivery│         │ Evidence  │         │Onboarding │         │    UAT    │
  ├───────────┤         ├───────────┤         ├───────────┤         ├───────────┤         ├───────────┤
  │• Win Sign │         │• Checkout │         │• TrustWeb │         │• 4 Sample │         │• 5-8 CPAs │
  │• Mac Notar│         │• Tx Email │         │• IT Pack  │         │  Journeys │         │• Unguided │
  │• SBOM/Scan│         │• Signed DL│         │• Manifest │         │• Privacy  │         │• Trust    │
  │• Gatekeepr│         │  URLs     │         │• Vuln Disc│         │  Screen   │         │  Friction │
  └───────────┘         └───────────┘         └───────────┘         └───────────┘         └───────────┘
```

### Lane A: Production Binary Trust
- `MMP15-PROD-WIN-SIGN-001`: Windows Authenticode code signing with RFC 3161 timestamping; SmartScreen reputation readiness.
- `MMP11-DIST-MAC-004`: macOS Developer ID signing, Apple notarization ticket, and stapling.
- `MMP15-PROD-SEC-002`: Multi-engine malware scanning and CycloneDX SBOM release generation.

### Lane B: Acquisition & Secure Delivery
- `MMP15-PROD-COM-001`: Commercial purchase and trial request orchestration engine.
- `MMP15-PROD-MAIL-001`: Transactional email delivery with SPF/DKIM/DMARC authentication.
- `MMP15-PROD-DL-001`: Authenticated artifact delivery service with expiring HMAC-signed download URLs.

### Lane C: Trust Evidence & Enterprise Readiness
- `MMP15-PROD-TRUSTWEB-001`: Production Trust Center (`vaultbasis.com/trust`) and pre-download trust panel.
- `MMP15-PROD-ENT-001`: Enterprise IT Deployment & Security Profile (`VaultBasis_IT_Deployment_and_Security_Profile.md`).
- `MMP15-PROD-VULN-001`: Responsible Vulnerability Disclosure policy and security contact route (`security@vaultbasis.com`).

### Lane D: Product Onboarding & Native Trust Experience
- `MMP15-PROD-ONB-001`: First-run screen with explicit privacy summary and 4 controlled samples (Clean 1099-DA, Multi-Exchange, Basis Gap, Tampered Receipt).
- `MMP15-PROD-UPG-001`: In-place application upgrade qualification preserving existing databases, receipts, and licenses.
- `MMP15-PROD-REC-001`: 1-click database backup and transactional restore verification.

### Lane E: Human Observed Qualification
- `MMP15-PROD-UAT-001`: Structured, unguided UAT sessions with 5–8 CPAs measuring trust friction, time-to-value, and willingness to buy.

---

## 6. The 18 Industrial Production Release Gates (PROD-GATES)

Before VaultBasis is declared **`PRODUCTION_RELEASE = YES`**, the release authority must verify all 18 gates:

| Gate ID | Release Requirement | Verification Standard |
|---|---|---|
| **`PROD-GATE-01`** | **Value Comprehension** | Unfamiliar CPA understands product purpose and scope in < 15 seconds. |
| **`PROD-GATE-02`** | **Pricing Transparency** | Tier, case capacity, and renewal rules fully clear without sales contact. |
| **`PROD-GATE-03`** | **Transactional Email** | Purchase/license emails arrive in inbox within 2 minutes across major mail providers. |
| **`PROD-GATE-04`** | **Secure Delivery** | Downloads served via authenticated, expiring signed links; no directory listings. |
| **`PROD-GATE-05`** | **Windows Binary Trust** | Executable signed with valid Authenticode certificate & RFC 3161 timestamp; verified offline. |
| **`PROD-GATE-06`** | **macOS Binary Trust** | Apple Developer ID signed, notarized, stapled; clean Gatekeeper pass without `xattr` bypass. |
| **`PROD-GATE-07`** | **Artifact Security & SBOM** | CycloneDX SBOM generated; zero critical/high unmitigated CVEs; malware scan clean. |
| **`PROD-GATE-08`** | **Localhost Runtime Boundary**| Sockets bind exclusively to `127.0.0.1`; local session auth token enforced; zero case egress. |
| **`PROD-GATE-09`** | **First-Run Onboarding** | Welcome screen displays privacy facts; Sample A runs to completion in < 60 seconds. |
| **`PROD-GATE-10`** | **Real Case Lifecycle** | Ingest $\rightarrow$ reconcile $\rightarrow$ exception inspect $\rightarrow$ Form 8949 worksheet output complete. |
| **`PROD-GATE-11`** | **Independent Verification** | Evidence bundle transferred to separate machine and verified successfully via offline verifier. |
| **`PROD-GATE-12`** | **Restart & Persistence** | Closing and reopening app recovers 100% of cases, firm identity, license, and audit log. |
| **`PROD-GATE-13`** | **Durability & Recovery** | Online backup creates valid snapshot; restore recovers exact state with zero corruption. |
| **`PROD-GATE-14`** | **In-Place Upgrade Safety**| Upgrading to newer version discovers existing DB, applies migrations, and leaves past receipts verifiable. |
| **`PROD-GATE-15`** | **Enterprise IT Package** | IT Deployment & Security Profile document reviewed and accepted for Intune/Defender allowlisting. |
| **`PROD-GATE-16`** | **Sanitized Diagnostics** | Exported `diagnostic.zip` verified to contain manifest and zero client PII or unmasked PTIN/EFIN. |
| **`PROD-GATE-17`** | **Legal & Privacy Boundaries**| EULA, Privacy Statement, and Tax/Legal Disclaimers finalized and published. |
| **`PROD-GATE-18`** | **First-Time UAT Sign-Off** | 5–8 unguided CPA test sessions confirm trust confidence, successful case completion, and commercial intent. |

---

## 7. Enterprise IT Deployment & Security Profile Specification

The companion artifact [`docs/enterprise/VaultBasis_IT_Deployment_and_Security_Profile.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/enterprise/VaultBasis_IT_Deployment_and_Security_Profile.md) defines the exact technical posture for enterprise security reviewers:

1. **Publisher Identity & Code Signing:** Legal publisher details, certificate issuer, and verification commands.
2. **Execution Privileges:** Standard user space only (`%LOCALAPPDATA%` on Windows, `/Applications` or `~/Applications` on macOS); zero Administrator elevation required.
3. **Network Behavior:** Strict loopback binding (`127.0.0.1:8000` default, dynamic fallback); **zero outbound network connections during case processing**.
4. **Filesystem Boundaries:** Reads only explicitly selected practitioner files; writes only to isolated application data directory; zero modifications to system registries or kernel extensions.
5. **Data Storage & Encryption:** Local SQLite database with WAL durability; AES-GCM local protection for regulated identifiers (PTIN/EFIN).
6. **Telemetry Policy:** Zero runtime telemetry, usage tracking, or token logging from case processing.
7. **Allowlisting Signatures:** Executable paths, hash algorithms, and MDM / Intune deployment configurations.
8. **Vulnerability Disclosure:** Responsible disclosure contact at `security@vaultbasis.com`.
