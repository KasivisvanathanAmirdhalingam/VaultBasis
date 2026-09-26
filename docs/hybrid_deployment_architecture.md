# VaultBasis — Hybrid Deployment & Incremental Production Architecture

> **Document Version**: v1.0.0  
> **Status**: APPROVED ARCHITECTURE SPECIFICATION  
> **PRD References**: §6.1, §6.3, §13.8, §21.1, §34.1, §34.3, §41 (AC-06, AC-07), §50.4  

---

## 1. System Topology Overview

VaultBasis enforces a dual-tier separation of concerns to simultaneously satisfy two paramount constraints:
1. **Public Internet Accessibility & Universal Verification**: Anyone on the internet must be able to explore the marketing portal, examine the normative Evidence Contract specification, and independently verify Ed25519-signed Outcome Receipts in a browser.
2. **Zero Token Bleed & Zero Transaction Egress (PRD §21.1)**: Under no circumstances may Form 1099-DA forms, tax software CSVs, or customer financial transaction rows leave the local machine or be transmitted over public networks.

```
                      PUBLIC INTERNET (Vercel Edge Platform)
  ┌───────────────────────────────────────────────────────────────────────────┐
  │  Vercel Edge CDN (Production Domain: https://*.vercel.app)                │
  │                                                                           │
  │  • / (apps/web-marketing) ──> Institutional Landing & Value Proposition  │
  │  • /verifier (apps/web-verifier) ──> Autonomous Client-Side WebCrypto    │
  │  • /schemas/receipt-v0.1.json ──> Normative Evidence Contract Schema     │
  │  • /404 ──> Fail-Safe Institutional Static Fallback                       │
  │                                                                           │
  │  * ZERO Backend Services       * ZERO Cloud Database                      │
  │  * ZERO Remote Logs            * ZERO Transaction Ingestion                │
  └─────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                         Client-Side Localhost Bridge
                         (Health Probe: http://127.0.0.1:8000/api/health)
                                        │
                                        ▼
                      LOCAL MACHINE / AIRGAP (Local Edge Runtime)
  ┌───────────────────────────────────────────────────────────────────────────┐
  │  Localhost Customer Premises (http://127.0.0.1:8000)                      │
  │                                                                           │
  │  • Local Dashboard (/) ──> 3-Screen Case Review & Reconciliation Console │
  │  • Local REST API (/api/*) ──> Form 1099-DA Parsing & Math Engine         │
  │  • Local SQLite Store (/data/vaultbasis.db) ──> Case Persistence          │
  │  • Local Ed25519 Engine ──> Cryptographic Outcome Signing                 │
  │                                                                           │
  │  * Egress Blocked: Zero outbound telemetry, Zero cloud AI API calls       │
  └───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Incremental Vercel Configuration & Pipeline

### 2.1 Configuration (`vercel.json`)
The production build is declared in `vercel.json` with strict HTTP security headers:
- `buildCommand`: `node scripts/build_public_web.js`
- `outputDirectory`: `dist/public-web`
- `cleanUrls`: `true`
- **Rewrites**:
  - `/verifier` ➔ `/verifier/index.html`
  - `/schemas/(.*)` ➔ `/schemas/$1`
  - `/about` ➔ `/index.html`
  - `/marketing` ➔ `/index.html`
- **Security Headers**:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`

### 2.2 Deterministic Static Artifact Packager (`scripts/build_public_web.js`)
Builds static distribution assets into `dist/public-web`:
1. Injects Git commit SHA and build timestamp.
2. Packages `apps/web-marketing` to `dist/public-web/index.html`.
3. Packages `apps/web-verifier` to `dist/public-web/verifier/index.html`.
4. Copies normative `schemas/receipt/receipt-v0.1.json` to `dist/public-web/schemas/`.
5. Generates custom `404.html`.
6. Executes automated Zero-Leakage audit checking that 0 `.key`, `.pem`, `.db`, or `.env` files are included.

### 2.3 NPM Workflow (`package.json`)
```bash
# Build static distribution bundle
npm run build

# Run comprehensive pre-commit left-shift validation
npm run validate

# Deploy preview slice to Vercel
npm run deploy:preview

# Deploy production slice to Vercel
npm run deploy:prod
```

---

## 3. Left-Shift Validation from Day 1

Every incremental slice is subjected to continuous automated left-shift gates prior to every commit:

1. **Syntax & Schema Compilation**: Python 3.13 compilation + Draft-07 JSON Schema conformance.
2. **Comprehensive Test Suite**:
   - `tests/quality/atdd`: End-to-end CPA journeys and reconciliation workflows.
   - `tests/quality/bdd`: Given-When-Then criteria for all 7 blocking preview gates.
   - `tests/quality/tdd`: Decimal exactness, sub-atomic satoshi precision, RFC 8785 canonicalization.
   - `tests/quality/ddd`: Domain models, case aggregate lifecycle, source hash integrity.
   - `tests/quality/production_deployment`: Vercel configuration validity, build execution, and zero-leakage security audit.
   - `tests/unit`: Slice 1 cryptographic primitives, Slice 2 Form 1099-DA/Koinly CSV parsers, and FastAPI REST endpoints.
3. **Standalone Clean-Machine CLI Verification**: Valid and tampered golden fixture execution.
4. **Local Key Permission Audit**: Permissions enforced to 0600.
5. **Incremental Production Bundle Audit**: Automated check that `dist/public-web` is complete, clean, and free of private keys or databases.

---

## 4. User Experience: Public Internet to Local App Bridge

1. A user visits the public marketing site hosted on Vercel (`https://*.vercel.app`).
2. The user clicks **Launch Local Edge**.
3. The client-side application probes `http://127.0.0.1:8000/api/health`.
   - **If Local Edge is Running**: The browser redirects immediately to `http://127.0.0.1:8000/`, granting instant access to the local Form 1099-DA reconciliation console.
   - **If Local Edge is Not Running**: A modal displays step-by-step launch instructions:
     ```bash
     git clone <repo-url> && cd VaultBasis
     ./scripts/launch.sh
     ```
     Once launched, clicking **Check Connection & Open App** connects seamlessly.
4. **Third-Party Verification**: Anyone receiving a `.vb-receipt.json` outcome receipt can navigate to `/verifier` on the public domain or open `apps/web-verifier/index.html` locally. Verification executes entirely client-side inside the browser using WebCrypto (`crypto.subtle`) with zero data transmission over the network.
