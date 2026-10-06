# VaultBasis — Subprocessor Register & Data Boundary Architecture
**Standard:** Left-Shift Maximum & Strict Two-Plane Architecture (PRD §64, §71)  
**Version:** 1.0 (Current Production Baseline — MMP-1.5)  
**Lifecycle Mapping:**
* `v1.0` — MMP-1.5 Commercial Baseline & Offline Edge Execution
* `v2.0` — MMP-2 Local Intelligence, Bounded Agents & On-Device Models
* `v2.5` — Multi-Year / Multi-Reviewer Practitioner Workflows
* `v3.x` — Firm-Scale, Enterprise SSO & Ecosystem Integrations

---

## 1. Current Production Privacy Architecture

VaultBasis enforces a strict architectural boundary between two independent planes:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 WEB & COMMERCIAL PLANE                                 │
│  (Customer Identity, Commercial Billing/MoR, Website Hosting, License Delivery)         │
│  Active Subprocessors: Vercel, Paddle / Stripe (MoR), Transactional Mailer, GitHub     │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │ Encrypted .license delivery / download link
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                  EDGE EVIDENCE PLANE                                   │
│  (Tax Reconciliation, Broker CSV Intake, Basis Analysis, 1099-DA Receipts & Export)   │
│  Location: 100% Local Practitioner Workstation                                         │
│  Runtime Policy: No required cloud egress for case processing; air-gap supported       │
│  Cloud Subprocessors for normal Edge case processing: NONE                             │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

> ### 🛡️ The Durable Privacy Invariant
> **VaultBasis uses a strictly limited number of cloud service providers solely to operate its public marketing website, commercial billing, and license delivery communications.**
> 
> **Tax case processing does not require transmission of client case data to VaultBasis cloud infrastructure. Client tax records, Form 1099-DA CSVs, broker intake files, taxpayer identities (SSN/TIN), wallet addresses, reconciliation findings, and signed Evidence Receipts are processed locally on the practitioner workstation by the VaultBasis Edge application.**

---

## 2. Production Subprocessors & Service Provider Lifecycle

*This table maintains an authoritative lifecycle record of service providers, distinguishing active data processors from infrastructure and planned vendors.*

| Provider / Service | Corporate Entity & Location | Primary Purpose | Commercial / Account Data Processed | Client Tax / Case Data Processed? | Lifecycle Classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Vercel** | Vercel Inc. (San Francisco, CA, USA) | Public website hosting, serverless API execution (`/api/checkout`, `/api/download`), edge caching | IP address, user-agent, request timestamps, access/order IDs, runtime execution logs | **NO** (Strictly Zero) | `ACTIVE` |
| **Vercel Blob** *(Private Store)* | Vercel Inc. (San Francisco, CA, USA) | Serverless order record persistence, download entitlement tokens, webhook idempotency tracking | Order ID, buyer work email, plan tier, hashed download token (SHA-256), timestamp | **NO** (Strictly Zero) | `ACTIVE` |
| **Transactional Email Provider** *(Postmark / Resend / SendGrid)* | *Provider under final qualification* | Secure delivery of license tokens, download authorizations, and commercial notices | Customer work email, customer name, license ID, temporary download URL (72h TTL) | **NO** (Strictly Zero) | `QUALIFICATION` |
| **Paddle** *(Merchant of Record)* | Paddle Payments Ltd (UK) / Paddle.com Inc. (USA) | Merchant of Record (MoR), checkout UI, payment card processing, global sales tax/VAT remittance, invoicing | Customer name, work email, firm name, billing address, payment instrument metadata | **NO** (Strictly Zero) | `PLANNED` |
| **GitHub** | GitHub, Inc. (San Francisco, CA, USA) | Source code repository, CI/CD pipeline, industrial validation gates | Source code, git commit logs, automated build artifacts, CI runner logs | **NO** (Zero customer data) | `ENGINEERING_INFRASTRUCTURE` |
| **Apple** | Apple Inc. (Cupertino, CA, USA) | macOS Developer ID code signing validation and notary ticket stapling | Compiled desktop application binary (`.app` bundle) for automated security scanning | **NO** (Zero customer data) | `RELEASE_INFRASTRUCTURE` |
| **Windows CA / Timestamp Authority** | Sectigo / DigiCert / GlobalSign | Windows Authenticode code signing certificate and RFC 3161 timestamping | Compiled Windows desktop executable (`VaultBasis.exe` hash) | **NO** (Zero customer data) | `RELEASE_INFRASTRUCTURE` |
| **VaultBasis Offline Signer** | Internal Air-Gapped Workstation | Ed25519 commercial license token generation and signing ceremony | License ID, customer ID, firm metadata, entitlement tier, validity window | **NO** (Internal key custody, not subprocessor) | `INTERNAL_SIGNING_AUTHORITY` |


---

## 3. Current Non-Subprocessor Components (Software Dependencies vs. Subprocessors)

A critical distinction is maintained between **software dependencies** (which execute locally) and **cloud subprocessors** (third parties that process data on remote infrastructure).

| Component Category | Concrete Example | Classification | Subprocessor Status |
| :--- | :--- | :--- | :--- |
| **Local Runtime Libraries** | `fastapi`, `pydantic`, `cryptography` | Open-source Python library | **NOT a subprocessor** (runs in-process) |
| **Local SQLite Engine** | `sqlite3` (WAL mode) | Embedded database engine | **NOT a subprocessor** (local file on disk) |
| **Local AI / Neural Runtimes** *(MMP-2)* | `llama.cpp`, `ONNX Runtime`, `Ollama` | Local inference engine | **NOT a subprocessor** (zero remote API calls) |
| **Local Model Weights** *(MMP-2)* | Local quantized GGUF/ONNX weights | Static weight files | **NOT a subprocessor** (stored locally) |
| **Model Distribution CDN** *(MMP-2)* | Hugging Face / Cloudflare CDN | One-time binary download | **Service Provider** (no case data transmitted) |
| **Local MCP Connectors** *(MMP-2)* | Filesystem / Local DB MCP Server | Local protocol bridge | **NOT a subprocessor** (local IPC) |
| **Customer-Directed External APIs** | User's firm Google Drive / SharePoint | External storage integration | **Assessed separately** (see Section 7) |
| **Future Hosted Evidence Vault** *(MMP-3)* | Optional cloud backup / firm sync | Hosted cloud storage | **WILL BE a subprocessor** (upon explicit opt-in) |

---

## 4. Edge Data Boundary & Local Processing Invariants

1. **No Required Cloud Egress for Case Processing**:
   The VaultBasis Edge daemon binds strictly to loopback (`127.0.0.1`). Normal tax reconciliation, broker CSV parsing, lot-level matching, discrepancy detection, and Evidence Receipt generation require zero outbound internet connectivity.
2. **Air-Gapped Operation Supported**:
   The application is fully qualified to run on air-gapped workstations. Offline verification of commercial `.license` files and Evidence Receipts uses Ed25519 public keys embedded in the binary without remote activation servers or DRM heartbeats.
3. **Legitimate Operational Connectivity**:
   Future background network actions (such as checking for software updates, downloading regulatory tax rule updates, or optional local model weight updates) are decoupled from case processing and transmit zero client financial records.

---

## 5. Commercial / Merchant of Record (MoR) Data Boundary

### Corporate & Cross-Border Context
* **Selling Entity:** French Single-Shareholder Company (**EURL** registered in France).
* **Primary Target Market:** United States Certified Public Accountants (CPAs), Enrolled Agents (EAs), and tax accounting practices.
* **Product Form:** Locally installed desktop software with annual commercial license tokens ($499 Solo / $1,499 Practice).

### Division of Responsibility under Merchant of Record Model

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              PADDLE (Merchant of Record)                               │
│  • Charges US CPA Buyer ($499 / $1,499 + applicable state sales tax)                   │
│  • Remits US Sales Tax directly to state revenue departments across all 50 states      │
│  • Issues formal B2B compliant invoices to CPA firms                                   │
│  • Dispatches signed webhook (`transaction.completed`) to VaultBasis API              │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │ Verified Webhook payload
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             FRENCH EURL (VaultBasis Core)                              │
│  • Receives net software royalty payout from Paddle (B2B reverse charge VAT)           │
│  • French corporate accounting: 1 consolidated B2B revenue invoice per payout period   │
│  • French corporate tax handled with French expert-comptable                           │
│  • ZERO individual US state tax registrations or physical nexus liability              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Cryptographic Signing Key Boundary
> **Paddle NEVER receives the VaultBasis Ed25519 commercial license private signing key.**
> Paddle only signals commercial transaction confirmation (`ORDER_ELIGIBLE_FOR_PROVISIONING`). The issuance and cryptographic signing of `.license` tokens remain strictly confined to the isolated VaultBasis License Authority.

---

## 6. Future Capability Data Boundary Matrix

| Future Capability | Target Milestone | Expected Execution | Client Case Data Leaves Edge? | New Subprocessor Required? |
| :--- | :--- | :--- | :--- | :--- |
| **Local L2 Explanations** | MMP-2 | Local deterministic heuristics | **No** (Local execution) | **No** |
| **Local RAG & Embeddings** | MMP-2 | Local vector index (SQLite-vec / FAISS) | **No** (Local execution) | **No** |
| **Local Reasoning Agents** | MMP-2 | Local on-device SLMs / models | **No** (Local execution) | **No** |
| **Model Weight Distribution** | MMP-2 | One-time binary download | **No** (Download only) | Content/CDN provider only |
| **Regulatory Corpus Update** | MMP-2 / 2.5 | Signed tax schema download | **No** (Download only) | CDN provider only |
| **Customer-Configured MCP** | MMP-2 / 3 | Customer-selected tools | **Potentially** (User-directed) | Governed under Section 7 |
| **Firm SSO / IAM Integration** | MMP-3 | Cloud Identity Provider (OIDC/SAML) | **Identity only** (No tax data) | **Yes** (Identity Provider) |
| **Evidence Vault (Cloud Backup)** | Future | Hosted encrypted storage | **Yes** (Explicit opt-in) | **Yes** (Cloud Storage Provider) |
| **Hosted AI Inference (Optional)** | Future | Cloud LLM endpoint | **Potentially** (Explicit opt-in) | **Yes** (AI Model Provider) |

---

## 7. Conditional & Customer-Directed External Systems

MMP-2 and MMP-3 introduce interfaces (such as Model Context Protocol — MCP, and Agent-to-Agent — A2A protocols) enabling integration with external services (e.g., firm-managed Google Drive, Microsoft SharePoint, or internal document repositories).

### Architectural & Legal Governance:
1. **User-Directed Routing:** When a practitioner connects VaultBasis to their firm's external storage or MCP server, that connection is established directly from the local workstation to the third-party endpoint using the practitioner's credentials.
2. **Subprocessor Distinction:** Third-party services configured directly by the practitioner (where VaultBasis acts neither as data controller nor as an intermediary routing proxy) are classified as **Customer-Directed External Systems**, governed by the customer's own commercial agreement with that vendor.
3. **VaultBasis-Operated Connectors:** If VaultBasis introduces a hosted intermediary synchronization bridge, that vendor will undergo full subprocessor review and be listed in Section 2.

---

## 8. AI & Model Governance Boundary (MMP-2 Gate: `MMP2-PRIV-001`)

Before any AI, neural inference, or agentic workflow unlocks in MMP-2, it must satisfy mandatory **Data-Flow & Privacy Gate `MMP2-PRIV-001`**:

```
MMP2-PRIV-001 Architectural Qualification Checklist:
├── 1. Data Ingestion: What data fields enter the model context window?
├── 2. Execution Domain: Does inference execute 100% on local CPU/GPU/NPU?
├── 3. Embedding Persistence: Are vector embeddings stored exclusively in local SQLite?
├── 4. Egress Guard: Are local AI runtime processes blocked from external socket communication?
├── 5. Prompt Logging: Are prompt traces and reasoning steps preserved locally without cloud telemetry?
├── 6. Component Provenance: Are model weights audited for commercial open-weights licensing?
└── 7. Cloud Inference Exception: Any optional hosted model requires explicit user opt-in and prior subprocessor registration.
```

### Model Component Registry (Separated from Subprocessor List)
Local model weights and runtimes are tracked in an internal **AI Component Registry** detailing:
* Component Name & Version (e.g., `Llama-3.2-3B-Instruct-Q4_K_M`)
* Model Publisher & Origin (e.g., Meta AI / Hugging Face)
* License & Commercial Use Grants (e.g., Llama 3.2 Community License)
* Cryptographic Hash (SHA-256) of model weight binaries
* Execution Resource Envelope (VRAM / RAM allocation)

---

## 9. Subprocessor Introduction & Qualification Procedure

A new cloud service provider cannot enter production merely because a feature requires it. Every candidate subprocessor must satisfy the four-stage qualification protocol:

1. **Data Flow & Necessity Audit:** Technical architecture review confirming the minimum data necessary is transmitted, and that client tax records remain strictly unexposed.
2. **Security & DPA Review:** Verification of Data Processing Addendum (DPA), Standard Contractual Clauses (SCCs), SOC 2 Type II / ISO 27001 compliance, and GDPR/CCPA alignment.
3. **Register Update & Transparency:** Formal update to Section 2 of this register, synchronization with [`apps/web-marketing/privacy-policy.html`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/apps/web-marketing/privacy-policy.html), and notice to active license holders.
4. **Automated Egress Testing:** Integration of regression tests ensuring local Edge reconciliation remains isolated from the newly introduced web-plane subprocessor.

---

## 10. Change History by MMP Milestone

| Version | Date | MMP Milestone | Summary of Changes | Author |
| :--- | :--- | :--- | :--- | :--- |
| **v1.0** | 2026-10-05 | **MMP-1.5** | Initial production baseline: Vercel hosting/Blob, Paddle/Stripe MoR architecture, transactional mailer, GitHub CI/CD, Apple/Windows release infrastructure. Zero Edge tax data egress frozen. | VaultBasis Core Team |
