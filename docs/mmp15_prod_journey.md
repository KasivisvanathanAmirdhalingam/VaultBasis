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
- `MMP15-PROD-MAIL-001`: Transactional email delivery with SPF/DKIM/DMARC authentication (license issued, purchase confirmation, download link, expiry/resend, support acknowledgement; **strictly zero client evidence receipt egress**).
- `MMP15-PROD-DL-001`: Authenticated artifact delivery service with expiring HMAC-signed download URLs.

### Lane C: Trust Evidence & Enterprise Readiness
- `MMP15-PROD-TRUSTWEB-001`: Production Trust Center (`vaultbasis.com/trust`) and pre-download trust panel.
- `MMP15-PROD-ENT-001`: Enterprise IT Deployment & Security Profile (`VaultBasis_IT_Deployment_and_Security_Profile.md`).
- `MMP15-PROD-VULN-001`: Responsible Vulnerability Disclosure policy and security contact route (`security@vaultbasis.com`).

### Lane D: Product Onboarding & Native Trust Experience
- `MMP15-PROD-ONB-001`: First-run screen with explicit privacy summary, About/System Information panel, and 4 controlled evaluation samples (Clean 1099-DA, Multi-Exchange, Basis Gap, Tampered Receipt).
- `MMP15-PROD-UPG-001`: In-place application upgrade qualification preserving existing databases, receipts, and licenses.
- `MMP15-PROD-REC-001`: 1-click database backup and transactional restore verification.

### Lane E: Human Observed Qualification
- `MMP15-PROD-UAT-001`: Structured, unguided UAT sessions with 5–8 CPAs measuring trust friction, hesitation, time-to-value, and willingness to buy under zero developer intervention.

---

## 6. Distinct Production Cryptographic Key Domains

To ensure robust security architecture, VaultBasis strictly isolates five distinct cryptographic key domains with zero cross-use:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        VAULTBASIS CRYPTOGRAPHIC TRUST DOMAINS                          │
├────────────────────────────────┬──────────────────────┬────────────────────────────────┤
│ Trust Domain                   │ Key Type / Standard  │ Purpose & Security Boundary    │
├────────────────────────────────┼──────────────────────┼────────────────────────────────┤
│ 1. Evidence Receipt Signing    │ Ed25519 (Private)    │ Local case evidence authenticity│
│ 2. Commercial License Signing  │ Ed25519 (Private)    │ Entitlement token authenticity │
│ 3. Windows Code Signing        │ Authenticode (X.509) │ Software publisher identity    │
│ 4. macOS Developer ID          │ Apple Dev ID (X.509) │ macOS Gatekeeper & Notarization│
│ 5. Release Manifest Authority  │ Independent Key/HTTPS│ Release metadata authenticity  │
└────────────────────────────────┴──────────────────────┴────────────────────────────────┘
```
*Compromise or rotation in one trust domain never impacts or invalidates keys in another domain.*

---

## 7. The 18 Industrial Production Release Gates (PROD-GATES)

Before VaultBasis is declared **`PRODUCTION_RELEASE = YES`**, the release authority must verify all 18 gates:

| Gate ID | Release Requirement | Verification Standard |
|---|---|---|
| **`PROD-GATE-01`** | **Value Comprehension** | Unfamiliar CPA understands product purpose and scope in < 15 seconds. |
| **`PROD-GATE-02`** | **Pricing Transparency** | Tier, case capacity, and renewal rules fully clear without sales contact. |
| **`PROD-GATE-03`** | **Transactional Email** | Purchase/license emails arrive in inbox within 2 minutes across major mail providers; zero evidence data. |
| **`PROD-GATE-04`** | **Secure Delivery** | Downloads served via authenticated, expiring signed links; clean SHA-256 release manifest (`release-manifest.json`). |
| **`PROD-GATE-05`** | **Windows Binary Trust** | Executable signed with valid Authenticode certificate & RFC 3161 timestamp; verified offline. |
| **`PROD-GATE-06`** | **macOS Binary Trust** | Apple Developer ID signed, notarized, stapled; clean Gatekeeper pass without quarantine overrides. |
| **`PROD-GATE-07`** | **Artifact Security & SBOM** | CycloneDX SBOM generated; zero critical/high unmitigated CVEs; malware scan clean. |
| **`PROD-GATE-08`** | **Localhost Runtime Boundary**| Sockets bind exclusively to `127.0.0.1`; local session auth token enforced; zero case egress. |
| **`PROD-GATE-09`** | **First-Run Onboarding** | Welcome screen displays privacy facts; Sample A runs to completion in < 60 seconds; evaluation mode is explicit. |
| **`PROD-GATE-10`** | **Real Case Lifecycle** | Ingest $\rightarrow$ reconcile $\rightarrow$ exception inspect $\rightarrow$ Form 8949 worksheet output complete. |
| **`PROD-GATE-11`** | **Independent Verification** | Evidence bundle transferred to separate machine and verified successfully via frozen offline verifier (`apps/verifier/verify.py`). |
| **`PROD-GATE-12`** | **Restart & Durability** | SQLite WAL mode with `synchronous = FULL`; closing/reopening recovers 100% of cases, firm identity, license, and audit log. |
| **`PROD-GATE-13`** | **Durability & Recovery** | Online backup creates valid snapshot; restore recovers exact state with zero corruption; first-run rollback recovers cleanly. |
| **`PROD-GATE-14`** | **In-Place Upgrade Safety**| Upgrading to newer version discovers existing DB, applies migrations, and leaves past receipts verifiable. |
| **`PROD-GATE-15`** | **Enterprise IT Package** | IT Deployment & Security Profile document reviewed and accepted for Intune/Defender allowlisting. |
| **`PROD-GATE-16`** | **Sanitized Diagnostics** | Exported `diagnostic.zip` verified to contain manifest and zero client PII or unmasked PTIN/EFIN. |
| **`PROD-GATE-17`** | **Legal & Privacy Boundaries**| EULA, Privacy Statement, and Tax/Legal Disclaimers finalized and published. |
| **`PROD-GATE-18`** | **First-Time UAT Sign-Off** | 5–8 unguided CPA test sessions confirm trust confidence, zero-intervention completion, and commercial intent. |

---

## 8. Non-Happy Path & Failure Journeys

Production qualification explicitly exercises 14 mandatory failure modes to guarantee clear, actionable user recovery:

1. **Transactional Email Delayed/Lost:** Instant resend and web-fallback flow.
2. **Expired Download Link:** Friendly re-authentication / link-renewal prompt without repurchasing.
3. **Wrong Platform Downloaded:** Automatic detection and 1-click alternative platform download link.
4. **Interrupted Download:** Resumable downloads or clear error message prompting re-download.
5. **Signature Check Failure:** OS warnings or altered binary triggers explicit integrity alert.
6. **Malformed License Token:** Clear UI alert distinguishing syntax error from signature tampering.
7. **Expired License:** Transparent warning displaying expiration date and renewal CTA without locking historical cases.
8. **Case Capacity Limit Reached:** Clear upgrade CTA without data loss or case corruption.
9. **Production Ingestion Without License:** Clear prompt redirecting to evaluation samples or license purchase.
10. **Mid-Flight Crash / Power Loss:** SQLite WAL `synchronous = FULL` guarantees zero corrupt database files on restart.
11. **First-Run Initialization Rollback:** Interrupted initial storage creation rolls back cleanly and re-initializes on restart.
12. **Legacy Database Upgrade:** Smooth migration from previous schema versions with audit trail preservation.
13. **Backup Restore Attempt:** Transactional restore with automatic pre-restore backup of the target database.
14. **Corporate Endpoint Block:** Clear IT Deployment Profile instructions provided for corporate allowlisting.

---

## 9. Customer Invariants & Final Closure Standard

### Customer Invariant
> **No production release may require a first-time user to consult GitHub, Terminal, PowerShell, Docker, Python, developer documentation, or the founder in order to complete the supported commercial journey.**

### About & Version Visibility
The application UI visibly exposes under **About / System Information**:
- VaultBasis version
- Release channel (`STABLE`, `CANDIDATE`, `LTS`)
- Exact Git commit SHA
- Target platform (`win-x64`, `mac-arm64`, `mac-x64`)
- SQLite database schema version
- Commercial license state & remaining case capacity

### Formal MMP15-PROD-001 Closure Acceptance Standard
> **MMP15-PROD-001 closes only when an unfamiliar practitioner, using a clean supported machine and only public/customer-facing materials, can independently establish product relevance and security trust; obtain an authentic qualified VaultBasis artifact; run bundled evaluation cases; purchase/request and activate a license; ingest realistic production evidence; reconcile a case; export and independently verify signed evidence; restart without losing work; obtain support diagnostics; and understand renewal/support paths without developer intervention.**
> 
> **For managed machines: An enterprise IT reviewer can independently determine application publisher identity, privileges, network behavior, data locations, dependencies, security posture and deployment requirements from the provided IT package.**

---

## 10. Governing Launch & GTM Programs

This production journey is executed in strict alignment with two dedicated, parallel launch specifications:
1. [`docs/launch/MMP15_LAUNCH_OPS_001_SUBPROCESSOR_READINESS.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/launch/MMP15_LAUNCH_OPS_001_SUBPROCESSOR_READINESS.md) — *Vendor, Subprocessor & External Dependency Readiness Matrix* (Paddle, Vercel, Email, DNS, Apple, Azure, Support, Privacy DPA Ledger).
2. [`docs/launch/MMP15_GTM_LAUNCH_001_COMMERCIAL_MARKET_ENTRY.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/launch/MMP15_GTM_LAUNCH_001_COMMERCIAL_MARKET_ENTRY.md) — *VaultBasis Commercial Launch & Market Entry Program* (Positioning freeze, ICP taxonomy, Multi-tier channel distribution, Content Asset Bank, AI-Search SEO, 10-to-1 repurposing engine, 5-phase rollout, and full-funnel conversion metrics).
