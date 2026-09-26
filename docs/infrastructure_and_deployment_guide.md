# VaultBasis — Infrastructure, Deployment Artifacts & Operations Guide

> **Document Version**: v1.0.0-MMP1  
> **Standard**: Granite-Grade Industrial Standard / Left-Shift Maximum  
> **PRD References**: §6.1, §6.3, §13.8, §18.1, §21.1, §23.1, §34.1, §34.3, §41 (AC-01 through AC-07), §50.4, §62.1  
> **Status**: APPROVED OPERATIONS RUNBOOK  

---

## 1. Executive Infrastructure Topology

VaultBasis operates as a **dual-tier hybrid assurance topology**. The system strictly decouples the public verification and discovery surface (hosted on the public internet) from the customer reconciliation runtime (hosted locally within the customer's airgapped trust boundary).

```
                      PUBLIC INTERNET (Vercel Edge Platform)
  ┌───────────────────────────────────────────────────────────────────────────┐
  │  Vercel Edge CDN Infrastructure (https://*.vercel.app)                    │
  │                                                                           │
  │  • / ──> apps/web-marketing/index.html (Institutional Discovery)          │
  │  • /verifier ──> apps/web-verifier/index.html (Client-Side WebCrypto)     │
  │  • /schemas/receipt-v0.1.json ──> Normative Evidence Contract Schema     │
  │  • /sample-receipt.json ──> Valid Golden Receipt Fixture                 │
  │  • /404 ──> Fail-Safe Institutional Static Response                      │
  │                                                                           │
  │  [INFRASTRUCTURE GUARANTEES]                                              │
  │  • Strict HTTP Security Headers (CSP, HSTS 2-Yr, nosniff, DENY)          │
  │  • ZERO Serverless Functions / Python Runtimes                           │
  │  • ZERO Cloud Databases / Storage Buckets                                │
  │  • ZERO Customer Financial Transaction Processing                        │
  └─────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                         Client-Side Localhost Bridge
                         (Health Probe: http://127.0.0.1:8000/api/health)
                                        │
                                        ▼
                      LOCAL CUSTOMER PREMISES (Local Edge Runtime)
  ┌───────────────────────────────────────────────────────────────────────────┐
  │  Localhost Airgap Edge (http://127.0.0.1:8000)                            │
  │                                                                           │
  │  • FastAPI REST Engine on Uvicorn (edge/api/app.py)                       │
  │  • Local 3-Screen Dashboard (apps/web-dashboard/index.html)               │
  │  • SQLite Storage Engine with WAL Mode (data/vaultbasis.db)               │
  │  • Ed25519 Installation Keypair Engine (data/keys/installation.key)       │
  │  • Exact Decimal Math & 13 Bounded Outcome States                         │
  │                                                                           │
  │  [SECURITY POSTURE & ZERO TOKEN BLEED - PRD §21.1]                        │
  │  • 100% Local Ingestion of Form 1099-DA & Koinly CSVs                     │
  │  • Zero Network Egress: Blocked from all outbound internet traffic        │
  │  • Key Isolation: 0600 file permissions enforced                          │
  └───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Infrastructure Specifications

### 2.1 Public Cloud Infrastructure (Vercel Edge Platform)

| Property | Value | Rationale |
| :--- | :--- | :--- |
| **Hosting Platform** | Vercel Edge CDN | Global edge distribution, sub-50ms latency worldwide, DDoS protection. |
| **Runtime Architecture** | Pure Static Distribution (`dist/public-web`) | Eliminates remote attack surfaces; ensures zero customer financial data can be sent to or stored on cloud servers. |
| **Vercel Engine Config** | `vercel.json` (Version 2) | Declares deterministic build command, clean URLs, security headers, and rewrite routing. |
| **Rewrites** | `/verifier` ➔ `/verifier/index.html`<br>`/schemas/(.*)` ➔ `/schemas/$1`<br>`/about` & `/marketing` ➔ `/index.html` | Clean URL structure matching enterprise conventions. |
| **Security Headers** | `X-Content-Type-Options: nosniff`<br>`X-Frame-Options: DENY`<br>`X-XSS-Protection: 1; mode=block`<br>`Strict-Transport-Security: max-age=63072000; includeSubDomains; preload` | Protects users against clickjacking, MIME-sniffing, and protocol downgrades. |

### 2.2 Local Airgap Edge Infrastructure

| Property | Value | Rationale |
| :--- | :--- | :--- |
| **Local Service** | Python 3.10+ / FastAPI / Uvicorn | High-performance, lightweight asynchronous local daemon. |
| **Default Port** | `127.0.0.1:8000` | Standard local HTTP interface; accessible only via loopback interface. |
| **Persistence Engine** | SQLite 3 with Write-Ahead Logging (WAL) | ACID-compliant, zero-configuration local single-file database (`data/vaultbasis.db`). |
| **Cryptographic Engine**| Ed25519 (`cryptography.hazmat`) | High-speed, 128-bit security level, resistant to side-channel attacks, signature size of 64 bytes. |
| **Key Storage** | `data/keys/installation.key` | Generated locally on first boot with POSIX `0600` permissions. Key never leaves localhost. |
| **Network Egress Policy**| `STRICT_LOCAL_ONLY` | Inbound loopback only. Zero telemetry, zero analytics, zero external API requests (PRD §21.1). |

---

## 3. Deployment Artifacts Inventory

The build pipeline compiles deterministic, self-contained artifacts for both tiers:

| Artifact Path | Target Tier | Description | Security Controls |
| :--- | :--- | :--- | :--- |
| `dist/public-web/index.html` | Vercel CDN | Public marketing and institutional portal with live localhost probe bridge. | No tracking scripts; CSP headers enforced; static only. |
| `dist/public-web/verifier/index.html` | Vercel CDN | Public web verifier executing autonomous Ed25519 verification via WebCrypto. | Zero network requests during verification; runs 100% in-browser. |
| `dist/public-web/schemas/receipt-v0.1.json` | Vercel CDN | Normative JSON Schema for Evidence Contract v0.1. | Read-only static JSON schema conforming to Draft-07. |
| `dist/public-web/sample-receipt.json` | Vercel CDN | Golden valid outcome receipt fixture for instant user testing. | Anonymized test vectors; zero real taxpayer PII. |
| `dist/public-web/sample-receipt-tampered.json` | Vercel CDN | Golden tampered receipt fixture for demonstrating tamper detection. | Test vector with invalidated signature. |
| `dist/public-web/404.html` | Vercel CDN | Custom institutional 404 error page. | Static fallback page. |
| `apps/web-dashboard/index.html` | Localhost Edge | Local 3-screen customer console (Case List, Case Review, Outcome Receipt). | Served exclusively over loopback (`http://127.0.0.1:8000/`). |
| `apps/verifier/verify_receipt.py` | Local & Export | Standalone, zero-dependency Python CLI verifier. | Can be run on any disconnected, airgapped clean machine. |
| `VaultBasis_Evidence_<case_id>.zip` | Export Bundle | Self-contained audit bundle containing receipt, schema, verifier, and raw files. | Generated on-demand on local edge; downloaded directly to local disk. |

---

## 4. Step-by-Step Deployment Runbooks

### 4.1 Tier 1: Public Web Deployment to Vercel

#### Step 1: Pre-Deployment Validation (Left-Shift Gate)
Before publishing any increment to production infrastructure, run the comprehensive left-shift pre-commit pipeline:
```bash
./scripts/validate_before_commit.sh
```
All 6 industrial verification steps must return green:
1. Python syntax compilation check.
2. Draft-07 JSON Schema conformance check.
3. Automated test suite (ATDD, BDD, DDD, TDD, Unit, Deployment).
4. Golden fixture CLI verifier check.
5. Key permission & security posture check.
6. Incremental Vercel public web build & zero-leakage security audit.

#### Step 2: Build Static Distribution Bundle
Execute the deterministic packaging script:
```bash
npm run build
# OR directly via node:
node scripts/build_public_web.js
```
The script:
- Creates `dist/public-web/`.
- Injects Git commit SHA and ISO build timestamp.
- Packages marketing, verifier, normative schema, and sample receipts.
- Scans `dist/public-web/` recursively to guarantee 0 `.key`, `.pem`, `.db`, or `.env` files are included.

#### Step 3: Deploy to Vercel (Preview or Production)
```bash
# To deploy a preview slice:
npm run deploy:preview

# To deploy directly to production:
npm run deploy:prod
```
*Note: Ensure the Vercel CLI is authenticated via `npx vercel login` or `VERCEL_TOKEN` environment variable.*

#### Step 4: Production Smoke Testing
Once deployed to Vercel (e.g., `https://vaultbasis.vercel.app`):
1. Navigate to `/`: Verify marketing portal loads with HTTP 200 and security headers.
2. Navigate to `/verifier`: Verify public verifier loads. Click **Test with Valid Sample Receipt** and confirm all 4 checks return `PASS`. Click **Test with Tampered Receipt** and confirm signature check returns `FAIL`.
3. Navigate to `/schemas/receipt-v0.1.json`: Confirm raw Draft-07 schema is accessible.
4. Click **Launch Local Edge**: Verify the connection modal opens and cleanly probes `http://127.0.0.1:8000/api/health`.

---

### 4.2 Tier 2: Localhost Edge Runtime Deployment

#### Option A: Native Launch Script (Recommended for Development & Local Production)
```bash
# Make script executable (if not already)
chmod +x ./scripts/launch.sh

# Launch local Edge daemon:
./scripts/launch.sh
```
The script:
- Activates Python virtual environment or system Python.
- Verifies and installs dependencies from `requirements.txt`.
- Initializes `data/keys/` and generates local Ed25519 installation keypair with `0600` permissions.
- Initializes SQLite database at `data/vaultbasis.db`.
- Starts Uvicorn server on `http://127.0.0.1:8000` with auto-reload enabled.

#### Option B: OCI / Docker Container Launch (Airgapped Production Environment)
For environments requiring containerized isolation:
```bash
# 1. Build the hardened container image
docker build -t vaultbasis-edge:preview -f Dockerfile .

# 2. Run the container with a local data volume mount
docker run -d \
  --name vaultbasis-edge \
  -p 127.0.0.1:8000:8000 \
  -v $(pwd)/data:/app/data \
  --network none \
  vaultbasis-edge:preview
```
*Note: In production airgapped mode, `--network none` guarantees mathematically zero egress.*

#### Step 3: Localhost Verification
Verify edge daemon health via curl:
```bash
curl -s http://127.0.0.1:8000/api/health
```
Expected output:
```json
{
  "status": "HEALTHY",
  "service": "VaultBasis Edge",
  "version": "0.1.0-preview",
  "installation_key_id": "<64-character-hex-sha256>",
  "egress_policy": "STRICT_LOCAL_ONLY"
}
```

Access the local reconciliation dashboard in any browser at:
`http://127.0.0.1:8000/`

---

## 5. Security Posture & Zero-Leakage Invariants

1. **Static Distribution Boundary**: The `dist/public-web` folder is strictly verified prior to deployment. The automated test `test_zero_egress_and_secret_leak_in_build_artifacts` asserts that no sensitive file extensions (`.key`, `.pem`, `.db`, `.sqlite`, `.env`) can ever enter the distribution package.
2. **Localhost CORS Policy**: The local REST API on `127.0.0.1:8000` only accepts local origin requests and returns health status to the public web client probe.
3. **Receipt Portability**: Outcome Receipts (`.vb-receipt.json`) contain cryptographic hashes and signatures of differences, but never raw unredacted personal identifiers (SSNs, EINs, account numbers) per PRD §13.4.

---

## 6. Incident Response & Rollback Procedures

### 6.1 Vercel Rollback
If a defect is identified on the public web surface:
```bash
# Rollback to the previous stable Vercel deployment instantly:
npx vercel rollback
```

### 6.2 Local Database Recovery
The local SQLite store (`data/vaultbasis.db`) operates in WAL mode:
```bash
# Backup active local case database:
sqlite3 data/vaultbasis.db ".backup 'data/vaultbasis_backup_$(date +%Y%m%d).db'"
```
All cases are stored immutably once reconciled and signed.
