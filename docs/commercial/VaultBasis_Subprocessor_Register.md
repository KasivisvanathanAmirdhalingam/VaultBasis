# VaultBasis — Cloud Subprocessor Register & Data Boundary Model
**Standard:** Left-Shift Maximum & Strict Two-Plane Architecture (PRD §64, §71)  
**Version:** 1.0 (Commercial Operational Baseline)  
**Scope:** Commercial Web Plane, Billing/MoR, Transactional Communications & Local Edge Invariants

---

## 1. Executive Architecture & Privacy Statement

VaultBasis operates under a strict **Two-Plane Separation of Concerns**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                    WEB & COMMERCIAL PLANE                              │
│  (Customer Identity, Commercial Billing/MoR, Website Hosting, License Delivery)         │
│  Subprocessors: Vercel, Paddle / Stripe (MoR), Transactional Mailer, GitHub (CI/CD)   │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │ Encrypted .license delivery / download link
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 EDGE EVIDENCE PLANE                                    │
│  (Tax Reconciliation, Broker CSV Intake, Basis Analysis, 1099-DA Receipts & Export)   │
│  Location: 100% Local Practitioner Workstation (Zero Cloud Egress, Air-Gapped Capable) │
│  Subprocessors: NONE                                                                   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

> ### 🛡️ The Canonical Privacy Invariant
> **VaultBasis uses a strictly limited number of cloud service providers to operate its public marketing website, commercial billing, and license delivery communications.**
> 
> **Client tax records, Form 1099-DA CSVs, broker intake files, taxpayer identities (SSN/TIN), wallet addresses, reconciliation findings, and signed Evidence Receipts are processed 100% locally on the practitioner's computer by the VaultBasis Edge application and are NEVER transmitted to, stored on, or processed by any cloud subprocessor.**

---

## 2. Cloud Subprocessor Inventory

| Provider / Subprocessor | Corporate Entity & Location | Primary Purpose | Commercial / Account Data Processed | Client Tax / Case Data Processed? | Operational Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Vercel** | Vercel Inc. (San Francisco, CA, USA) | Public website hosting, serverless API execution (`/api/checkout`, `/api/download`), edge caching, static asset distribution | IP address, browser user-agent, request timestamps, access/order IDs, serverless execution logs | **NO** (Strictly Zero) | **Active (Production & Preprod)** |
| **Vercel Blob** *(or private managed store)* | Vercel Inc. (San Francisco, CA, USA) | Serverless order record persistence, download entitlement tokens, webhook idempotency tracking | Order ID, buyer work email, plan tier, hashed download token (SHA-256), timestamp | **NO** (Strictly Zero) | **Active (Operational)** |
| **Paddle** *(Recommended MoR)* / **Stripe** | Paddle Payments Ltd (UK) / Paddle.com Inc. (USA) *or* Stripe Inc. | Merchant of Record (MoR), checkout UI, payment card processing, global indirect tax (US sales tax / EU VAT) collection & remittance, invoicing | Customer name, work email, firm name, billing address, payment instrument metadata, transaction/refund IDs | **NO** (Strictly Zero) | **Modeled / Evaluation Phase (Target: MoR)** |
| **Transactional Email Provider** *(Postmark / Resend / SendGrid)* | *TBD (Provider Selection in Progress)* | Secure delivery of license files, download authorizations, and commercial invoices | Customer work email, customer name, license ID, temporary download URL (72h TTL) | **NO** (Strictly Zero) | **In Selection / UAT Stage** |
| **GitHub** | GitHub, Inc. (San Francisco, CA, USA) | Source code version control, automated CI/CD pipeline, industrial validation gates | Source code, git commit logs, automated build artifacts, CI runner logs | **NO** (Strictly Zero — no production keys or customer DBs) | **Active (Engineering)** |
| **Apple** | Apple Inc. (Cupertino, CA, USA) | macOS Developer ID code signing validation and notary ticket stapling | Compiled desktop application binary (`.app` bundle) for automated security scanning | **NO** (Zero customer or tax data) | **Active (Release Infrastructure)** |
| **Microsoft / Certificate Authority** | Sectigo / DigiCert / GlobalSign *(TBD)* | Windows Authenticode code signing certificate and RFC 3161 timestamping | Compiled Windows desktop executable (`VaultBasis.exe` hash) | **NO** (Zero customer or tax data) | **Planned (Release Infrastructure)** |

---

## 3. Explicit "NOT A SUBPROCESSOR" Invariant Register

To prevent ambiguity, the following categories are explicitly **NOT** part of the VaultBasis architecture:

* 🚫 **No Hosted LLM / Cloud AI Providers (OpenAI, Anthropic, Google Gemini, DeepSeek, AWS Bedrock):**  
  MMP-2 intelligence is frozen to local, air-gapped deterministic heuristics and optional local on-device neural models. Zero tax data or prompt tokens are sent to any remote API.
* 🚫 **No Cloud Tax Reconciliation Backend:**  
  There is no remote calculation engine, cloud database, or remote worker. Form 1099-DA matching runs 100% in-process on the local machine.
* 🚫 **No Cryptocurrency Custodians or Node Services:**  
  VaultBasis does not hold private keys, seed phrases, or custody assets. It parses read-only transaction export CSVs.
* 🚫 **No Remote DRM / License Heartbeat Tracking:**  
  License enforcement in the Edge application is 100% offline and cryptographic (Ed25519 public key signature verification with monotonic replay rejection). No telemetry ping is made to verify active licenses.
* 🚫 **No Advertising Trackers or Analytics Pixels:**  
  `vaultbasis.com` uses zero Google Analytics, Meta Pixel, or third-party behavioral trackers.

---

## 4. Merchant of Record (MoR) Architectural Analysis: Paddle vs. Stripe

### Context & Corporate Structure
* **Selling Entity:** French Single-Shareholder Company (**EURL** registered in France).
* **Primary Target Market:** United States Certified Public Accountants (CPAs), Enrolled Agents (EAs), and tax accounting practices.
* **Product Form:** Locally installed desktop software with annual license keys ($499 Solo / $1,499 Practice).

### Comparative Assessment

| Dimension | Paddle (Merchant of Record) | Plain Stripe Payments (+ Stripe Tax) |
| :--- | :--- | :--- |
| **Seller of Record** | **Paddle** (Reseller of software to buyer) | **French EURL** (Direct merchant) |
| **US State Sales Tax Liability** | **Assumed by Paddle** (Paddle registers, calculates, collects, files, and remits sales tax across all 50 US states) | **EURL responsibility** (EURL must monitor economic nexus, register in individual US states, and file returns) |
| **EU / International VAT** | **Handled by Paddle** under B2B reverse charge rules | EURL must file EU VAT One-Stop Shop (OSS) |
| **Invoicing & Compliance** | Automatically generates compliant B2B invoices with buyer tax ID / state exemption support | Must be designed, configured, and maintained in Stripe Billing |
| **Dunning, Chargebacks & Disputes** | Handled natively by MoR risk infrastructure | Managed directly by solo founder |
| **Founder Administrative Burden** | **Extremely Low** (Single B2B payout from Paddle to French bank account per month) | **High** (Multi-state compliance, tax filings, legal nexus tracking) |
| **VaultBasis Architecture Alignment** | **Optimal** (Simplifies BILL-001 to verified webhook adapter) | Requires custom tax integration and accounting overhead |

### Accounting & Legal Division of Responsibility under MoR

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              PADDLE (Merchant of Record)                               │
│  • Charges US CPA Buyer ($499 / $1,499 + applicable state sales tax)                   │
│  • Remits US Sales Tax directly to state revenue departments                           │
│  • Issues formal B2B invoice to CPA firm                                               │
│  • Dispatches signed webhook (`transaction.completed`) to VaultBasis API              │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │ Verified Webhook payload
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             FRENCH EURL (VaultBasis Core)                              │
│  • Receives net software royalty payout from Paddle (B2B reverse charge VAT)           │
│  • French corporate accounting: 1 consolidated B2B revenue invoice per payout period   │
│  • Corporate income tax & local French declarations handled with French expert-comptable│
│  • NEVER worries about individual US state tax registrations or nexus thresholds       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Architectural Signing Invariant
Even with Paddle acting as Merchant of Record:
> **Paddle NEVER receives the VaultBasis Ed25519 commercial license private signing key.**
> Paddle only signals commercial transaction confirmation (`ORDER_ELIGIBLE_FOR_PROVISIONING`). The issuance and cryptographic signing of `.license` tokens remain strictly confined to the isolated VaultBasis License Authority.

---

## 5. Data Classification & Protection Invariants

| Data Category | Examples | Storage Location | Retention / Governance |
| :--- | :--- | :--- | :--- |
| **Customer Commercial Identity** | Name, Firm, Work Email, Billing Address | MoR (Paddle/Stripe) + VaultBasis Order Ledger | Retained for statutory accounting and license renewal term |
| **License Credentials (`.license`)** | Customer ID, Plan Tier, Case Capacity, Expiry Date, Ed25519 Signature | Encrypted transit to customer; local file on workstation | Issued with 72h download TTL; persisted in local SQLite store |
| **Client Taxpayer Data** | Form 1099-DA, Broker CSVs, SSN/TIN, Capital Gains Math | **Local Workstation ONLY** | **NEVER leaves practitioner machine** (Zero Egress) |
| **Evidence Receipts** | Signed JSON receipts, SHA-256 bundle digests | **Local Workstation ONLY** | Validated offline via CLI or zero-upload Web Verifier |

---

## 6. Formal Subprocessor Maintenance & Review Protocol

1. **Change Control:** Any new third-party cloud service provider must undergo technical privacy review before introduction to production.
2. **Practitioner Transparency:** Any changes to active subprocessors will be published directly to [`privacy-policy.html`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/apps/web-marketing/privacy-policy.html) and communicated to license holders.
3. **Annual Audit:** Annual inspection of data egress boundaries confirms that zero telemetry or tax data leaks into web plane subprocessors.
