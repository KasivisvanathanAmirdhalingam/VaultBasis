# VaultBasis MMP-1.1 Task Ledger

> **Release**: MMP-1.1 — Practitioner-Ready Stabilization  
> **Directive**: VB-DIR-2026-09-30-MMP11-PRACTITIONER-READINESS-001  
> **Purpose**: Make the MMP-1 capability distributable, secure, professionally presented, institutionally credible and suitable for Associate and CPA/EA validation.  
> **MMP-1 base**: FROZEN (historical baseline, must not be rewritten)  
> **Last updated**: 2026-09-30

## State vocabulary
`PENDING` → `IN_PROGRESS` → `IMPLEMENTED` → `VERIFIED` → `QUALIFIED`

- **IMPLEMENTED**: code written and committed
- **VERIFIED**: CI green + automated checks pass
- **QUALIFIED**: human confirmation on live production surface

---

## Track A — Distribution & Security (Release Blockers)

| Task ID | Description | State | Commit | Notes |
|---|---|---|---|---|
| MMP11-DIST-MAC-001 | Mac RC3 packaging: PyInstaller onedir, symlink preservation via `zip -ry`, recipient-style extraction via `unzip -X`, PRE/POST-ZIP launch gates | IMPLEMENTED | `3845219`, `4ec1a74` | CI evidence for `5dc4962` run awaited — supersedes 4ec1a74 for qualification |
| MMP11-DIST-WIN-001 | Windows RC3: switch `--onefile` → `--onedir`, hard timeout on communicate(), Defender exclusion in CI | IMPLEMENTED | `5dc4962` | CI run in progress at time of ledger update; PRE/POST-ZIP qualification pending |
| MMP11-SEC-002 | Blob-backed expiring entitlement: token → `sha256(token).json`, 72h TTL, timing-safe comparison, artifact-hash binding, fail-closed | IMPLEMENTED | (prior session) | Production smoke test pending |
| MMP11-SEC-003 | `PUBLIC_BASE_URL` env var for provisioning emails; adversarial host-header test | IMPLEMENTED | (prior session) | Production confirmation pending |
| MMP11-SEC-004 | CORS origin restriction to canonical production hostname | IMPLEMENTED | (prior session) | Verified in code |
| MMP11-SEC-DEPLOY-001 | Restore Vercel Deployment Protection (anonymous access to vaultbasis.com was open) | PENDING | — | USER ACTION: requires Vercel dashboard; root cause suspected: Standard Protection scope |

---

## Track B — Web Presentation & Credibility (Practitioner Readiness)

| Task ID | Description | State | Commit | Notes |
|---|---|---|---|---|
| MMP11-WEB-001 | P0/P1 regulatory audit fixes: copyright, claims, terminology, disclaimer | VERIFIED | `e3e63b9` | CI green |
| MMP11-WEB-002 | Footer link corrections based on user feedback | VERIFIED | `f6c6647` | CI green |
| MMP11-WEB-003 | Remove TecTixBase, engineering jargon, internal refs from all user-facing pages | VERIFIED | `9e68178` | CI green |
| MMP11-WEB-004 | WEB-QUAL-001 remediation batch: Ethereal removal, real support routes, verifier terminology, Tax Correctness row, standalone legal pages, sample receipt fix | VERIFIED | `bb8e93a` | CI green |
| MMP11-WEB-005 | Fix GATE-08/09 regressions: update test assertions for renamed labels; revert golden fixture description to preserve Ed25519 signature | VERIFIED | `a69fc87` | CI green |
| MMP11-WEB-006 | MMP11-WEB-PRES-001: SVG geometric brand mark, practitioner nav IA, trust strip, hero composition, footer restructure, verifier UX reorder | IMPLEMENTED | `034eb38` | CI in queue |
| MMP11-WEB-007 | Practitioner-readiness convergence: About, Trust & Assurance, FAQ pages; nav updated; "Golden Test Vectors" → "Verification Test Receipts"; vercel.json + build script updated | IMPLEMENTED | (pending commit) | CI pending |
| MMP11-WEB-QUAL-001 | Route verification + absence of dev artifacts in production | PENDING | — | Requires live Vercel deployment verification |
| MMP11-WEB-A11Y-001 | Human browser pass: keyboard, focus, contrast, zoom, mobile, 8 routes | PENDING | — | Human action |

---

## Track C — Qualification & Publication

| Task ID | Description | State | Commit | Notes |
|---|---|---|---|---|
| MMP11-CI-001 | Record exact CI evidence for current HEAD: run ID, conclusion, GATE-01..11, artifact SHAs | PENDING | — | Evidence to be captured from GitHub Actions for `034eb38` / next run |
| MMP11-DIST-MAC-001-VERIFY | Inspect Mac CI result: PRE-ZIP, symlink, POST-ZIP, health, content gate, artifact SHA | PENDING | — | Evidence from current CI run |
| MMP11-DIST-WIN-001-VERIFY | Windows full qualification: native launch, health, sample, receipt, verify, relaunch | PENDING | — | Evidence from `5dc4962` CI run |
| MMP11-PROMOTE-001 | Promote exact qualified artifacts to private Blob storage via workflow_dispatch | PENDING | — | Prerequisite: complete CI green + DEPLOY-SEC-001 closed |
| MMP11-DEPLOY-001 | Deploy qualified web build to Vercel + verify production routes | PENDING | — | Conditional on promotion |
| MMP11-DEPLOY-VERIFY-001 | Post-deployment: verify actual document content (not just HTTP 200) for all 12 routes on both vaultbasis.com and www | PENDING | — | Includes anonymous-session verification of DEPLOY-SEC-001 |

---

## Track D — Smoke & Qualification

| Task ID | Description | State | Commit | Notes |
|---|---|---|---|---|
| MMP11-SEC-002-PROD | 10-step production entitlement smoke: synthetic data, separate from DEPLOY-SEC-001 | PENDING | — | Independent conclusion |
| MMP11-SEC-003-PROD | PUBLIC_BASE_URL Vercel env confirmation + adversarial host-header test | PENDING | — | Independent conclusion |
| MMP11-SMOKE-FOUNDER | Founder recipient-path smoke: exact production bytes, Finder extraction, launch, sample case, receipt, verify — no developer intervention | PENDING | — | Required before Associate-001 |

---

## Track E — Associate & CPA Validation

| Task ID | Description | State | Commit | Notes |
|---|---|---|---|---|
| Associate-001A | Distribution canary: download → extract → launch → sample → receipt → verify → quit → relaunch → help | PENDING | — | Gates: CI + DEPLOY-SEC-001 + DIST-MAC/WIN + SEC-002 + SEC-003 |
| Associate-001B | Zero-knowledge practitioner rehearsal: website → understand → access → download → use → verify → find support | PENDING | — | Gate: Associate-001A + MMP11-WEB-PRES-001 complete + all institutional links live |
| CPA-001 | CPA/EA Design-Partner evaluation | PENDING | — | Gates: Associate-001B clear + SEC-005 + factual Privacy/Terms + frozen SHA/URLs + DEPLOY-SEC-001 closed |

---

## Track F — Deferred (Not Associate Gates)

| Task ID | Description | State | Notes |
|---|---|---|---|
| MMP11-SEC-005 | Fixture signing-key disposition: usage scope, classification, history-rewrite decision | PENDING | Required before CPA-001, not Associate gate |
| MMP11-TEST-001 | Golden fixture defect: new test-only signing key, regenerate correctly-formed signed receipt | PENDING | After release blockers; description field currently `,200` instead of `$4,200` due to signed payload constraint |
| BRAND-001 | VaultBasis distinctive identity system: geometric mark concepts, trademark search, favicon/app-icon system | PENDING | Parallel to engineering; current SVG mark is working placeholder |

---

## Publication acceptance criteria (before Vercel deploy)

- [ ] Zero known P0 blockers
- [ ] Zero practitioner-blocking P1 blockers
- [ ] No dead institutional links (`/about`, `/trust-assurance`, `/faq`, `/contact`, `/security-disclosure`, `/privacy-policy`, `/terms-of-service`, `/docs/scope_and_limitations_v0.1.html`)
- [ ] No practitioner-visible internal release vocabulary (MMP, RC, PRD, BUILD_VERIFIED, UAT, GATE)
- [ ] Coherent Marketing/Verifier/Edge terminology
- [ ] Functional self-service help (FAQ, verifier guide)
- [ ] Material claims factually verified against codebase
- [ ] Complete CI green (all 11 gates)
- [ ] Exact candidate SHA-256 identities recorded
- [ ] Production route/content verification green
- [ ] Deployment protection independently verified (DEPLOY-SEC-001)

---

## Directives issued

| Directive ID | Summary | Date |
|---|---|---|
| VB-DIR-2026-09-30-MMP11-CONVERGENCE-001 | MMP-1.1 task ledger, state vocabulary, stop-patching rule | 2026-09-30 |
| VB-DIR-2026-09-30-MMP11-PRACTITIONER-READINESS-001 | MMP-1.1 scope definition, five categories, CPA-gate requirements | 2026-09-30 |
| VB-DIR-2026-09-30-PRACTITIONER-LANGUAGE-SELF-SERVICE-001 | Two vocabulary planes, language audit, FAQ structure, self-service target | 2026-09-30 |
| VB-DIR-2026-09-30-PRACTITIONER-READINESS-CONVERGENCE-001 | Consolidated run directive: About/Trust/FAQ + language + publication conditions | 2026-09-30 |
