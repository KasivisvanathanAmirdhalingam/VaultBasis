# VaultBasis MMP-1.1 Task Ledger

> **Release**: MMP-1.1 — Practitioner-Ready Stabilization  
> **Directive**: VB-DIR-2026-09-30-MMP11-PRACTITIONER-READINESS-001 / MMP11-EXEC-009A  
> **Purpose**: Make the MMP-1 capability distributable, secure, professionally presented, institutionally credible and suitable for Associate and CPA/EA validation.  
> **MMP-1 base**: FROZEN (historical baseline, must not be rewritten)  
> **Last updated**: 2026-10-03

## State vocabulary
`PENDING` → `IMPLEMENTED` → `AUTOMATED_VALIDATION_PASS` → `READY_FOR_PHYSICAL_RECIPIENT_QUALIFICATION` → `DISTRIBUTION_QUALIFIED` → `ASSOCIATE_READY`

- **IMPLEMENTED**: code written and committed
- **AUTOMATED_VALIDATION_PASS**: CI green + automated 11 gates pass
- **READY_FOR_PHYSICAL_RECIPIENT_QUALIFICATION**: Code frozen, candidate ready for physical recipient machine testing
- **DISTRIBUTION_QUALIFIED**: Human confirmation on live physical recipient machines without developer intervention
- **ASSOCIATE_READY**: Candidate certified for Associate-001 distribution

---

## Track A — Distribution & Security (Release Blockers)

| Task ID | Description | State | Commit | Notes |
|---|---|---|---|---|
| MMP11-DIST-MAC-001 | Mac RC3 packaging: PyInstaller onedir, symlink preservation via `zip -ry`, recipient-style extraction via `unzip -X`, PRE/POST-ZIP launch gates | IMPLEMENTED | `3845219`, `4ec1a74` | Superseded by EXEC-009A |
| MMP11-DIST-WIN-001 | Windows RC3: switch `--onefile` → `--onedir`, hard timeout on communicate(), Defender exclusion in CI | IMPLEMENTED | `5dc4962` | Superseded by EXEC-009A |
| MMP11-DIST-WIN-003 | Windows Evidence Bundle Export UTF-8 encoding fix under `cp1252` host environment | CLOSED / QUALIFIED | `55eb501` | Closed; verified in CI Run 37190867994 and physical Windows smoke |
| MMP11-DIST-WIN-004 | Windows package bounded resource inclusion, hygiene gate, and evidence-export allowlist contract | CLOSED / QUALIFIED | `bd9b1e7` | CI Run 37197525586; candidate SHA `434957f1...`, export SHA `403de48c...`; 0 leaks, physical smoke PASS |
| MMP11-DIST-MAC-004 | macOS candidate repeatable build & Developer ID signing/notarization distribution qualification | PENDING | — | Functional manual pass verified (`9ec370c1...`); Developer ID signing/notarization pending |
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

## Track G — Recipient Runtime & Practitioner Journey Closure (MMP11-EXEC-009A)

| Task ID | Description | State | Commit | Notes |
|---|---|---|---|---|
| MMP11-DIST-WIN-002 | Windows Explorer runtime startup: stdio None fallback, `log_config=None`, hiddenimports, disconnected stdio CI launch gate | DISTRIBUTION_QUALIFIED | `55eb501` | 11/11 gates PASS; physical test PASS |
| MMP11-DIST-MAC-002 | Mac launcher browser auto-open: OS-authoritative `open <url>` launch on health confirmation | READY_FOR_PHYSICAL_RECIPIENT_QUALIFICATION | Current | 11/11 gates PASS; physical test pending |
| MMP11-UX-STORY-001 | Practitioner mental model: Client/Year Context, Source A (Broker) vs Source B (Tax Ledger), readiness layer, 4-stage workflow, sensitized results | READY_FOR_PHYSICAL_RECIPIENT_QUALIFICATION | Current | 11/11 gates PASS; physical test pending |
| MMP11-SAMPLE-001 | 1-Click zero-knowledge sample case onboarding (`POST /api/sample-case/load`) | DISTRIBUTION_QUALIFIED | Current | 11/11 gates PASS; physical test PASS on Windows & Mac |
| MMP11-VERIFY-UX-001 | GUI Offline Verifier practitioner journey; bundle restructuring for secondary technical tools | DISTRIBUTION_QUALIFIED | Current | 11/11 gates PASS; physical test PASS on Windows & Mac |
| MMP11-CASE-001 | Empty case persistence containment (`VB-CASE-INV-001`) + non-wrapping header streamline | AUTOMATED_VALIDATION_PASS | Current | In-memory draft wizard; persists only upon first valid evidence ingestion; 11/11 gates PASS |
| VB-REG-GAP-001 | Form 1099-DA / Basis Reconciliation Regulatory & Evidence Context Analysis | RESEARCH_DISPOSITION_RECORDED | Current | Triaged: 1.1 unknown-never-zero invariant verified; 1.5 Evidence Context scheduled; tax characterization claims rejected |
| VB-DOC-INV-001 | Canonical docs architecture: `case_model`, `domain_model`, `practitioner_journey`, `evidence_readiness`, `visual_semantics`, `MMP15-COMM-001`, `MMP15-PRACTICE-001` | VERIFIED | Current | Included in repo |
| MMP11-QUAL-PHYS-001 | Physical recipient qualification execution on Mac arm64 & Windows x64 | IN_PROGRESS | `bd9b1e7` | Windows x64 QUALIFIED; macOS arm64 functional manual pass confirmed |

---

## Track E — Associate & CPA Validation

| Task ID | Description | State | Commit | Notes |
|---|---|---|---|---|
| Associate-001A | Distribution canary: download → extract → launch → sample → receipt → verify → quit → relaunch → help | PENDING | — | Prerequisite: Physical recipient qualification PASS |
| Associate-001B | Zero-knowledge practitioner rehearsal: website → understand → access → download → use → verify → find support | PENDING | — | Gate: Associate-001A clear |
| CPA-001 | CPA/EA Design-Partner evaluation | PENDING | — | Gate: Associate-001B clear |

---

## Directives issued

| Directive ID | Summary | Date |
|---|---|---|
| VB-DIR-2026-09-30-MMP11-CONVERGENCE-001 | MMP-1.1 task ledger, state vocabulary, stop-patching rule | 2026-09-30 |
| VB-DIR-2026-09-30-MMP11-PRACTITIONER-READINESS-001 | MMP-1.1 scope definition, five categories, CPA-gate requirements | 2026-09-30 |
| VB-DIR-2026-09-30-PRACTITIONER-LANGUAGE-SELF-SERVICE-001 | Two vocabulary planes, language audit, FAQ structure, self-service target | 2026-09-30 |
| VB-DIR-2026-09-30-PRACTITIONER-READINESS-CONVERGENCE-001 | Consolidated run directive: About/Trust/FAQ + language + publication conditions | 2026-09-30 |
| MMP11-EXEC-009A | Recipient Runtime & Practitioner Journey Closure Directive | 2026-10-03 |
