# Technical Incident & Breach Response Runbook (LEGAL-013)

**Version:** 1.0.0  
**Scope:** Technical infrastructure, evidence gathering, credential rotation, and containment protocols for VaultBasis 1.5.0-rc3.  
**Ownership Boundary:** Engineering owns technical containment, log preservation, system isolation, and diagnostic analysis. Founder and Legal Counsel own external notification, regulatory reporting (IRC § 7216, GDPR/CNIL, State Data Breach Notification statutes), customer disclosures, and law enforcement escalation.

---

## 1. System Inventory & Architecture Map

| System / Boundary | Hosting / Provider | Data Processed / Stored | Exposure Risk Level |
|---|---|---|---|
| **VaultBasis Edge Desktop Daemon** | Local Client Machine (`macOS`/`Windows`) | Local 1099-DA/Ledger CSVs, SQLite case DB, Ed25519 signing keys, Evidence Receipts | **Zero Cloud Ingestion** (Zero centralized server exposure) |
| **Public Marketing & Checkout Gateway** | Vercel Edge (`vaultbasis.com`) | Static marketing HTML/CSS/JS, serverless checkout handoff endpoint, license token dispenser | **Low** (Ephemeral serverless execution, zero taxpayer data) |
| **Merchant of Record & Payments** | Paddle.com (PCI-DSS Level 1) | Payment details, customer email, billing address, order transactions | **Delegated** (Paddle manages credit card storage & PCI compliance) |
| **Source Code & CI/CD Pipeline** | GitHub (`KasivisvanathanAmirdhalingam/VaultBasis`) | Source code, test fixtures, build scripts, GitHub Actions secrets | **High** (Build environment, release artifact integrity) |
| **Transactional Email Gateway** | Mailer Provider (SPF / DKIM / DMARC) | Order confirmation emails, download links, license keys | **Medium** (Customer email routing) |

---

## 2. Data Classification Matrix

| Data Class | Examples | System Location | Retention / Storage Policy |
|---|---|---|---|
| **Class A: Taxpayer Identifying Data** | Taxpayer names, SSN/TIN, broker accounts, crypto trade histories, cost basis | **Client Local Disk Only** (`%LOCALAPPDATA%\VaultBasis`, `~/Library/Application Support/VaultBasis`) | Never transmitted to or stored on VaultBasis infrastructure. |
| **Class B: Customer Account Metadata** | Buyer email, purchase date, tier (`Practitioner`/`Firm`), order ID | Paddle MoR, Vercel checkout logs | Retained by Paddle for statutory accounting & tax compliance. |
| **Class C: Cryptographic Identity Data** | Installation Ed25519 public key, release signing certificates | Local receipt envelopes, Azure Artifact Signing / Apple Developer ID | Public keys recorded in receipts; private keys strictly protected in secure enclave / Azure KMS. |
| **Class D: Operational Telemetry** | Build provenance SHA, version string, crash diagnostics | CI logs, release manifests | Zero PII / Zero trade data; sanitized technical logs only. |

---

## 3. Incident Evidence Sources & Log Locations

In the event of an alleged or detected security incident, the engineering team preserves raw, immutable evidence from the following locations:

| Evidence Category | Source / Platform | Retrieval Command / Protocol |
|---|---|---|
| **Local Client Diagnostic Bundle** | Client OS | `VaultBasis Edge -> Help -> Export Diagnostics` (Sanitized system state, zero CSV/trade data) |
| **Vercel Serverless Logs** | Vercel CLI | `vercel logs vaultbasis.com --since=24h --output=raw > vercel_access_incident.log` |
| **Paddle Webhook Event Logs** | Paddle Dashboard / API | Export raw webhook delivery records, failed signature attempts, and transaction payloads |
| **GitHub CI/CD Audit Trail** | GitHub Security Log | Export GitHub Organization Audit Log (Commit authorizations, Secret access events, Workflow dispatches) |
| **Release Artifact Verification** | Public & Blob Storage | Compute SHA-256 digests of live distributed binaries; compare against signed release manifests |

---

## 4. Technical Containment & Mitigation Procedures

```
                       INCIDENT CONTAINMENT PROTOCOL
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
        RELEASE ARTIFACT COMPROMISE             WEB / CHECKOUT COMPROMISE
                 │                                       │
     1. Revoke Signing Certificate           1. Trigger Vercel Rollback
        (Apple Developer ID / Azure)            (Revert to known good deployment)
     2. Invalidate Blob Distribution         2. Rotate Paddle API & Webhook Secrets
     3. Publish Revocation Manifest          3. Enable Cloudflare Under Attack Mode
     4. Notify Microsoft / Apple CAs         4. Isolate Serverless Endpoints
```

### Protocol A: Compromised Release Binary / Supply Chain
1. **Immediate Revocation:** Request Certificate Revocation from Apple Developer CA / Microsoft CA via Azure Trusted Signing.
2. **Distribution Purge:** Invalidate all public download tokens and remove compromised binaries from Vercel Blob storage.
3. **Revocation Notice:** Publish updated `REVOCATION_MANIFEST.json` and emergency security advisory to `https://www.vaultbasis.com/security-disclosure.html`.

### Protocol B: Checkout or Web Gateway Compromise
1. **Vercel Rollback:** Execute `vercel rollback [deployment-id]` to restore the last qualified immutable deployment.
2. **Secret Rotation:** Immediately rotate `BLOB_READ_WRITE_TOKEN`, `PADDLE_WEBHOOK_SECRET_KEY`, and `PADDLE_API_KEY`.
3. **Traffic Quarantine:** Restrict checkout endpoints and inspect incoming webhook payloads for signature forgery.

---

## 5. Credential Rotation Runbook

| Credential / Secret | Location | Rotation Procedure | Escalation Timeframe |
|---|---|---|---|
| **GitHub Actions Secrets** | Repo Settings -> Secrets | Update `BLOB_READ_WRITE_TOKEN`, `AZURE_CREDENTIALS`, `APPLE_API_KEY` | Immediate (< 1 hour) |
| **Paddle Webhook Secret** | Paddle Dashboard -> Notifications | Generate new Webhook Secret Key; update Vercel environment variables | Immediate (< 2 hours) |
| **Vercel Deployment Token** | Vercel Project Settings | Revoke active tokens, generate new token, re-link CLI | Within 4 hours |
| **Code Signing Certificates** | Apple / Microsoft Azure | Invalidate compromised key pair; re-issue new certificate | Within 24 hours |

---

## 6. Escalation Matrix

```
Technical Discovery (Developer)
       │
       ├──> 1. Technical Containment & Isolation (Within 30 mins)
       │
       ├──> 2. Evidence Preservation & Digest Capture (Within 1 hour)
       │
       └──> 3. Brief Founder & Qualified Counsel (Within 2 hours)
                 │
                 ├──> Legal Assessment (IRC § 7216 / GDPR / State Breach Laws)
                 │
                 └──> Mandatory Customer & Regulatory Notifications (Counsel Led)
```
