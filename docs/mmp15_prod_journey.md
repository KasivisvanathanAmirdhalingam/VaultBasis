# VaultBasis MMP-1.5 Production Practitioner Journey & Enterprise Trust Architecture (MMP15-PROD-001)

> **Milestone:** MMP15-PROD-001 — First-Time Practitioner Commercial Journey & Enterprise Trust Qualification  
> **Status:** ACTIVE GOVERNANCE MILESTONE  
> **Pre-requisites:** `milestone/mmp15-commercial-control-plane-ready-001` (Merged at SHA `63ba5528...`, 364 tests PASS, 11/11 Gates PASS)  
> **Strategic Gate:** MMP-2 Local Intelligence implementation is strictly **ON HOLD** awaiting qualification of this production commercial journey.

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
│  (RFC 3161)     │ │• Zero egress    │                         │• CycloneDX SBOM │ │• Clear pricing  │
│• Apple Developer│ │• No admin rights│                         │• Allowlist spec │ │• Auth'd emails  │
│  ID Notarization│ │• Zero telemetry │                         │• Intune/MDM doc │ │• Signed dl URLs │
│• SHA-256 Digest │ │• Never asks for │                         │• Silent install │ │• EULA & Privacy │
│• CI Malware Scan│ │  crypto keys/pwd│                         │  specification  │ │  commitments    │
└─────────────────┘ └─────────────────┘                         └─────────────────┘ └─────────────────┘
```

---

## 2. Dual Customer Persona Journeys

To accommodate both independent practitioners and accountants working inside governed firms, VaultBasis supports two distinct production paths:

### Path A: Self-Managed Practitioner (Solo CPA / Independent EA)
```
[ www.vaultbasis.com ] ──► [ Value & Pricing ] ──► [ Request / Buy License ] ──► [ Transactional Email ]
                                                                                         │
[ Open Application ] ◄── [ Extract & Launch ] ◄── [ OS Validates Signature ] ◄── [ Signed Download ]
        │
[ Onboarding & Sample A ] ──► [ Real Case Intake ] ──► [ Reconcile ] ──► [ Export & Verify Receipt ]
```

### Path B: Firm-Managed Practitioner (Enterprise / Multi-Seat CPA Firm)
```
[ www.vaultbasis.com ] ──► [ "Managed Work Laptop?" ] ──► [ Enterprise IT Deployment Pack ]
                                                                   │
[ Practitioner Receives Installed App ] ◄── [ IT Allowlisting & Intune/MDM Push ] ◄──────┘
        │
[ Firm License Activation ] ──► [ Workspace Identity Setup ] ──► [ Multi-Lot Reconciliation ]
```

---

## 3. The 27-Stage Practitioner Commercial Golden Path

| Stage | Practitioner Question / Action | Production Requirement & Expected Behavior |
|---|---|---|
| **1. Discovery** | *"What is VaultBasis?"* | Homepage articulates local, deterministic digital-asset tax basis reconstruction in < 15 seconds. |
| **2. Relevance** | *"Is this for someone like me?"* | CPA / EA / Tax Preparer / Reviewer use cases prominently framed above the fold. |
| **3. Trust** | *"Why should I trust this on my PC?"* | Explicit "Why this is safe" badges: Local-only, Zero Egress, Signed & Notarized, Open Verifier. |
| **4. Scope** | *"What does it actually handle?"* | Supported inputs (Form 1099-DA, exchange CSVs, wallet exports) and boundaries clearly listed. |
| **5. Pricing** | *"What does it cost?"* | Transparent tier/case capacity matrix without opaque sales walls. |
| **6. Acquisition** | *"How do I obtain a license?"* | Simple, structured checkout / trial request flow requiring minimal practitioner data. |
| **7. Confirmation** | *"Did my request succeed?"* | Immediate on-screen confirmation with expected delivery timeframe (< 2 mins). |
| **8. Email Delivery** | *"Where is my license and link?"* | Authenticated transactional email delivered reliably (SPF, DKIM, DMARC compliant). |
| **9. Email Content** | *"What do I do with this email?"* | Clear email containing license token, platform-specific download button, SHA-256 hash, and instructions. |
| **10. Secure Download** | *"Is this download authentic?"* | Authenticated, temporary signed download link serving correct platform bundle (`.zip` / `.dmg`). |
| **11. Pre-Install Verification**| *"Can I verify before running?"* | Published release manifest (`manifest.json`) and SHA-256 checksums available for manual verification. |
| **12. OS Gatekeeper / SmartScreen**| *"Does the OS trust the binary?"* | Windows Authenticode verified publisher; macOS Gatekeeper accepts notarized ticket without `xattr` bypass. |
| **13. Zero-Engineering Install** | *"Do I need developer tools?"* | Extract and launch executable directly. Zero Python, zero pip, zero terminal commands, zero Docker. |
| **14. Privacy & Security Screen** | *"What will this app access?"* | First-run dialogue explicitly summarizing: "Local data only, No admin rights, No seed phrases requested". |
| **15. License Activation** | *"Where does the license go?"* | Drag-and-drop license file or paste token. Immediate validation with clear capacity display. |
| **16. Firm Identity Setup** | *"How is my firm identified?"* | Configure Firm Name, Preparer Name, and optional PTIN/EFIN (strictly encrypted & isolated locally). |
| **17. First Success (Sample A)** | *"Can I see it work immediately?"* | 1-click execution of Clean 1099-DA sample producing reconciled Form 8949 worksheet in < 60 seconds. |
| **18. Complex Ingest (Sample B)**| *"Can it handle multiple sources?"*| Multi-source exchange + wallet CSV ingest with automated deduplication and lot matching. |
| **19. Exception Handling (Sample C)**| *"What if data is missing?"* | Demonstrates missing basis detection, transfer matching gap findings, and actionable practitioner guidance. |
| **20. Real Client Ingest** | *"Can I use real client files?"* | Seamless intake of real client broker files with schema preflight validation. |
| **21. Deterministic Reconcile** | *"Is the calculation defensible?"* | Real-time reconciliation generating audit-trail findings and capital gain/loss summaries. |
| **22. Evidence Package Export** | *"How do I deliver this to a reviewer?"*| 1-click export of complete evidence bundle including signed outcome receipt (`receipt.json`). |
| **23. Independent Verification** | *"Can a reviewer verify without trust?"*| Open-source offline verifier verifies Ed25519 signature and SHA-256 evidence digests independently. |
| **24. Session Persistence** | *"Is my work saved on restart?"* | Re-opening application instantly recovers all cases, firm profile, license state, and audit log. |
| **25. Durability & Backup** | *"How do I protect my database?"* | 1-click database backup (`.db` snapshot) with transactional restore capability. |
| **26. Support & Diagnostics** | *"What if I encounter an issue?"* | 1-click export of sanitized support bundle (`diagnostic.zip` with manifest and zero client PII). |
| **27. License Renewal / Expiry**| *"What happens when my license ends?"*| Graceful degradation: existing cases and verifier remain 100% accessible; clear renewal path displayed. |

---

## 4. Master Task Ledger: MMP15-PROD Program Catalog

| Task ID | Task Title | Core Objective & Deliverable | Primary Persona | Status |
|---|---|---|---|---|
| **`MMP15-PROD-WEB-001`** | Production Website & Value Proposition | Clear, responsive website (`vaultbasis.com`) explaining local deterministic reconciliation in < 15s. | Prospective CPA / EA | `READY FOR SPEC` |
| **`MMP15-PROD-PRICE-001`**| Pricing, Tiers & Capacity Transparency | Transparent pricing matrix detailing case limits, practitioner workflow features, and renewals. | Managing Partner | `READY FOR SPEC` |
| **`MMP15-PROD-TRUST-001`**| Public Binary Trust & Code Signing | Windows RFC 3161 Authenticode signing & macOS Developer ID notarization and stapling. | Security Admin / CPA | `IN PROGRESS (Track A)` |
| **`MMP15-PROD-SEC-002`** | Artifact Security & Malware Scanning | CI pipeline integration for multi-engine malware scanning, dependency CVE checks, and CycloneDX SBOM. | Enterprise Security | `READY FOR SPEC` |
| **`MMP15-PROD-LOCAL-001`**| Local Runtime Boundary & Least Privilege | Strict 127.0.0.1 binding, ephemeral session auth tokens, zero admin rights, zero background daemons. | IT Administrator | `READY FOR SPEC` |
| **`MMP15-PROD-ENT-001`** | Enterprise IT Deployment Pack | Complete IT pack with Intune/MDM allowlisting guides, silent install flags, and network manifests. | Enterprise IT Lead | `READY FOR SPEC` |
| **`MMP15-PROD-TRUSTWEB-001`**| Trust Center (`vaultbasis.com/trust`) | Dedicated web portal covering security architecture, data locality, vulnerability disclosure, and FAQs. | Risk & Compliance | `READY FOR SPEC` |
| **`MMP15-PROD-COM-001`** | License Request & Acquisition Flow | Self-serve license request engine with automated key generation and CRM integration. | Customer Ops | `READY FOR SPEC` |
| **`MMP15-PROD-MAIL-001`**| Transactional Email & Deliverability | Production email template with SPF/DKIM/DMARC qualification, download links, and license tokens. | End-User CPA | `READY FOR SPEC` |
| **`MMP15-PROD-DL-001`**  | Secure Signed Artifact Delivery | Time-limited, authenticated download endpoints serving platform-specific distribution bundles. | Security Engineer | `READY FOR SPEC` |
| **`MMP15-PROD-WIN-001`** | First-Time Windows Direct Journey | Zero-terminal Windows packaging qualification with SmartScreen reputation management documentation. | Windows Practitioner | `READY FOR SPEC` |
| **`MMP15-PROD-MAC-001`** | First-Time macOS Direct Journey | Clean-download Gatekeeper acceptance on fresh Apple Silicon / Intel macOS without security bypasses. | macOS Practitioner | `IN PROGRESS (Track A)` |
| **`MMP15-PROD-ONB-001`** | First-Run Onboarding & Sample Suite | Interactive first-run guide with Samples A (1099-DA), B (Exchange), C (Basis Gap), and D (Tamper Proof). | First-Time User | `READY FOR SPEC` |
| **`MMP15-PROD-E2E-001`** | Real Practitioner Workflow Lifecycle | End-to-end multi-lot intake, reconciliation, exception review, and Form 8949 worksheet generation. | Senior Tax Preparer | `READY FOR SPEC` |
| **`MMP15-PROD-VERIFY-001`**| Independent Verifier Physical Journey| Physical machine receipt transfer and air-gapped cryptographic validation demonstration. | Audit Reviewer | `READY FOR SPEC` |
| **`MMP15-PROD-UPG-001`** | In-Place Upgrade & Migration Safety | Seamless version upgrades preserving existing databases, receipts, licenses, and firm identity. | IT Support / CPA | `READY FOR SPEC` |
| **`MMP15-PROD-REC-001`** | Backup, Restore & Recovery Journey | 1-click snapshot creation, atomic transactional restore, and corruption detection verification. | Practitioner | `READY FOR SPEC` |
| **`MMP15-PROD-SUP-001`** | Support & Sanitized Diagnostic Journey| 1-click sanitized diagnostic ZIP export with manifest, allowing fast triage without PII leakage. | Support Engineer | `READY FOR SPEC` |
| **`MMP15-PROD-UAT-001`** | Observed First-Time Practitioner UAT| Structured, unguided user testing with 5–8 CPAs measuring trust friction, time-to-value, and NPS. | Product Lead | `READY FOR SPEC` |

---

## 5. Security & Privacy Invariants for Production

1. **Zero Crypto Credential Requests:** VaultBasis will **NEVER** prompt for or store seed phrases, private keys, exchange passwords, or withdrawal-enabled API keys.
2. **Strict Data Locality:** All case calculations, source document parsing, and database records remain exclusively on the user's local machine (`127.0.0.1`).
3. **No Hidden Background Services:** VaultBasis does not register background daemons, kernel drivers, browser extensions, or automatic startup entries without explicit user action.
4. **Non-Elevated Execution:** Normal practitioner operations run entirely within standard user permissions (non-Administrator / non-root).
5. **Sanitized Diagnostics:** Support bundles exported by practitioners use strict positive-allowlisting and regex scrubbing, guaranteeing zero client transaction rows or unmasked PTIN/EFIN values.
