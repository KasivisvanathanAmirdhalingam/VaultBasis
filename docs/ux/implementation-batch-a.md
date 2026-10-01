# MMP11-EXEC-001 — First bounded implementation batch

Date: 2026-10-01. Branch: `fix/mmp11-ux-001`. State: implementation and local automated evidence only; no deployed UX acceptance.

## Branch evidence

Fetched remote refs before changes; main/release remained `73a4523c82c91cedaba414af3fbce5d6b200bf52`, Edge `83d78dbc7b2643e520fc72d288ebeb629a94ed58`, remote PRES-003 `73a4523c82c91cedaba414af3fbce5d6b200bf52`, lab `412a6db00b43f251b39e5ae1e09e57b7d79c08b9`.

Pushed `docs/engineering-handover-2026-09-30` to `origin` at `defaf5af0ee9db12c3e15aac7404ab043a5b7227`, containing the original accepted audit `95708fa` and governance `dfc176f` plus SHA closeout. Traceability validator passed and five governance negative controls were already evidenced. No deployment command, main/release merge or promotion was performed.

Created Web branch from `origin/release/mmp-1.1`; cherry-picked only the three named documentation/governance commits. Resulting identities: `da6d8fd449972ea4673842a3a517ea44d8c81301`, `770521473f99f094c7d1aee7500b86bdec081fc3`, `c1f3a925c3079a1700ee3dde34de1b48d3b1cc09`. Restored the linked historical handover document from the documentation branch. Original commit references remain provenance references; they do not imply cherry-picks have identical SHA. Rejected `586a83c`, Edge changes and lab work were not imported.

## Implemented changes and task boundaries

| Task | Change | Remaining scope |
|---|---|---|
| MMP11-GIT-001 | Verified refs, pushed governance baseline and isolated Web branch | Future remote changes checked before integration |
| MMP11-NAV-404-001 | Shared-shell 404 source; explicit last unmatched-route rewrite to server function that returns status 404, including safe missing-artifact fallback | Exact Vercel Preview routing qualification; production not changed |
| MMP11-UX-FOUNDATION-001 | Canonical public header/footer, Trust Center label, removed homepage pseudo-header, skip link, visible focus and shared form/dialog styles | Full page narrative/design convergence; Scope and authenticated verifier shell integration; no approved visual baseline yet |
| MMP11-NAV-TOP-001 | Floating scroll-threshold top button; reduced-motion support and focus to main | Supported-browser and human confirmation |
| MMP11-A11Y-001 | Native modal plus explicit keyboard wrap, exact invoker restoration, Escape/close, associated field errors, live status, mobile close behavior; low-contrast small labels corrected | Full WCAG/human/VoiceOver and cross-browser qualification remains open |
| MMP11-ACCESS-001 | Validated form and protected pending UI; recoverable errors; honest unconfirmed-delivery response; closed dialog retains in-flight state | Legacy service still uses test SMTP; no complete provisioning, preview-credential or download workflow claim |
| MMP11-JOURNEY-001 | Generated-page/fragment crawl, 404, modal, mock response states, mobile navigation, reflow and axe tests with negative controls | Authenticated verifier, real delivery, native Edge and full environment/state matrix |
| MMP11-CI-UX-001 | Dedicated branch/PR workflow, full-depth history, task validator, protected-path diff, existing 11 gates/Python/security and Chromium browser evidence | Exact remote run identity/result must be observed separately |

## Technical details and deliberate limits

`api/not-found.js` reads the built public 404 page; `vercel.json` includes that artifact in the function bundle and adds a final catch-all after existing routes. Existing `/verifier` server authority and download entitlement handlers are unchanged. The local Express harness serves clean HTML URLs and uses the real 404 handler, but it is not a Vercel runtime emulator. Vercel's documented [custom static 404 behavior](https://vercel.com/kb/guide/custom-404-page) and [rewrite configuration](https://vercel.com/docs/routing/rewrites) inform this design; Preview must verify actual precedence and included files.

The local harness deliberately returns 503 for provisioning. Browser tests intercept responses; no request is sent to a practitioner, and no credential or entitlement is minted. A legacy API 200 is accepted only with its expected JSON success state, and the UI explicitly says delivery is unconfirmed. Operational manual/automated provisioning remains its own task.

The frozen v0.1 body font and primary color remain; shared form/error/focus styling adds presentation roles around them. Small accent-colored labels use the existing darker primary-hover color to satisfy measured contrast. Frozen design tokens, all protected assurance modules, browser verification algorithm, schemas, Golden Corpus and vectors remain unchanged.

The canonical runner now invokes pytest with `sys.executable -m pytest`; PATH previously chose a different Anaconda interpreter and stalled locally. On the sandboxed Mac, use `PYTHONPYCACHEPREFIX=/private/tmp/vb-pycache` to avoid a denied system-cache write. These are validation-environment fixes, not relaxed assertions. Existing obsolete web label/footer/anchor-presence assertions were updated to the accepted navigation contract; protected tests were not changed.

## Evidence and remaining qualification

See [batch validation](../audit/internal/tasks/batch-a-validation.json), [registry](../task_registry.json), and task closeouts. Local suite: full Python regression, 11 canonical gates, SEC-002/003 JS checks, Chromium at 1440/1280/768/390/320, axe serious/critical threshold, generated-link/fragment crawl and negative controls. Four negative controls cover Home/200, dead link, non-modal focus escape and missing dialog name. Local visual inspection covered Home desktop/mobile and mobile dialog; it is not founder acceptance.

No Firefox/Edge/Safari/iPhone/Android, VoiceOver, authenticated live verifier, real provisioning, native package or production qualification is implied. CI cannot assign founder acceptance. No request for piecemeal founder review is made.

Next order remains Batch C full page convergence and access-service completion, followed by authenticated verifier and complete candidate qualification; Edge Mac/Windows remain independent. Do not deploy this partial batch for founder acceptance.

Implementation identities: `1d7cfe9217f6c67b915fc14890db42355b1cdf3c` (public foundation) and `8a04fa44f7a87ff21eee1949e3ea152b770bc0bc` (browser/CI gates). Follow-up evidence commit records these real SHAs without changing runtime code.
