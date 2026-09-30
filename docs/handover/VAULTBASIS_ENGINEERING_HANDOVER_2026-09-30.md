# VaultBasis Engineering Handover — 2026-09-30

**Effective date:** 2026-09-30  
**Directive:** FINAL ENGINEERING HANDOVER / STOP-WORK  
**Stop-work scope:** No implementation, remediation, deployment, merging, release promotion, UX changes, dependency changes, or branch restructuring.  
**Prepared by:** Engineering session ending 2026-09-30  
**Repository:** https://github.com/KasivisvanathanAmirdhalingam/VaultBasis

---

## 1. Repository State

### 1.1 Remote

```
origin  https://github.com/KasivisvanathanAmirdhalingam/VaultBasis (fetch)
origin  https://github.com/KasivisvanathanAmirdhalingam/VaultBasis (push)
```

### 1.2 Branch SHA Matrix

| Branch | Local SHA | Remote SHA (origin) | Relationship | Tracking |
|---|---|---|---|---|
| `main` | `73a4523` | `73a4523` | In sync | `origin/main` |
| `release/mmp-1.1` | `73a4523` | `73a4523` | In sync | `origin/release/mmp-1.1` |
| `fix/mmp11-dist-mac-001` | `83d78db` | `83d78db` | In sync (pushed) | `origin/fix/mmp11-dist-mac-001` |
| `fix/mmp11-pres-003` | `586a83c` | `73a4523` | **LOCAL ONLY — 1 commit ahead of origin** | `origin/fix/mmp11-pres-003` points to `73a4523` |
| `lab/mmp-2-ai` | `412a6db` | NOT CHECKED | Local only; no verification of remote state | — |
| `release/mmp-1` | `bc52595` | NOT CHECKED | Historical | — |

**Critical note on `fix/mmp11-pres-003`:** The remote `origin/fix/mmp11-pres-003` ref points to `73a4523` (the release baseline). The local branch has one additional unpushed commit (`586a83c`). The candidate has never been deployed to production.

### 1.3 Active Worktrees (local, agent-created — do not delete without confirming contents)

```
.claude/worktrees/agent-a32179eabfc9b986c  @ 034eb38
.claude/worktrees/agent-ac09cf3ae3a719828  @ 5dc4962
.claude/worktrees/agent-ac4605dbee025833d  @ cfb55b8
```

These are isolated git worktrees created by the Claude agent during prior sessions. They are not on any named branch. Their paths are inside `.claude/` which is untracked by git.

### 1.4 Working Tree Status (current branch: `fix/mmp11-pres-003`)

```
On branch fix/mmp11-pres-003
Untracked files:
  .claude/

nothing added to commit but untracked files present
```

`.claude/` is the agent memory system. It is untracked and local-only. It contains no source code. It must not be staged or committed.

`package.json` and `package-lock.json` were contaminated during this session by `npm install --save-dev playwright` (run to enable screenshot capture). Both files have been restored to their `586a83c` state via `git restore`. Contamination is cleared.

### 1.5 Stashes

None (`git stash list` returned empty).

### 1.6 Unpushed Commits

| Branch | Unpushed |
|---|---|
| `main` | None |
| `release/mmp-1.1` | None |
| `fix/mmp11-dist-mac-001` | None |
| `fix/mmp11-pres-003` | **1 commit unpushed** — `586a83c` |
| `lab/mmp-2-ai` | Not verified |

### 1.7 Generated / Local Files

- `dist/public-web/` — generated output from `node scripts/build_public_web.js`. Not committed. Must be regenerated from source before any deployment.
- `.claude/` — agent memory system. Untracked. Not a build artifact.
- No other generated or temporary files present in the working tree.

### 1.8 Running Processes

- **PID 65956** — `VaultBasis.app` launched from App Translocation path. This is the founder's own application from the qualification session. **Not started by this engineering session. Not terminated.**
- **PID 74819** — `python3 -m http.server 7799` started by this session for local visual review. **Terminated** during handover preparation.
- No uvicorn processes running.

---

## 2. Candidate Classification

### 2.1 Public Web IA Candidate

| Field | Value |
|---|---|
| Branch | `fix/mmp11-pres-003` |
| SHA | `586a83c` |
| Commit message | `fix(mmp11-pres-003): converge practitioner IA — canonical nav, footer, vocabulary, Trust Center` |
| Status | **LOCAL IMPLEMENTATION CANDIDATE ONLY** |
| Founder acceptance | **REJECTED BY FOUNDER** |
| Production deployment | **NOT DEPLOYED** |
| Release qualification | **NOT RELEASE-QUALIFIED** |
| Automated test result | 205 passed / 1 skipped (local run against localhost build) |
| Basis for rejection | Visual acceptance performed against `http://localhost:7799` local render, not against production domain. Localhost evaluation does not constitute founder UX acceptance. Qualification label "FOUNDER UX REVIEW PASS" was incorrectly applied and is hereby retracted. |

**MMP11-PRES-003 = REJECTED BY FOUNDER**

The production domain (vaultbasis.com) continues to serve the design deployed at `73a4523`. Screenshots taken by the founder against the production domain show the prior IA (Trust & Assurance navigation label, Resources nav item, secondary homepage jump-navigation strip, legacy footer format). Those elements are from the live production deployment, not from the undeployed `586a83c` candidate. The candidate's local build does contain the revised IA, but it has never reached production.

### 2.2 Edge Distribution Candidate

| Field | Value |
|---|---|
| Branch | `fix/mmp11-dist-mac-001` |
| SHA | `83d78db` |
| Commit message | `fix(mmp11-dist-mac-001): close MAC-UX-001/002 and offline-verifier network dependency` |
| Status | **IMPLEMENTED — CI PENDING HUMAN REVIEW** |
| Founder qualification | **NOT QUALIFIED** — CI artifact from `83d78db` has not been downloaded and subjected to founder recipient-path qualification |
| Prior qualification result | `73a4523` artifact (CI Run #64) received FAIL from founder — 8 defects identified during Mac qualification |

### 2.3 Current Production Baseline

| Field | Value |
|---|---|
| Source SHA | `73a4523` |
| Commit message | `fix(mmp11-pres-002): converge practitioner experience and restore validation-ready UI` |
| Branches at this SHA | `main`, `release/mmp-1.1`, `origin/main`, `origin/release/mmp-1.1` |

---

## 3. Production State

### 3.1 Vercel Deployment

**SOURCE SHA NOT ESTABLISHED FROM LOCAL ENVIRONMENT.**

The current Vercel production deployment state for `vaultbasis.com` and `www.vaultbasis.com` — including deployment ID, immutable deployment URL, build source SHA, deployment timestamp, alias mapping, and protection state — cannot be established from the local repository. These values are only retrievable from the Vercel dashboard or Vercel CLI with project credentials.

**What is known:**
- The production domain is `vaultbasis.com`. A `www.vaultbasis.com` alias is expected but not independently confirmed.
- The deployment serving production was built from source at or before `73a4523` (the HEAD of `main`). The exact build SHA Vercel used is NOT ESTABLISHED — Vercel does not guarantee SHA-to-deployment traceability without explicit CI-triggered deployments or Vercel CLI confirmation.
- **DEPLOY-SEC-001 is PENDING:** Anonymous access to `vaultbasis.com` was identified as open (Vercel Deployment Protection not enforced). Whether this was subsequently restored is NOT ESTABLISHED. This is a P0 security item.

### 3.2 Rollback Target

The last known stable production baseline is `73a4523`. No rollback has been executed. If a rollback is required, the new developer must use the Vercel dashboard to identify the prior immutable deployment URL and re-alias it.

### 3.3 Production/Candidate Discrepancy

The founder's screenshots during this session show navigation elements including "Trust & Assurance", "Resources", a secondary homepage jump-navigation strip, and the legacy footer. These are from the **currently deployed production experience at vaultbasis.com** (source `73a4523` or earlier), which has not been updated.

The unpublished local candidate `586a83c` contains a different IA (canonical nav: How It Works / Trust Center / About / Verify Receipt / Request Access; no jump-nav; four-column footer). This candidate has never been deployed. It does not fix the production experience. It is not a replacement for the current production state.

---

## 4. Production/Candidate Discrepancy (detailed)

| Element | Production (vaultbasis.com, `73a4523` or earlier) | Local candidate (`586a83c`, never deployed) |
|---|---|---|
| Primary nav | How It Works / Trust & Assurance / Resources / About | How It Works / Trust Center / About |
| CTA buttons | Varies by build | Verify Receipt ↗ / Request Access |
| Homepage jump-nav | Present (secondary navigation strip) | Removed |
| Trust page label | Trust & Assurance | Trust Center |
| Footer structure | Legacy multi-block | Product / Trust / Company / Legal (4 columns) |
| Deployment status | LIVE at vaultbasis.com | NOT DEPLOYED |

The `586a83c` candidate does not correct what a visitor to vaultbasis.com sees today. Only a Vercel deployment of the candidate (after founder acceptance) would change the production experience.

---

## 5. Edge Distribution State

### 5.1 Mac RC3 Candidate

| Field | Value |
|---|---|
| Source branch | `fix/mmp11-dist-mac-001` |
| Source SHA | `83d78db` |
| CI run | CI run for `83d78db` — **run number and database ID NOT ESTABLISHED** from local environment; must be retrieved from GitHub Actions UI |
| Artifact name | `vaultbasis-rc3-candidate-macos-latest` (expected, based on CI workflow configuration) |
| GitHub artifact digest | **NOT ESTABLISHED** — must be retrieved from GitHub Actions artifact page |
| Inner distribution ZIP SHA-256 | **NOT ESTABLISHED** — requires downloading artifact and computing `shasum -a 256 <inner-zip>` |
| Packaging qualification | IMPLEMENTED (CI pipeline runs `build_rc3_macos.py`, PRE-ZIP gate, POST-ZIP gate) |
| Founder recipient-path qualification | **NOT COMPLETED** — `83d78db` artifact has not been downloaded and qualified by founder |

**Prior qualification result:** `73a4523` artifact (CI Run #64, artifact 54.9 MB) — **FAIL**. 8 defects reported:
- MAC-NAV-001: `/verifier` route returned 404 (Vercel-only session check in web verifier)
- MAC-NAV-002/003/004/005: `/faq`, `/contact`, `/security-disclosure` returned 404
- MAC-UX-001: Logo inconsistency (Edge dashboard vs marketing site)
- MAC-UX-002: Text contrast (muted text too light)
- MAC-FUNC-001: Offline receipt verifier not present
- Additional: Google Fonts CDN dependency in offline verifier

These defects are addressed in `fix/mmp11-dist-mac-001 @ 83d78db`. Qualification of that artifact is pending.

**Note:** GitHub artifact-container digest (the ZIP wrapper that GitHub Actions produces) is distinct from the inner release ZIP SHA-256 (the file a recipient extracts and launches). Both must be recorded for release identity. Neither is established here.

### 5.2 Windows RC3 Candidate

| Field | Value |
|---|---|
| Source SHA | `5dc4962` (Windows onedir switch + Defender exclusion) |
| CI run | NOT ESTABLISHED |
| Artifact | NOT ESTABLISHED |
| Inner ZIP SHA-256 | NOT ESTABLISHED |
| Qualification | PRE/POST-ZIP qualification NOT COMPLETED |
| Windows spec file | No `VaultBasis-RC3-Windows.spec` found in working tree; build uses `scripts/build_rc3_windows.py` directly |

---

## 6. Security State

| Item | Implementation Evidence | Deployed/Production Verified | State |
|---|---|---|---|
| **DEPLOY-SEC-001** — Restore Vercel Deployment Protection (anonymous access) | No code change required; Vercel dashboard action | NOT VERIFIED — requires human Vercel dashboard action | **PLANNED / USER ACTION REQUIRED** |
| **SEC-002** — Blob-backed expiring entitlement: `sha256(token).json`, 72h TTL, timing-safe, artifact-hash binding, fail-closed | Implemented in `api/entitlement-store.js`, `api/download.js`, `api/verifier-page.js`, `api/verifier-session.js` | NOT VERIFIED — production smoke test pending | **IMPLEMENTED / NOT PRODUCTION-VERIFIED** |
| **SEC-003** — `PUBLIC_BASE_URL` env var for provisioning emails; adversarial host-header rejection | Implemented in `api/request-access.js` | NOT VERIFIED — `PUBLIC_BASE_URL` Vercel env var not confirmed; adversarial host-header test not run against production | **IMPLEMENTED / NOT PRODUCTION-VERIFIED** |
| **SEC-004** — CORS origin restriction | Implemented in `edge/api/app.py` | Verified in code; not tested against deployed production | **IMPLEMENTED** |
| **SEC-005** — Fixture signing-key disposition | `tests/fixtures/keys/installation_ed25519.key` and `.pub` exist in repository history | Decision on scope classification and history-rewrite NOT MADE | **PLANNED — REQUIRED BEFORE CPA-001** |
| **SEC-006 / DATA-001** — Zero egress from Edge kernel | Enforced by local-only architecture; network behavior documented in Scope & Limitations | Not independently verified against deployed production app | **IMPLEMENTED** |

---

## 7. Access-Request Implementation

The complete design-partner access flow is as follows. Steps marked are the implemented/verified state as of `73a4523` (production HEAD):

### Step 1 — Browser CTA / Modal
**IMPLEMENTED.** The marketing site presents a "Request Access" button which opens a modal (`openAccessModal()`). The modal collects Full Name and Contact Email. Source: `apps/web-marketing/index.html`, modal injected via `partials/modal.html` at build time.

### Step 2 — Endpoint
**IMPLEMENTED.** Form submits to `POST /api/request-access` (Vercel serverless function at `api/request-access.js`).

### Step 3 — Storage
**IMPLEMENTED.** `api/request-access.js` writes a preview-access record to Vercel Blob private storage at `preview-access/<sha256(email)>.json`. Record contains: `email`, `name`, `status: ACTIVE`, `createdAt`, `expiresAt` (72h), `entitlementToken` (64-char hex).

### Step 4 — Email / Provisioning
**IMPLEMENTED WITH ETHEREAL — NOT PRODUCTION EMAIL.**  
`api/request-access.js` uses `nodemailer` with `smtp.ethereal.email` as the SMTP host. This is a UAT email sink. Emails are **not delivered to the recipient**. They are captured at `ethereal.email` and accessible only to whoever has Ethereal credentials. The provisioning email contains the access token and download link. **This is not a production-qualified email delivery path.**

The email is sent from `"VaultBasis Provisioning" <no-reply@vaultbasis.com>` but is routed through Ethereal SMTP, not through any real mail transport. The recipient does not receive an email. The `uatPreviewUrl` returned in the response body is an Ethereal-hosted preview URL — it is not a real inbox delivery.

### Step 5 — Preview Credential
**IMPLEMENTED.** The `entitlementToken` is embedded in the provisioning email download link as `?token=<token>`.

### Step 6 — Entitlement
**IMPLEMENTED.** `api/entitlement-store.js` validates the token against the Blob-stored record. Checks: token format, hash-keyed lookup, `status === ACTIVE`, expiry, artifact-hash binding.

### Step 7 — Artifact Download
**IMPLEMENTED (dependent on promoted artifact).** `api/download.js` reads `rc3/current/manifest.json` from private Blob, validates entitlement, resolves platform, and redirects to the artifact Blob URL. **The manifest only exists after an explicit artifact promotion step (workflow_dispatch `promote: true`).** If the manifest has not been promoted, download returns 503.

### Step 8 — Verifier Access
**IMPLEMENTED.** `api/verifier-page.js` serves the Web Verifier page only after validating the `vb_session` cookie against a session record in Blob. `api/verifier-session.js` creates sessions. `api/verifier-session-check.js` provides defense-in-depth client-side validation.

### Summary of incomplete steps

| Gap | Severity |
|---|---|
| Ethereal SMTP — recipient does not receive email | **P0 — release blocker** |
| Artifact promotion manifest — download returns 503 if not promoted | P1 — blocks distribution |
| Production email delivery (real SMTP / SES / Postmark) | Not implemented |
| Production smoke test of full flow | Not completed |

---

## 8. Public Web Architecture

### 8.1 Source Files (source-of-truth, committed)

| Path | Purpose |
|---|---|
| `apps/web-marketing/index.html` | Marketing homepage source (uses sentinel comments for build-time partial injection) |
| `apps/web-marketing/trust-assurance.html` | Trust & Assurance page source |
| `apps/web-marketing/about.html` | About page source |
| `apps/web-marketing/faq.html` | FAQ page source |
| `apps/web-marketing/contact.html` | Contact page source |
| `apps/web-marketing/privacy-policy.html` | Privacy policy source |
| `apps/web-marketing/terms-of-service.html` | Terms of service source |
| `apps/web-marketing/security-disclosure.html` | Security disclosure source |
| `apps/web-marketing/verifier-access.html` | Verifier access page source |
| `apps/web-marketing/partials/header.html` | Shared header partial (injected at build time) |
| `apps/web-marketing/partials/footer.html` | Shared footer partial (injected at build time) |
| `apps/web-marketing/partials/modal.html` | Request Access modal partial |
| `apps/web-marketing/partials/shell.css` | Shared stylesheet partial |
| `apps/web-marketing/partials/shell.js` | Shared script partial |
| `apps/web-marketing/api/` | Vercel serverless functions (marketing-side) |
| `apps/web-verifier/index.html` | Web Verifier UI source — **served by `api/verifier-page.js`, NOT placed in outputDirectory** |
| `apps/web-shared/` | Shared web resources |

### 8.2 Build-Time Injection

The build script (`scripts/build_public_web.js`) replaces five sentinel comments in source pages at build time:
- `<!-- SHELL_CSS -->` → content of `partials/shell.css`
- `<!-- HEADER -->` → content of `partials/header.html`
- `<!-- FOOTER -->` → content of `partials/footer.html`
- `<!-- MODAL -->` → content of `partials/modal.html`
- `<!-- SHELL_JS -->` → content of `partials/shell.js`

Source pages contain these sentinels. Generated output contains the injected content. **Source pages are source-of-truth. Generated output in `dist/public-web/` is not committed and must be regenerated.**

### 8.3 Generated Output

| Path | Status |
|---|---|
| `dist/public-web/` | Generated by `node scripts/build_public_web.js`. Not committed. Not version-controlled. |

### 8.4 Vercel Configuration

`vercel.json` at repo root. Key settings:
- `buildCommand`: `node scripts/build_public_web.js`
- `outputDirectory`: `dist/public-web`
- `cleanUrls`: true (strips `.html` from URLs)
- Rewrites: `/verifier` → `/api/verifier-page`; `/about` → `/about.html`; `/trust-assurance` → `/trust-assurance.html`; `/faq` → `/faq.html`; `/contact` → `/contact.html`; `/security-disclosure` → `/security-disclosure.html`; `/privacy-policy` → `/privacy-policy.html`; `/terms-of-service` → `/terms-of-service.html`

### 8.5 Vercel Serverless Functions

All in `api/`:

| File | Purpose |
|---|---|
| `api/request-access.js` | Handles access-request form submission; writes Blob record; sends Ethereal email |
| `api/verifier-page.js` | Serves Web Verifier HTML (gated by session validation) |
| `api/verifier-session.js` | Creates verifier sessions in Blob |
| `api/verifier-session-check.js` | Client-side defense-in-depth session check |
| `api/entitlement-store.js` | Validates entitlement tokens against Blob |
| `api/download.js` | Resolves platform, validates entitlement, redirects to Blob artifact URL |
| `api/preview-access-store.js` | Preview-access record management |

### 8.6 Access Control

The Web Verifier is gated behind a session cookie (`vb_session`). Anonymous users are redirected to the verifier-access page. The marketing site itself has no authentication gate in the committed source, but **DEPLOY-SEC-001 (Vercel Deployment Protection)** is intended to gate the entire domain. Current protection state is NOT ESTABLISHED.

---

## 9. Edge UI Architecture

### 9.1 Dashboard

| File | Purpose |
|---|---|
| `apps/web-dashboard/index.html` | Edge dashboard UI. Single HTML file. Served by FastAPI at `/`. Source-of-truth — committed. |

### 9.2 Edge API / Router

| File | Purpose |
|---|---|
| `edge/api/app.py` | FastAPI application. Routes: `/` (dashboard), `/verifier` (on `fix/mmp11-dist-mac-001`: 302 redirect to production; on `main`/`73a4523`: serves `apps/web-verifier/index.html`), `/offline-verifier` (on `fix/mmp11-dist-mac-001`: serves `apps/edge-offline-verifier/index.html`), `/about`, `/api/health`, `/api/receipts/verify`, `/api/cases/*`, `/schemas/*`, `/sample-receipt.json`, `/sample-receipt-tampered.json`, `/docs/*` |
| `main.py` | Entry point for PyInstaller and local dev launch |

**Important branch difference:** On `main` (`73a4523`), `/verifier` serves the Web Verifier HTML locally. That HTML (`apps/web-verifier/index.html`) calls `GET /api/verifier-session-check` on load — a Vercel-only serverless function that does not exist in the Edge API. This causes a 404 on the local Edge runtime. On `fix/mmp11-dist-mac-001` (`83d78db`), `/verifier` is replaced with a 302 redirect to `https://vaultbasis.com/verifier`, and a new `/offline-verifier` route serves `apps/edge-offline-verifier/index.html` (a fully offline receipt verifier).

### 9.3 Packaged Help / Resources

On `main` (`73a4523`): Help links point to `/faq`, `/contact`, `/security-disclosure` — local routes that do not exist in the Edge FastAPI app, causing 404s.  
On `fix/mmp11-dist-mac-001` (`83d78db`): Help links corrected to `https://vaultbasis.com/{faq,contact,security-disclosure}` with `↗` indicators.

### 9.4 Offline Verifier

| File | Purpose |
|---|---|
| `apps/edge-offline-verifier/index.html` | New file on `fix/mmp11-dist-mac-001` only. Self-contained offline receipt verifier. Calls local `/api/receipts/verify`. No external network dependencies (Google Fonts CDN dependency removed). |

**Note:** `apps/edge-offline-verifier/` does not exist on `main` or `release/mmp-1.1`. It exists only on `fix/mmp11-dist-mac-001`.

### 9.5 External Web Verifier Linkage

On `fix/mmp11-dist-mac-001` (`83d78db`): Dashboard presents two verifier options:
1. Offline Verifier (local `/offline-verifier`) — no network required
2. Independent Web Verifier ↗ (`https://vaultbasis.com/verifier`) — requires network and active session

### 9.6 PyInstaller Specs and Packaging Scripts

| File | Purpose |
|---|---|
| `VaultBasis-RC3-macOS.spec` | PyInstaller spec for macOS `.app` bundle. Target arch: `arm64`. Bundle ID: `com.vaultbasis.edge`. LSMinimumSystemVersion: 14.0. Bundles `apps/`, `schemas/`, `docs/scope_and_limitations_v0.1.md`, golden fixtures. |
| `scripts/build_rc3_macos.py` | Orchestrates macOS RC3 build: runs PyInstaller with the spec, then packages into ZIP using `zip -ry` to preserve symlinks. |
| `scripts/build_rc3_windows.py` | Orchestrates Windows RC3 build: onedir mode, Defender exclusion CI workaround. |
| `scripts/build_desktop_executable.py` | Generic desktop build script used by CI. |

No `VaultBasis-RC3-Windows.spec` was found in the working tree at handover time.

### 9.7 Navigation Contract Tests

| File | Purpose |
|---|---|
| `tests/quality/production_deployment/test_edge_navigation_contract.py` | Added on `fix/mmp11-dist-mac-001`. 11 tests covering: prohibited local hrefs absent from dashboard; required external hrefs present; `/verifier` 302 redirect; `/offline-verifier` 200; receipt verify endpoint pass/fail; negative control. |

---

## 10. Deterministic Kernel Protected Boundary

The following modules constitute the deterministic assurance kernel. **The UX handover does not authorize modification of these components.** Any change requires a separate directive, dedicated testing, and re-qualification of all affected golden vectors.

| Module / Path | Function |
|---|---|
| `edge/assurance/reconciliation_engine.py` | Deterministic reconciliation: applies declared rules to compare broker and tax-ledger records. 13 outcome states. No floating point. |
| `edge/connectors/form1099da_parser.py` | Form 1099-DA intake parser |
| `edge/connectors/koinly_parser.py` | Koinly CSV intake parser |
| `edge/connectors/vaultbasis_csv_parser.py` | VaultBasis CSV fallback parser |
| `edge/connectors/validator.py` | Intake dispatcher and validation |
| `edge/connectors/hasher.py` | Evidence hashing |
| `edge/receipts/canonicalizer.py` | Receipt payload canonicalization (exact string representation, no float) |
| `edge/receipts/signer.py` | Ed25519 receipt signing |
| `edge/receipts/keygen.py` | Installation keypair management |
| `edge/receipts/verifier.py` | Receipt signature and schema verification (local) |
| `edge/core/explanations.py` | Provenance and explanation text generation |
| `edge/storage/sqlite_store.py` | Local SQLite evidence and case storage |
| `apps/verifier/verify_receipt.py` | Outcome Receipt verification logic (schema, version, key fingerprint, signature) |
| `schemas/` | Evidence Contract schema (JSON Schema) |
| `schemas/canonical/case.py`, `transaction.py`, `preflight.py` | Canonical data models |
| `tests/fixtures/golden_receipt_valid.json` | Golden valid receipt fixture |
| `tests/fixtures/golden_receipt_tampered.json` | Golden tampered receipt fixture |
| `tests/fixtures/canonical_vectors_v0.1.json` | Canonicalization test vectors |

---

## 11. Validation Commands

All commands assume the repository root as the working directory and a Python 3.10+ environment with dependencies installed (`pip install -r requirements.txt` or equivalent).

### 11.1 Full Python Regression Suite

```bash
python -m pytest tests/unit/ tests/quality/ -q
```
Expected on `main` (`73a4523`): 205 passed, 1 skipped.

### 11.2 Canonical 11-Gate Validation

```bash
python scripts/run_validation_gates.py
```
Gates: GATE-01 (Python syntax), GATE-02 (JSON schema), GATE-03 through GATE-08 (unit and integration test suites), GATE-09 (offline verifier), GATE-10 (Vercel build), GATE-11 (language invariant).  
All 11 gates must be green before any release promotion.

### 11.3 Public Web Build

```bash
node scripts/build_public_web.js
```
Output: `dist/public-web/`. Node.js 20+ required. No npm dependencies needed beyond those in `package.json` (express, nodemailer, @vercel/blob — these are Vercel function dependencies, not build-time dependencies).

### 11.4 Public Web Navigation Tests (require prior build)

```bash
python -m pytest tests/quality/production_deployment/test_web_navigation_and_links.py -v
```
Requires `dist/public-web/` to exist (run build first). Also requires running Edge API (for route tests).

### 11.5 Edge Navigation Contract Tests

```bash
python -m pytest tests/quality/production_deployment/test_edge_navigation_contract.py -v
```
Available only on `fix/mmp11-dist-mac-001` and later. Not present on `main`.

### 11.6 Deploy Security Tests

```bash
python -m pytest tests/quality/production_deployment/test_deploy_sec_001_access_control.py -v
```

### 11.7 Mac Build and Package

```bash
python scripts/build_rc3_macos.py
```
Requires PyInstaller, Python 3.10, and macOS arm64. Produces `dist/VaultBasis.app` and inner ZIP. CI runs this in GitHub Actions on `macos-latest`.

### 11.8 Windows Build and Package

```bash
python scripts/build_rc3_windows.py
```
Requires PyInstaller and Windows x64 environment. CI runs this on `windows-latest`.

### 11.9 Recipient-Path Mac Qualification (human, not automated)

No automated command covers this. The human qualification card requires:
1. Download artifact ZIP from GitHub Actions (no developer tools)
2. Extract with Finder double-click or `unzip -X` (preserve modes)
3. Locate `VaultBasis.app` — right-click → Open (Gatekeeper bypass for unsigned preview)
4. Confirm dashboard loads at `http://localhost:PORT`
5. Create sample case, load evidence, run reconciliation
6. Generate Outcome Receipt
7. Open Offline Verifier at `/offline-verifier`, verify receipt → PASS
8. Verify tampered receipt → FAIL
9. Quit and relaunch — confirm persistence
10. Record ZIP SHA-256: `shasum -a 256 <inner-zip>`

---

## 12. Known Defects and Open Tasks

### 12.1 Release Blockers (P0)

| ID | Severity | Component | Defect | Evidence | State | Blocks |
|---|---|---|---|---|---|---|
| DEPLOY-SEC-001 | P0 | Vercel / Production | Anonymous access to vaultbasis.com is open — Vercel Deployment Protection not enforced | Identified during session audit | PENDING — USER ACTION (Vercel dashboard) | All associate/CPA access |
| EMAIL-001 | P0 | Access Request / Provisioning | Email delivery uses Ethereal SMTP sink — recipients do not receive provisioning emails | `api/request-access.js` line: `host: 'smtp.ethereal.email'` | IMPLEMENTED (Ethereal only) — NOT PRODUCTION EMAIL | Associate-001, CPA-001 |

### 12.2 Distribution Qualification (P1)

| ID | Severity | Component | Defect | Evidence | State | Blocks |
|---|---|---|---|---|---|---|
| MMP11-DIST-MAC-001 | P1 | Mac Distribution | `73a4523` artifact FAIL: 8 defects (nav 404s, logo, contrast, no offline verifier, CDN dependency) | Founder qualification session 2026-09-30 | REMEDIATED IN `83d78db` — RE-QUALIFICATION PENDING | Founder smoke, Associate-001 |
| MMP11-DIST-WIN-001 | P1 | Windows Distribution | No founder qualification attempted | No CI artifact confirmed | IMPLEMENTED — NOT QUALIFIED | Associate-001 |
| PROMOTE-001 | P1 | Distribution | Artifact promotion manifest (`rc3/current/manifest.json`) not present in Blob — download endpoint returns 503 | `api/download.js` manifest lookup | PENDING — requires `workflow_dispatch promote: true` after qualification | Distribution to any user |

### 12.3 Public Web (P1)

| ID | Severity | Component | Defect | Evidence | State | Blocks |
|---|---|---|---|---|---|---|
| MMP11-PRES-003 | P1 | Public Web / IA | Production vaultbasis.com shows old IA: Trust & Assurance nav, Resources nav, secondary homepage jump-nav, legacy footer | Founder screenshots 2026-09-30 | REJECTED — local candidate `586a83c` exists but not deployed, not founder-accepted | Associate-001, CPA-001 |
| WEB-QUAL-001 | P1 | Public Web | Route verification not completed against live production | Pending | PENDING | Associate-001 |
| WEB-A11Y-001 | P1 | Public Web | Human browser WCAG pass not completed | Pending | PENDING | Associate-001 |

### 12.4 Security (P1)

| ID | Severity | Component | Defect | Evidence | State | Blocks |
|---|---|---|---|---|---|---|
| SEC-002-PROD | P1 | Entitlement / Blob | Production entitlement smoke test not completed | Pending | PENDING | CPA-001 |
| SEC-003-PROD | P1 | Host Header | `PUBLIC_BASE_URL` not confirmed in Vercel env; adversarial host-header test not run | Pending | PENDING | CPA-001 |
| SEC-005 | P1 | Fixture Keys | `tests/fixtures/keys/installation_ed25519.key` in repository — scope, classification, history-rewrite decision not made | `tests/fixtures/keys/` | PENDING DECISION | CPA-001 |

### 12.5 Test Infrastructure (P2)

| ID | Severity | Component | Defect | Evidence | State | Blocks |
|---|---|---|---|---|---|---|
| MMP11-TEST-001 | P2 | Test Fixtures | Golden fixture `golden_receipt_valid.json` has description field `,200` instead of `$4,200` — signed payload cannot be corrected without new signing key | Fixture file | KNOWN DEFECT — deferred | Not an Associate gate |

### 12.6 Founder-Reported Production UX Defects (against vaultbasis.com as of 2026-09-30)

| Defect | Observed | Remediation |
|---|---|---|
| Primary nav shows "Trust & Assurance" | Founder browser, 2026-09-30 | Requires deploying `586a83c` (after founder acceptance) or equivalent |
| Primary nav shows "Resources" | Founder browser, 2026-09-30 | As above |
| Secondary jump-navigation strip on homepage | Founder browser, 2026-09-30 | As above |
| Footer is oversized / sitemap-like | Founder browser, 2026-09-30 | As above |
| "Back to Top" appears only at bottom (not persistent float) | Founder observation, 2026-09-30 | As above |
| Request Access modal evaluated on appearance only — workflow not qualified | Founder observation, 2026-09-30 | EMAIL-001 must be resolved; full provisioning flow must be qualified |
| Design-partner commercial journey incomplete | Founder observation, 2026-09-30 | Provisioning, entitlement, download path must all be production-qualified |

---

## 13. MMP Roadmap and Documentation

| Milestone | Document | Location | Status |
|---|---|---|---|
| MMP-1 | Master Tasks Ledger | `docs/master_tasks_ledger.md` | EXISTS |
| MMP-1.1 | Task Ledger | `docs/mmp11_task_ledger.md` | EXISTS |
| MMP-1.5 | Roadmap | NOT CREATED | — |
| MMP-2 | Evidence Ontology Research | `docs/roadmap/evidence-ontology-v0.1-research.md` | EXISTS (research only, not a task ledger) |
| MMP-2 | Task Ledger | NOT CREATED | — |
| MMP-2.1 | Roadmap / Task Ledger | NOT CREATED | — |
| MMP-2.5 | Roadmap / Task Ledger | NOT CREATED | — |
| MMP-3 | Roadmap / Task Ledger | NOT CREATED | — |

Additional existing documentation:

| Document | Path |
|---|---|
| Scope & Limitations | `docs/scope_and_limitations_v0.1.md` |
| Reconciliation Semantics | `docs/reconciliation-semantics-v0.1.md` |
| Edge Deployment Guide | `docs/edge_deployment_guide.md` |
| Independent Verifier Guide | `docs/verifier_guide.md` |
| Edge Quick Start | `docs/Edge_Quick_Start.md` |
| CPA Observation Sheet | `docs/CPA_Observation_Sheet.md` |
| Hybrid Deployment Architecture | `docs/hybrid_deployment_architecture.md` |
| Infrastructure & Deployment | `docs/infrastructure_and_deployment_guide.md` |
| Manual Validation Scenarios | `docs/manual_validation_scenarios.md` |
| Preview Gates Certification | `docs/preview_gates_certification.md` |
| Definition of Done | `docs/definition_of_done.md` |
| ADRs | `docs/adr/` |
| Audit | `docs/audit/` |

---

## 14. Secrets and External Services

**Values are not recorded here. Only names and configuration locations are listed.**

| Secret / Credential | Location / Mechanism | Purpose |
|---|---|---|
| `BLOB_READ_WRITE_TOKEN` | Vercel environment variable (project settings) | Vercel Blob private storage — read/write for preview-access records, session records, entitlement tokens, artifact manifest |
| `VAULTBASIS_SIGNING_SECRET` | Vercel environment variable (if used) | Additional signing if implemented; confirm in Vercel dashboard |
| `PUBLIC_BASE_URL` | Vercel environment variable | Base URL for provisioning email download links (e.g., `https://vaultbasis.com`). SEC-003: must be set and confirmed to prevent host-header injection in provisioning URLs. **NOT CONFIRMED AS SET.** |
| Ethereal SMTP credentials | Dynamically generated per request via `nodemailer.createTestAccount()` | UAT email sink only — not a stored secret |
| GitHub Actions secrets | Repository secrets in GitHub (Settings → Secrets) | CI artifact upload/download; any Blob promotion token |
| `tests/fixtures/keys/installation_ed25519.key` | Committed to repository | Test-only signing key for golden fixture generation. SEC-005: disposition decision pending. **Do not treat as production key.** |
| Vercel project ID / team | Vercel dashboard | Required for CLI deployment and artifact promotion |

**No secret values are recorded in this document.**

---

## 15. Final Integrity Check

### 15.1 Git Status (at handover)

```
On branch fix/mmp11-pres-003
Untracked files:
  .claude/

nothing added to commit but untracked files present
```

### 15.2 Git Log (last 15, all branches)

```
586a83c (HEAD -> fix/mmp11-pres-003) fix(mmp11-pres-003): converge practitioner IA — canonical nav, footer, vocabulary, Trust Center
73a4523 (origin/release/mmp-1.1, origin/main, origin/fix/mmp11-pres-003, release/mmp-1.1, main) fix(mmp11-pres-002): converge practitioner experience and restore validation-ready UI
8201553 fix(sec): remove verifier static file from outputDirectory — closes static-bypass gap
30eb014 fix(sec): soften XFF claim, add ACCESS-INV-001 removable boundary invariant
cde1b3b fix(sec): DEPLOY-SEC-001 final delta — revocation propagation, IP derivation, rate-limit bound
31cbe45 fix(sec): DEPLOY-SEC-001 pre-push corrections — separate trust objects, server-authoritative gate, rate limiting
d7db43e fix(sec): implement DEPLOY-SEC-001 capability access control for Web Verifier
3777462 fix(ci): fix ZIP broken-link false positive on javascript: pseudo-URLs; button for Request Access
3abbac1 fix(ci): fix cp1252 UnicodeEncodeError crashing Windows ZIP content gate
a534cd8 fix(ci): scan source HTML directly in language invariant — no prior build required
a5e2cc4 fix(mmp11-lang-001): add practitioner-language release invariant + fix 3 audit violations
05c69ee fix(mmp-1.1): practitioner-readiness final delta — language, Edge self-service, brand mark
ee08053 feat(mmp11): practitioner-readiness convergence — About, Trust & Assurance, FAQ; nav IA; ledger
034eb38 feat(mmp11-web-pres-001): practitioner/enterprise presentation stabilization
5dc4962 fix(ci): switch Windows RC3 build to --onedir and add Defender exclusion to unblock 2h+ CI hang
```

### 15.3 Branch SHA Matrix (final)

| Branch | SHA |
|---|---|
| `main` | `73a4523` |
| `release/mmp-1.1` | `73a4523` |
| `fix/mmp11-dist-mac-001` | `83d78db` (pushed to origin) |
| `fix/mmp11-pres-003` | `586a83c` (local only — NOT pushed to origin; origin points to `73a4523`) |
| `lab/mmp-2-ai` | `412a6db` |

### 15.4 Stashes

None.

### 15.5 Unpushed Commits

`fix/mmp11-pres-003` — 1 commit (`586a83c`) is local only and has not been pushed.  
All other active branches are in sync with origin.

### 15.6 Generated / Local Files

- `dist/public-web/` — generated, not committed. May reflect `586a83c` build from this session. Do not treat as authoritative.
- `.claude/` — agent memory system, untracked, not a build artifact, not to be committed.
- No other generated or temporary files.

### 15.7 Running Processes

- **PID 65956** — `VaultBasis.app` (App Translocation). Founder's own process from qualification session. **Not terminated by this handover.**
- **PID 74819** — `python3 -m http.server 7799`. Started by this session. **Terminated** during handover preparation.
- No other VaultBasis-related processes started by this session remain running.

### 15.8 Nothing Cleaned, Reset, or Rewritten

Consistent with the stop-work directive, no `git clean`, `git reset`, `git push --force`, branch deletion, or file deletion was performed during handover preparation except: termination of PID 74819 (the HTTP server this session started) and `git restore package.json package-lock.json` (reverting playwright contamination introduced during this session).

---

*End of handover document.*
