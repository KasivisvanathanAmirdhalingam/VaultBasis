# VaultBasis MMP-1.1 active task ledger

Status: ACTIVE — controlled recovery authorized. [Planning baseline](ux/README.md) accepted by founder; UI acceptance is separate. [Execution standard](task_execution_standard.md) is mandatory without repeated requests. [Registry](task_registry.json) supplies full implementation SHAs and documentation dispositions.

Execution: MMP11-EXEC-001 — IN_PROGRESS; first batch `1d7cfe9217f6c67b915fc14890db42355b1cdf3c` and tests `8a04fa44f7a87ff21eee1949e3ea152b770bc0bc`. [First bounded batch](ux/implementation-batch-a.md); controlled implementation directive 06 applies.

## Current recovery tasks

| Task ID | Task | State | Implementation commit IDs | Acceptance / exit evidence |
|---|---|---|---|---|
| MMP11-AUDIT-001 | Preserve accepted takeover planning baseline | IMPLEMENTED | `95708fade15efe583e25c6f5257e4bebe285f864` | Planning acceptance and immutable evidence commit; not runtime qualification. |
| VB-GOV-001 | Establish automatic task/commit/documentation closeout | IMPLEMENTED | `dfc176f193cc4e3378bb88189aca35e364496f8d` | Unique IDs, real implementation SHAs, six documentation dispositions, checker and negative controls. |
| MMP11-GIT-001 | Establish verified bounded Web convergence branch | IMPLEMENTED | `1d7cfe9217f6c67b915fc14890db42355b1cdf3c` | Fresh refs compared; branch from release baseline; Edge remains independent. |
| MMP11-UX-001 | Deliver coherent MMP-1.1 practitioner experience | AUTHORIZED | None — not implementation-closed | Complete accepted blueprint and journeys; no kernel changes; one complete candidate review. |
| MMP11-UX-FOUNDATION-001 | Shared design tokens and application shell | IN_PROGRESS | `1d7cfe9217f6c67b915fc14890db42355b1cdf3c` | One header/footer, typography/spacing/controls/status/focus system and distinct local navigation. |
| MMP11-UX-PAGES-001 | Converge all public/reference/verifier surfaces | AUTHORIZED | None — not implementation-closed | Home, Trust, About, Contact, Privacy, Terms, Security, Scope, access/verifier and 404 follow canonical IA. |
| MMP11-NAV-404-001 | Return intentional unknown-route HTTP 404 | IMPLEMENTED | `1d7cfe9217f6c67b915fc14890db42355b1cdf3c` | Unknown path including negative control returns 404 and usable recovery on actual candidate. |
| MMP11-NAV-TOP-001 | Accessible persistent Back-to-Top | IMPLEMENTED | `1d7cfe9217f6c67b915fc14890db42355b1cdf3c` | Keyboard/focus, scroll threshold, mobile-safe placement and reduced motion verified. |
| MMP11-A11Y-001 | Dialog lifecycle and WCAG 2.2 AA qualification | IN_PROGRESS | `1d7cfe9217f6c67b915fc14890db42355b1cdf3c`, `8a04fa44f7a87ff21eee1949e3ea152b770bc0bc` | Focus enters/contained/restored to exact invoker; Escape; labels/errors/status; axe plus human keyboard/VoiceOver. |
| MMP11-ACCESS-001 | Truthful access and provisioning state machine | IN_PROGRESS | `1d7cfe9217f6c67b915fc14890db42355b1cdf3c` | Validation/submitting/accepted-pending-error match durable service state; real or explicit manual provisioning; separate credentials/entitlements. |
| MMP11-EDGE-AUDIT-001 | Audit exact packaged Edge and remediate experience | AUTHORIZED | None — not implementation-closed | Cases/sample/finding/receipt/offline valid+tampered/help/navigation/persistence/quit/relaunch on recipient artifact; independently qualified track. |
| MMP11-NFR-001 | Supported environments and runtime qualification | IN_PROGRESS | None — not implementation-closed | All NFR Q01–Q19 applicable evidence on exact candidate; no source-only substitution. |
| MMP11-JOURNEY-001 | Behavioral journeys and negative controls | IN_PROGRESS | `1d7cfe9217f6c67b915fc14890db42355b1cdf3c`, `8a04fa44f7a87ff21eee1949e3ea152b770bc0bc` | Full public/access/verifier/Edge journeys; dead-link/focus/404/offline negative controls demonstrably fail. |
| MMP11-CI-UX-001 | Exact-SHA CI for bounded recovery branches | IMPLEMENTED | `1d7cfe9217f6c67b915fc14890db42355b1cdf3c`, `8a04fa44f7a87ff21eee1949e3ea152b770bc0bc` | Preserve canonical gates and add UX/NFR coverage; retain exact SHA/run/artifact evidence; CI triggers cover intended branch/PR. |
| MMP11-VISUAL-001 | Maintain visual acceptance matrix | AUTHORIZED | None — not implementation-closed | Every captured surface mapped to desktop/mobile/functional/a11y/UX/action; gaps explicit; baseline is not design acceptance. |
| MMP11-PREPROD-001 | Deploy exact CI-green Web candidate to protected Preview | AUTHORIZED | None — not implementation-closed | Immutable URL/deployment identity/source/run/time recorded; no production-first deployment. |
| MMP11-FOUNDER-001 | Complete candidate founder review | PENDING | None — not implementation-closed | Founder reviews exact coherent deployed candidate after engineering qualification; only founder assigns acceptance. |
| MMP11-RELEASE-001 | Integrate qualified tracks and requalify release | PENDING | None — not implementation-closed | Controlled PR into release; new merge SHA CI and applicable runtime evidence; accepted main follows production verification. |
| MMP11-PROD-001 | Immutable promotion, rollback readiness and production smoke | PENDING | None — not implementation-closed | Recorded rollback identity; promote same qualified candidate; verify real URLs/access/downloaded bytes; no unexplained blockers. |

## Existing task identities retained

Prior ledger entries are preserved in the [historical snapshot](handover/MMP11_TASK_LEDGER_PRE_UX_001.md). The table below retains all IDs and source attribution; it does not promote old generic VERIFIED/QUALIFIED claims. See the registry for expanded commit identities and explicit gaps. Existing Associate/CPA and security/distribution work remains necessary; historical implementation claims require fresh candidate evidence.

| Task ID | Task | Recorded implementation SHA(s) | Current qualification |
|---|---|---|---|
| MMP11-DIST-MAC-001 | Mac RC3 packaging: PyInstaller onedir, symlink preservation via `zip -ry`, recipient-style extraction via `unzip -X`, PRE/POST-ZIP launch gates | `38452199cb49dc8871b50a27fd43d69d916e5258`, `4ec1a749b3b1f24aded9d1a53407ea83d2214654`, `5dc4962de00ca807050e689c1e49c5ca948879f2` | Not requalified; see historical record and current workflow |
| MMP11-DIST-WIN-001 | Windows RC3: switch `--onefile` → `--onedir`, hard timeout on communicate(), Defender exclusion in CI | `5dc4962de00ca807050e689c1e49c5ca948879f2` | Not requalified; see historical record and current workflow |
| MMP11-SEC-002 | Blob-backed expiring entitlement: token → `sha256(token).json`, 72h TTL, timing-safe comparison, artifact-hash binding, fail-closed | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| MMP11-SEC-003 | `PUBLIC_BASE_URL` env var for provisioning emails; adversarial host-header test | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| MMP11-SEC-004 | CORS origin restriction to canonical production hostname | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| MMP11-SEC-DEPLOY-001 | Restore Vercel Deployment Protection (anonymous access to vaultbasis.com was open) | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| MMP11-WEB-001 | P0/P1 regulatory audit fixes: copyright, claims, terminology, disclaimer | `e3e63b9f48b7c7d358df5f046a113038998c32ed` | Not requalified; see historical record and current workflow |
| MMP11-WEB-002 | Footer link corrections based on user feedback | `f6c6647f91fc750fb6fdc5f067ec7116dc7d4003` | Not requalified; see historical record and current workflow |
| MMP11-WEB-003 | Remove TecTixBase, engineering jargon, internal refs from all user-facing pages | `9e68178e3761dd38717c219de1c7f7cb4330a7b0` | Not requalified; see historical record and current workflow |
| MMP11-WEB-004 | WEB-QUAL-001 remediation batch: Ethereal removal, real support routes, verifier terminology, Tax Correctness row, standalone legal pages, sample receipt fix | `bb8e93a37cfb175be3e5d430a5ea45ccfc2236fb` | Not requalified; see historical record and current workflow |
| MMP11-WEB-005 | Fix GATE-08/09 regressions: update test assertions for renamed labels; revert golden fixture description to preserve Ed25519 signature | `a69fc8759b97fcbdd0f5e15d4b6de4df0431e423` | Not requalified; see historical record and current workflow |
| MMP11-WEB-006 | MMP11-WEB-PRES-001: SVG geometric brand mark, practitioner nav IA, trust strip, hero composition, footer restructure, verifier UX reorder | `034eb387f656b94eff53621bed8542d19801f9ce` | Not requalified; see historical record and current workflow |
| MMP11-WEB-007 | Practitioner-readiness convergence: About, Trust & Assurance, FAQ pages; nav updated; "Golden Test Vectors" → "Verification Test Receipts"; vercel.json + build script updated | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| MMP11-WEB-QUAL-001 | Route verification + absence of dev artifacts in production | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| MMP11-WEB-A11Y-001 | Human browser pass: keyboard, focus, contrast, zoom, mobile, 8 routes | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| MMP11-CI-001 | Record exact CI evidence for current HEAD: run ID, conclusion, GATE-01..11, artifact SHAs | `034eb387f656b94eff53621bed8542d19801f9ce` | Not requalified; see historical record and current workflow |
| MMP11-DIST-MAC-001-VERIFY | Inspect Mac CI result: PRE-ZIP, symlink, POST-ZIP, health, content gate, artifact SHA | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| MMP11-DIST-WIN-001-VERIFY | Windows full qualification: native launch, health, sample, receipt, verify, relaunch | `5dc4962de00ca807050e689c1e49c5ca948879f2` | Not requalified; see historical record and current workflow |
| MMP11-PROMOTE-001 | Promote exact qualified artifacts to private Blob storage via workflow_dispatch | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| MMP11-DEPLOY-001 | Deploy qualified web build to Vercel + verify production routes | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| MMP11-DEPLOY-VERIFY-001 | Post-deployment: verify actual document content (not just HTTP 200) for all 12 routes on both vaultbasis.com and www | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| MMP11-SEC-002-PROD | 10-step production entitlement smoke: synthetic data, separate from DEPLOY-SEC-001 | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| MMP11-SEC-003-PROD | PUBLIC_BASE_URL Vercel env confirmation + adversarial host-header test | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| MMP11-SMOKE-FOUNDER | Founder recipient-path smoke: exact production bytes, Finder extraction, launch, sample case, receipt, verify — no developer intervention | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| Associate-001A | Distribution canary: download → extract → launch → sample → receipt → verify → quit → relaunch → help | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| Associate-001B | Zero-knowledge practitioner rehearsal: website → understand → access → download → use → verify → find support | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| CPA-001 | CPA/EA Design-Partner evaluation | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| MMP11-SEC-005 | Fixture signing-key disposition: usage scope, classification, history-rewrite decision | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| MMP11-TEST-001 | Golden fixture defect: new test-only signing key, regenerate correctly-formed signed receipt | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |
| BRAND-001 | VaultBasis distinctive identity system: geometric mark concepts, trademark search, favicon/app-icon system | UNRESOLVED — no verified attribution | Not requalified; see historical record and current workflow |

## Completion rule

Every task requires a unique ID, implementation SHA(s), linked evidence and six documentation dispositions. Do not close with “pending commit” or generic PASS. Follow [development workflow](development_workflow.md) for source → CI → Preview → human/founder → release → production → main, with independent Edge qualification. No future roadmap features or protected kernel changes in this line.
