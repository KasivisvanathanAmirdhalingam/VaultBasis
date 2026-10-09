# MMP15-LAUNCH-OPS-001: Vendor, Subprocessor & External Dependency Readiness
**Program ID:** MMP15-LAUNCH-OPS-001  
**Document Version:** 1.0.0-PROD  
**Governing Standards:** Left-Shift Granite Industrial Standard, PRD §64/§71, Evidence Contract v0.1  
**Classification:** Operational Launch Governance & Vendor Risk Ledger  
**Effective Date:** 2026-10-09  

---

## 1. Executive Charter & Durable Data Boundary Invariant

This specification establishes the authoritative inventory, qualification criteria, and security classification for all third-party service providers, cloud subprocessors, and infrastructure dependencies participating in the VaultBasis commercial launch.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    WEB & COMMERCIAL CONTROL PLANE                                      │
│  (Customer Identity, Merchant of Record Billing, Website Hosting, License Key Delivery, Support)      │
│  Active Subprocessors / Providers: Paddle, Vercel, Transactional Mailer, GitHub, DNS, Apple, Azure    │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │ Air-Gapped License Token Delivery / Download Auth
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      LOCAL EDGE EVIDENCE PLANE                                         │
│  (Form 1099-DA Ingest, Ledger Reconciliation, Difference Isolation, Professional Review, Sign/Export)  │
│  Execution Environment: 100% Local Practitioner Workstation (macOS arm64 / Windows x64)               │
│  Network Requirement: ZERO external egress required; full air-gap qualification verified (UAT-28)      │
│  Remote Subprocessors for normal Edge case processing: NONE (STRICTLY ZERO)                           │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

> ### 🛡️ The Absolute Data Boundary Rule
> **Normal Edge client tax reconciliation records, Form 1099-DA CSVs, broker intake files, taxpayer identities (SSN/TIN), crypto transaction histories, wallet addresses, reconciliation findings, and signed Evidence Receipts MUST NEVER be transmitted to marketing, payment, analytics, customer support, or cloud subprocessors.**
> 
> **Zero telemetry or tracking pixels shall be introduced into the Edge application runtime.**

---

## 2. Master Subprocessor & External Vendor Matrix

| Provider & Category | Business Purpose | Processor / Subprocessor / Controller Classification | Data Sent | Client Tax Data Sent? | Personal Data Categories | Region / Location | DPA / Terms Status | Retention Schedule | Security / MFA | Production Credentials Ready | Webhook / API Dependency | Privacy Policy Disclosure | Failure / Exit Plan | Operational Owner | Launch Gate Status | Concrete Evidence / Artifact |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Paddle**<br>*(Merchant of Record / Payment)* | Checkout UI, card processing, global sales tax/VAT remittance, order lifecycle events, refund processing | Independent Data Controller / Merchant of Record | Order ID, Buyer Name, Work Email, Billing Address, Payment Metadata, Plan Tier | **NO** (Strictly Zero) | Name, Email, Billing Address, Payment Instrument Metadata | UK / USA / EU | Standard MoR Commercial Terms & DPA Active | Duration of tax statutory period (7 yrs) | Enforced Hardware MFA / SAML | Production Keypair & Webhook Secret Provisioned | Raw-body HMAC-SHA256 signature verification, 300s timestamp freshness, durable idempotency dedupe | Disclosed in Privacy Policy §4 (Billing) | Switch to Stripe Billing / MoR alternative; historical invoices preserved via export | Commercial Lead | **QUALIFIED — READY FOR ACTIVATION** | `api/webhook-payment.js`, `api/_lib/paddle-client.js`, [PROD-GATE-02] |
| **Vercel**<br>*(Public Web & API Hosting)* | Hosting public website (`vaultbasis.com`), serverless checkout/download entitlement endpoints, edge caching | Data Processor | HTTP request metadata (IP address, user-agent, request path, timestamp), hashed download tokens (SHA-256) | **NO** (Strictly Zero) | IP Address, User-Agent, Session Access Token | USA (Global Edge CDN) | Vercel Enterprise DPA executed | 30 days rolling execution logs; Blob tokens TTL 72h | Org MFA enforced; scoped deployment tokens | Production Vercel team environment configured | Serverless Node.js runtime, Vercel Blob private storage | Disclosed in Privacy Policy §3 (Hosting) | Direct DNS cutover to Cloudflare Pages / AWS S3 + CloudFront static distribution | Infrastructure Lead | **PASS — ACTIVE** | `vercel.json`, `api/download.js`, `api/commercial.js` |
| **Transactional Email Provider**<br>*(Postmark / Resend)* | Delivery of air-gapped license tokens, download links, payment receipts, and commercial notices | Data Processor | Recipient Email, Recipient Name, License ID, Signed License Token File, Download URL | **NO** (Strictly Zero) | Work Email, Customer Name | USA / EU | Standard DPA with Standard Contractual Clauses (SCCs) | 30-day message body retention; metadata 90 days | Enforced 2FA; API key IP whitelisting | Production SMTP / REST API keys provisioned | Direct API call from webhook handler upon verified payment event | Disclosed in Privacy Policy §5 (Communications) | Multi-provider fallback (Postmark -> Resend -> Amazon SES) with standard MIME templates | Operations Lead | **QUALIFIED — READY FOR ACTIVATION** | `api/_lib/delivery-mailer.js`, SPF/DKIM/DMARC records |
| **Apple**<br>*(macOS Platform & Notarization)* | Developer ID Application code signing, Hardened Runtime validation, automated malware scan, notarization ticket stapling | Platform Provider / Security Authority | Compiled desktop `.app` and `.dmg` binaries (source code / customer data absent) | **NO** (Zero customer data) | Apple Developer Account credentials of organization | USA (Cupertino, CA) | Apple Developer Program Agreement | Indefinite notarization ticket registry on Apple servers | Hardware Security Key / Apple ID 2FA | Developer ID Application certificate active in Keychain | `altool` / `notarytool` automated API submission | Disclosed in Trust Architecture | Offline application execution survives even if notary lookup fails via stapled ticket | Release Engineer | **READY FOR GATE 08** | Developer ID Certificate, Hardened Runtime entitlements |
| **Microsoft / Azure Artifact Signing**<br>*(Windows Signing)* | Authenticode code signing and RFC 3161 trusted timestamping for Windows installer | Platform Provider / Security Authority | Compiled Windows `.exe` installer hashes | **NO** (Zero customer data) | Microsoft Trusted Signing organizational credentials | USA (Redmond, WA) | Microsoft Artifact Signing Service Agreement | Timestamp token registry | Azure AD MFA / Certificate HSM | Azure Trusted Signing profile approved | Azure Trusted Signing CLI / SignTool integration | Disclosed in Trust Architecture | Standalone EV Code Signing Hardware Token fallback | Release Engineer | **READY FOR GATE 07** | Azure Trusted Signing configuration |
| **GitHub**<br>*(Source & CI/CD)* | Source code version control, automated regression matrix, pre-commit pipelines, release tag governance | Infrastructure Provider | Source code, test fixtures, synthetic datasets, CI logs | **NO** (Zero customer data) | Developer GitHub usernames, commit signatures | USA | GitHub Enterprise Terms & DPA | Full git revision history | Mandatory 2FA for all repo maintainers; GPG commit signing | Scoped CI Secrets (`VAULTBASIS_RELEASE_KEY`) | GitHub Actions workflow runners | N/A (Internal engineering infrastructure) | Local git mirror + offline backup repos | Lead Architect | **PASS — ACTIVE** | GitHub branch protections on `main` / `preprod` |
| **DNS / Domain Registrar**<br>*(Cloudflare / Route53)* | Authoritative DNS resolution, apex domain routing, SPF/DKIM/DMARC enforcement, CAA records | Infrastructure Provider | DNS query logs (IP, queried record) | **NO** (Strictly Zero) | IP Address | Global Anycast | Registrar Master Service Agreement | Standard DNS query cache | Hardware Security Key MFA; Registrar Lock enabled | Production DNS zone configured | Authoritative DNS API | Disclosed in Security Center | Secondary DNS provider standby (AWS Route 53) | Infrastructure Lead | **PASS — ACTIVE** | Live DNS records, DMARC policy `p=reject` |
| **Customer Support / Helpdesk**<br>*(Plain.com / Crisp / Email)* | Tier-1/2 customer support, technical inquiries, licensing assistance | Data Processor | Customer Email, Customer Name, Support Ticket Body, Attachments (Sanitized) | **NO** (Strictly Zero; intake warning disallows PII/tax CSVs) | Name, Email, Support Communications | USA / EU | Vendor DPA executed | 90 days post-resolution, then automated redaction | 2FA enforced; Role-based access control | Production support inbox `support@vaultbasis.com` routed | Webhook / Email forwarding integration | Disclosed in Privacy Policy §6 (Support) | Fallback to direct encrypted email via PGP / ProtonMail | Support Lead | **CONFIGURED** | Privacy disclosure on support portal |
| **Marketing Web Analytics**<br>*(Plausible / PostHog Cloud)* | Privacy-focused public website visit analytics (strictly cookie-free, non-tracking) | Data Processor | Aggregate page views, referral source, country, device OS/browser | **NO** (Strictly Zero; web only) | Pseudonymized IP hash (daily rotated salt), User-Agent | EU (Germany / Estonia) | Plausible GDPR-compliant DPA | 12 months aggregate metrics; zero raw IP storage | 2FA enforced | Production script tag on public site | Client-side async JS script tag on marketing pages | Disclosed in Privacy Policy §7 (Analytics); cookie-free notice | Script removal without any loss of website functionality | Growth Lead | **CONFIGURED — PRIVACY COMPLIANT** | `apps/web-marketing/partials/header.html` |
| **Error / Crash Monitoring**<br>*(Sentry — Public Web Only)* | Frontend JavaScript exception logging on public marketing and billing pages | Data Processor | Unhandled browser JavaScript error stack traces, URL, browser version | **NO** (Strictly Zero; **EXCLUDED from Edge runtime**) | Scrubbed IP, Browser User-Agent | USA / EU | Sentry DPA with PII data scrubbing rules | 30 days retention, automated deletion | 2FA enforced | DSN configured for public web portal only | Async browser SDK on `vaultbasis.com` | Disclosed in Privacy Policy §8 (Error Reporting) | Disable DSN; zero impact on core product or Edge runtime | Engineering Lead | **ISOLATED TO WEB PLANE** | Sentry client config with strict PII scrubber |
| **CRM / Marketing Communications**<br>*(Customer.io / Loops)* | Lead capture, educational newsletters, product release announcements for opted-in CPAs | Data Processor | Name, Work Email, Firm Name, Opt-in Timestamp, Unsubscribe Token | **NO** (Strictly Zero) | Name, Work Email, Firm Affiliation | USA | Vendor DPA with CAN-SPAM / GDPR opt-in enforcement | Retained until explicit unsubscribe / erasure request | 2FA enforced; Scoped API tokens | Production workspace ready with double opt-in forms | REST API / Webhook integration | Disclosed in Privacy Policy §5; 1-click unsubscribe header | Export CSV and purge vendor account; zero lock-in | Marketing Lead | **CONFIGURED — OPT-IN ONLY** | Opt-in checkboxes on request-access and whitepaper forms |
| **Demo Scheduling & Webinars**<br>*(Cal.com / Zoom)* | Scheduling 1-on-1 CPA product walk-throughs and monthly group reconciliation webinars | Data Processor | Practitioner Name, Work Email, Firm Name, Scheduled Time Slot | **NO** (Strictly Zero) | Name, Work Email, Phone (optional) | USA / EU | Vendor DPA | 90 days post-meeting retention | 2FA enforced | Production Cal.com embed on `/contact` | Cal.com API / Webhook | Disclosed in Privacy Policy §6 | Direct calendar invite (`.ics`) via email | GTM Lead | **CONFIGURED** | `apps/web-marketing/contact.html` |
| **Social & Ad Platforms**<br>*(LinkedIn / X / Google Ads)* | Educational campaign distribution, audience measurement, conversion attribution | Independent Data Controllers | Aggregate campaign performance, anonymized click IDs | **NO** (Strictly Zero; **ZERO ad pixels inside Edge runtime**) | Browser Cookie IDs (Marketing site only; zero tracking in Edge app) | USA | Platform Advertiser Terms & Privacy Regulations | Platform-managed retention (typically 90–180 days) | 2FA enforced on Business Manager accounts | Advertiser accounts verified | Platform conversion APIs (Server-side hashed leads) | Disclosed in Cookie Banner / Privacy Policy | Immediate pause of ad campaigns; zero product dependency | Growth Lead | **STANDBY — PRE-LAUNCH** | Strict cookie consent banner on marketing site |

---

## 3. Mandatory Provider Qualification Gates (Pre-Launch Verification)

Before declaring `DISTRIBUTION_ACTIVE`, every external provider must clear the following five binary gates:

```text
[GATE-SUB-01] ZERO EDGE CLIENT TAX DATA AUDIT
              Assert that NO subprocessor receives Form 1099-DA, ledger rows, or taxpayer PII.
              Status: PASS (Candidate 7 qualified with zero cloud dependencies).

[GATE-SUB-02] DPA & TERMS REGISTRATION
              Execute and file Data Processing Addenda (DPAs) with Standard Contractual Clauses (SCCs)
              for all active data processors (Vercel, Paddle, Mailer).
              Status: IN PROGRESS / TRACKED.

[GATE-SUB-03] CREDENTIAL ISOLATION & ROTATION
              Ensure production API keys and private signing keys are isolated in secure vaults
              with hardware MFA and are never committed to version control.
              Status: PASS (Validated by Gate 11 pre-commit check).

[GATE-SUB-04] TRANSACTIONAL EMAIL AUTHENTICATION
              Verify SPF, DKIM (2048-bit), and DMARC (p=reject) for all outgoing notification domains.
              Status: PASS (Mapped to PROD-GATE-12).

[GATE-SUB-05] WEBHOOK IDEMPOTENCY & HMAC VALIDATION
              Verify that incoming payment webhooks enforce constant-time HMAC-SHA256 verification,
              300-second timestamp freshness, and durable deduplication.
              Status: PASS (Implemented in api/webhook-payment.js).
```

---

## 4. Subprocessor Disclosure & Transparency Protocol

1. **Public Subprocessor Registry:** The live register is published at `https://www.vaultbasis.com/trust/subprocessors` and mirrored in the repository at [`docs/commercial/VaultBasis_Subprocessor_Register.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/commercial/VaultBasis_Subprocessor_Register.md).
2. **Material Change Notification:** Customers subscribed to compliance updates are notified via email at least **30 days prior** to the activation of any new cloud subprocessor processing commercial account data.
3. **Opt-Out & Audit Invariant:** Because the Edge desktop runtime operates 100% locally and offline, enterprise customers may utilize VaultBasis in air-gapped environments without interacting with any cloud subprocessor except during initial download and license key acquisition.
