# MMP15-LAUNCH-OPS-001: Vendor, Subprocessor & External Dependency Readiness
**Program ID:** MMP15-LAUNCH-OPS-001  
**Document Version:** 1.1.0-PROD  
**Governing Standards:** Left-Shift Granite Industrial Standard, PRD §64/§71, Evidence Contract v0.1  
**Classification:** Operational Launch Governance & Vendor Risk Ledger  
**Effective Date:** 2026-10-09  

---

## 1. Executive Charter & Data Boundary Policy

This specification establishes the authoritative inventory, relationship classification, qualification criteria, and security governance for all third-party service providers, cloud subprocessors, and external operational dependencies participating in the VaultBasis commercial launch.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    WEB & COMMERCIAL CONTROL PLANE                                      │
│  (Customer Identity, Merchant of Record Billing, Website Hosting, License Key Delivery, Support)      │
│  External Providers / Dependencies: Paddle, Vercel, Transactional Mailer, GitHub, DNS, Apple, Azure   │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │ Offline License Token Delivery / Download Auth
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      LOCAL EDGE EVIDENCE PLANE                                         │
│  (Form 1099-DA Ingest, Ledger Reconciliation, Difference Isolation, Professional Review, Sign/Export)  │
│  Execution Environment: Local Practitioner Workstation (macOS arm64 / Windows x64)                     │
│  Offline Capability: Qualified offline Edge workflow completed without requiring external network access│
│  Remote Data Processors for Client Tax Records / Ledger Data: NONE                                     │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

> ### 🛡️ Authoritative Local Processing & Privacy Invariant
> **VaultBasis Edge processes client reconciliation and evidence locally on your computer. Client tax records and ledger data are not uploaded to VaultBasis cloud services for normal Edge case processing.**
> 
> **Normal Edge case processing does not require a remote data processor for client tax records or ledger data.**
> 
> **VaultBasis must not automatically transmit client tax records, broker/ledger source data, taxpayer identifiers (SSN/TIN, PTIN, EFIN), wallet/transaction histories, reconciliation findings, or Evidence Receipts to payment, marketing, analytics, support, or other cloud services during normal Edge processing. Support workflows must instruct users not to submit client tax data unless an explicitly approved secure support process exists.**
> 
> **Zero telemetry or tracking pixels shall be introduced into the Edge application runtime.**

---

## 2. Master Subprocessor & External Vendor Matrix

Every external entity is formally categorized by its exact legal and operational relationship to prevent confusing general infrastructure dependencies with customer data subprocessors.

### Relationship Classification Vocabulary
- `SUBPROCESSOR`: Third party processing customer/account personal data on behalf of VaultBasis under a Data Processing Addendum (DPA).
- `INDEPENDENT_CONTROLLER`: Third party processing data under its own legal authority and terms (e.g. Merchant of Record).
- `INFRASTRUCTURE_DEPENDENCY`: Core internet / platform infrastructure where customer data is absent or strictly out of scope.
- `SIGNING_TRUST_PROVIDER`: Platform security and code signing authorities validating executable integrity.
- `SERVICE_PROVIDER`: Business operations and transactional communication providers.
- `MARKETING_PLATFORM`: Ad and campaign measurement platforms (strictly isolated to public web; zero Edge presence).
- `NOT_IN_SCOPE_FOR_CUSTOMER_DATA_PROCESSING`: Engineering tools and repositories containing zero customer or client tax data.

### Provider Closure Lifecycle States
`NOT_SELECTED` | `SELECTED` | `ACCOUNT_CREATED` | `IDENTITY_VALIDATION_PENDING` | `CONTRACT/DPA_PENDING` | `TECHNICAL_INTEGRATION_PENDING` | `PRODUCTION_VALIDATION_PENDING` | `READY` | `BLOCKED` | `NOT_REQUIRED`

---

| Provider & Category | Business Purpose | Relationship Classification | Data Sent | Client Tax Data Sent? (1099-DA / Ledger) | Specific Personal Data Categories | Sensitive Identifiers (SSN, PTIN, EFIN, Wallets) | Region / Location | DPA / Terms Status | Retention Schedule | Security / MFA | Webhook / API Dependency | Privacy Policy Disclosure | Failure / Exit Plan | Closure State | Concrete Evidence / Artifact |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Paddle**<br>*(Merchant of Record / Payment)* | Checkout UI, payment processing, sales tax/VAT remittance, order events, refund processing | `INDEPENDENT_CONTROLLER` | Order ID, Buyer Name, Work Email, Billing Address, Payment Metadata, Plan Tier | **NO** (Strictly Zero) | Name, Email, Billing Address, Payment Instrument Metadata | **NONE** (Zero SSN, PTIN, EFIN, or Wallets) | UK / USA / EU | MoR Commercial Terms & DPA Active | Duration of tax statutory period (7 yrs) | Enforced Hardware MFA / SAML | Raw-body HMAC-SHA256 signature verification, 300s freshness, durable dedupe | Disclosed in Privacy Policy §4 (Billing) | Switch to Stripe Billing / MoR alternative; export invoices | `PRODUCTION_VALIDATION_PENDING` | `api/webhook-payment.js`, `api/_lib/paddle-client.js`, [PROD-GATE-02] |
| **Vercel**<br>*(Public Web & API Hosting)* | Public website hosting (`vaultbasis.com`), serverless checkout/download entitlement endpoints, edge caching | `SUBPROCESSOR` | HTTP request metadata (IP, user-agent, path, timestamp), hashed download tokens (SHA-256) | **NO** (Strictly Zero) | IP Address, User-Agent, Session Access Token | **NONE** (Zero SSN, PTIN, EFIN, or Wallets) | USA (Global Edge CDN) | Vercel Enterprise DPA executed | 30 days rolling logs; Blob tokens TTL 72h | Org MFA enforced; scoped deployment tokens | Serverless Node.js runtime, Vercel Blob private storage | Disclosed in Privacy Policy §3 (Hosting) | Direct DNS cutover to Cloudflare Pages / AWS S3 + CloudFront | `READY` | `vercel.json`, `api/download.js`, `api/commercial.js` |
| **Transactional Email Provider**<br>*(Postmark / Resend)* | Delivery of offline license tokens, download links, payment receipts, and commercial notices | `SUBPROCESSOR` | Recipient Email, Recipient Name, License ID, Signed License Token File, Download URL | **NO** (Strictly Zero) | Work Email, Customer Name | **NONE** (Zero SSN, PTIN, EFIN, or Wallets) | USA / EU | Standard DPA with Standard Contractual Clauses (SCCs) | 30-day message body retention; metadata 90 days | Enforced 2FA; API key IP whitelisting | Direct API call from webhook handler upon verified payment event | Disclosed in Privacy Policy §5 (Communications) | Multi-provider fallback (Postmark -> Resend -> Amazon SES) | `PRODUCTION_VALIDATION_PENDING` | `api/_lib/delivery-mailer.js`, SPF/DKIM/DMARC records |
| **Apple**<br>*(macOS Platform & Notarization)* | Developer ID Application code signing, Hardened Runtime validation, malware scan, notarization stapling | `SIGNING_TRUST_PROVIDER` | Compiled desktop `.app` and `.dmg` binaries | **NO** (Zero customer data) | Apple Developer Account credentials of organization | **NONE** | USA (Cupertino, CA) | Apple Developer Program Agreement | Indefinite notarization ticket registry on Apple servers | Hardware Security Key / Apple ID 2FA | `altool` / `notarytool` automated API submission | Disclosed in Trust Architecture | Offline application execution survives via stapled ticket | `READY` | Developer ID Certificate, Hardened Runtime entitlements |
| **Microsoft / Azure Artifact Signing**<br>*(Windows Signing)* | Authenticode code signing and RFC 3161 trusted timestamping for Windows installer | `SIGNING_TRUST_PROVIDER` | Compiled Windows `.exe` installer hashes | **NO** (Zero customer data) | Microsoft Trusted Signing organizational credentials | **NONE** | USA (Redmond, WA) | Microsoft Artifact Signing Service Agreement | Timestamp token registry | Azure AD MFA / Certificate HSM | Azure Trusted Signing CLI / SignTool integration | Disclosed in Trust Architecture | Standalone EV Code Signing Hardware Token fallback | `IDENTITY_VALIDATION_PENDING` | Azure Trusted Signing configuration |
| **GitHub**<br>*(Source & CI/CD)* | Source code version control, automated regression matrix, pre-commit pipelines, release governance | `NOT_IN_SCOPE_FOR_CUSTOMER_DATA_PROCESSING` | Source code, test fixtures, synthetic datasets, CI logs | **NO** (Zero customer data) | Developer GitHub usernames, commit signatures | **NONE** | USA | GitHub Enterprise Terms & DPA | Full git revision history | Mandatory 2FA for all maintainers; GPG commit signing | GitHub Actions workflow runners | N/A (Internal engineering infrastructure) | Local git mirror + offline backup repos | `READY` | GitHub branch protections on `main` / `preprod` |
| **DNS / Domain Registrar**<br>*(Cloudflare / Route53)* | Authoritative DNS resolution, apex domain routing, SPF/DKIM/DMARC enforcement, CAA records | `INFRASTRUCTURE_DEPENDENCY` | DNS query logs (IP, queried record) | **NO** (Strictly Zero) | IP Address | **NONE** | Global Anycast | Registrar Master Service Agreement | Standard DNS query cache | Hardware Security Key MFA; Registrar Lock enabled | Authoritative DNS API | Disclosed in Security Center | Secondary DNS provider standby (AWS Route 53) | `READY` | Live DNS records, DMARC policy `p=reject` |
| **Customer Support / Helpdesk**<br>*(Plain.com / Crisp / Email)* | Tier-1/2 customer support, technical inquiries, licensing assistance | `SUBPROCESSOR` | Customer Email, Customer Name, Support Ticket Body, Attachments (Sanitized) | **NO** (Automatic intake disallows PII/tax CSVs) | Name, Email, Support Communications | **NONE** (Warning prompts user not to attach client PII/SSN) | USA / EU | Vendor DPA executed | 90 days post-resolution, then automated redaction | 2FA enforced; Role-based access control | Webhook / Email forwarding integration | Disclosed in Privacy Policy §6 (Support) | Fallback to direct encrypted email via PGP / ProtonMail | `TECHNICAL_INTEGRATION_PENDING` | Privacy disclosure on support portal |
| **Marketing Web Analytics**<br>*(Plausible — Public Web Only)* | Privacy-focused public website visit analytics (strictly cookie-free, non-tracking) | `SUBPROCESSOR` | Aggregate page views, referral source, country, device OS/browser | **NO** (Strictly Zero; web only) | Pseudonymized IP hash (daily rotated salt), User-Agent | **NONE** | EU (Germany / Estonia) | Plausible GDPR-compliant DPA | 12 months aggregate metrics; zero raw IP storage | 2FA enforced | Client-side async JS script tag on marketing pages | Disclosed in Privacy Policy §7 (Analytics); cookie-free notice | Script removal without any loss of website functionality | `READY` | `apps/web-marketing/partials/header.html` |
| **Error / Crash Monitoring**<br>*(Sentry — Public Web Only)* | Frontend JavaScript exception logging on public marketing and billing pages | `SUBPROCESSOR` | Unhandled browser JavaScript error stack traces, URL, browser version | **NO** (Strictly Zero; **EXCLUDED from Edge runtime**) | Scrubbed IP, Browser User-Agent | **NONE** | USA / EU | Sentry DPA with PII data scrubbing rules | 30 days retention, automated deletion | 2FA enforced | Async browser SDK on `vaultbasis.com` | Disclosed in Privacy Policy §8 (Error Reporting) | Disable DSN; zero impact on core product or Edge runtime | `READY` | Sentry client config with strict PII scrubber |
| **CRM / Marketing Communications**<br>*(Loops / Customer.io)* | Lead capture, educational newsletters, product release announcements for opted-in CPAs | `SUBPROCESSOR` | Name, Work Email, Firm Name, Opt-in Timestamp, Unsubscribe Token | **NO** (Strictly Zero) | Name, Work Email, Firm Affiliation | **NONE** | USA | Vendor DPA with CAN-SPAM / GDPR opt-in enforcement | Retained until explicit unsubscribe / erasure request | 2FA enforced; Scoped API tokens | REST API / Webhook integration | Disclosed in Privacy Policy §5; 1-click unsubscribe header | Export CSV and purge vendor account; zero lock-in | `TECHNICAL_INTEGRATION_PENDING` | Opt-in checkboxes on request-access forms |
| **Demo Scheduling & Webinars**<br>*(Cal.com / Zoom)* | Scheduling 1-on-1 CPA product walk-throughs and monthly group reconciliation webinars | `SUBPROCESSOR` | Practitioner Name, Work Email, Firm Name, Scheduled Time Slot | **NO** (Strictly Zero) | Name, Work Email, Phone (optional) | **NONE** | USA / EU | Vendor DPA | 90 days post-meeting retention | 2FA enforced | Cal.com API / Webhook | Disclosed in Privacy Policy §6 | Direct calendar invite (`.ics`) via email | `READY` | `apps/web-marketing/contact.html` |
| **Social & Ad Platforms**<br>*(LinkedIn / X / Google Ads)* | Educational campaign distribution, audience measurement, conversion attribution | `MARKETING_PLATFORM` | Aggregate campaign performance, anonymized click IDs | **NO** (Strictly Zero; **ZERO ad pixels inside Edge runtime**) | Browser Cookie IDs (Marketing site only; zero tracking in Edge app) | **NONE** | USA | Platform Advertiser Terms & Privacy Regulations | Platform-managed retention (typically 90–180 days) | 2FA enforced on Business Manager accounts | Platform conversion APIs (Server-side hashed leads) | Disclosed in Cookie Banner / Privacy Policy | Immediate pause of ad campaigns; zero product dependency | `READY` | Cookie consent banner on marketing site |

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
3. **Opt-Out & Audit Invariant:** Because the Edge desktop runtime operates locally and offline, enterprise customers may utilize VaultBasis in air-gapped environments without interacting with any cloud subprocessor except during initial download and license key acquisition.
