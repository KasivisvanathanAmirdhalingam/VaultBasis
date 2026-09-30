# VB-NFR-001 — Enterprise experience and runtime qualification

Status: **qualification contract, not certification**. Updated 2026-09-30. Related: [UX blueprint](ux/canonical-ux-blueprint.md), [audit and defects](ux/current-experience-map.md), [evidence register](ux/evidence-register.md).

MMP11-A11Y-001 targets WCAG 2.2 AA engineering evidence. Do not claim ADA compliance. UX-QUAL-INV-001 requires evidence at the actual user boundary; UX-NAV-INV-001 requires one intentional outcome per interactive element; EDGE-OFFLINE-INV-001 requires declared local/offline capabilities to work with external connectivity disabled.

Test IDs below are **planned qualification cases**, not existing automated test names or passes. Link exact runner cases and evidence as they are executed. Existing narrow evidence never closes a whole row. Each run records immutable candidate identity, URL/package hash, environment/version, timestamp, operator, expected/actual result, logs/screenshot or recording, and disposition.

| NFR / planned test ID | Web | Verifier | Edge | Automated evidence | Human evidence | Release blocker / current state |
|---|---|---|---|---|---|---|
| Q01 cross-browser | Yes | Yes | Embedded browser separately | Same complete journey across engines | Safari/Chrome/Edge/Firefox and real mobile | Yes; pending |
| Q02 responsive | Yes | Yes | Desktop/zoom; mobile only if declared | Overflow/clipping, visible actions at all widths | Hierarchy, keyboard/touch/zoom feel | Yes; 1440/390 public capture only, no page overflow observed |
| Q03 WCAG 2.2 AA | Yes | Yes | Yes | axe all routes/states, zero serious/critical; contrast | Manual criteria review incl. reflow/text spacing | Yes; unqualified; live modal focus defect |
| Q04 keyboard | Yes | Yes | Yes | Tab/order/dialog/navigation basics | Entire journey without pointer; no trap | Yes; D03 live failure |
| Q05 screen reader | Yes | Yes | Yes | Semantic checks only | VoiceOver + Safari macOS; additional platform as practical | Yes; pending |
| Q06 offline / dependencies | Graceful degradation | Hosted auth distinct from local receipt processing | Required for all declared local tasks | Deny external network; resource/request inventory | Launch/sample/receipt/verify/help disconnected | Yes; candidate unqualified |
| Q07 performance | Yes | Yes | Yes | CWV lab, resource weights, bounded-scale timing/memory | Perceived responsiveness and stable interaction | Threshold gate; proposed budgets below, pending |
| Q08 errors / loading / empty | Yes | Yes | Yes | Timeout, offline, 401/403/404/429/500/503; no duplicate actions | Recovery clarity; no invented data-safety claim | Yes; source and live defects open |
| Q09 navigation integrity | Yes | Yes | Yes | Every element/fragment/deep link/history/download; proper status | Label predicts destination; no context loss | Yes; public missing URL returns homepage 200 |
| Q10 security UX | Access | Sessions | Local/external distinction | Anonymous/valid/invalid/expired/revoked, wrong artifact; no static bypass | Fail-closed but comprehensible | Yes; anonymous redirect observed only |
| Q11 persistence | — | — | Required | Create, reopen, receipt, multiple cases, failure isolation | Quit/relaunch/unexpected close with synthetic workspace | Yes; current package pending |
| Q12 installation | Download | — | Mac/Windows separate | CI/package gates and inner hash | Recipient download/extract/security prompt/launch/quit/relaunch without terminal | Yes; package provenance unresolved |
| Q13 visual consistency | Yes | Yes | Yes | Regression after acceptance | Typography, density, shell/brand/status consistency | Yes for coherence; cosmetic refinements triaged |
| Q14 actual-boundary smoke | Production | Production | Downloaded exact package | URLs/aliases/access/binary hash and critical journeys | Real inbox/download and native path | Yes; full flow pending |
| Q15 privacy and content | Yes | Yes | Yes | No forbidden internal terms, sensitive logs, unexpected requests | Boundary comprehension; contact/access never invite taxpayer files | Yes; pending |
| Q16 scale and unsupported input | Upload as applicable | Receipt size/runtime | Declared source limits | Small/normal/near-limit/oversized and hostile inputs using frozen contracts | UI remains operable; useful progress/error | Yes; no limit expansion permitted |
| Q17 generated artifacts | Guides/downloads | Receipt explanation | Receipt/bundle/help | Names/links/packaging and machine-readable integrity | Human route to understand and retain artifacts | Yes; pending |
| Q18 provisioning / real delivery | Required | Credential readiness | Entitled platform distribution | Durable states, retry/idempotency, delivery failure, unavailable manifest | Actual inbox receipt and correct platform artifact | Yes; test SMTP and state mismatch block |
| Q19 console/network | Yes | Yes | Yes | No uncaught JS, unexplained errors, failed required resources, mixed content or sensitive logging | Review warnings, expected failures and dependency list | Yes; no console errors in limited public capture, not full pass |

## Supported-environment proposal

Web: current stable Chrome, Edge, Safari macOS and Firefox; Safari iPhone and Chrome Android. Record exact browser and OS/device versions at qualification; automation Chromium is not a substitute for actual stable Chrome/Edge or Safari. Viewports: 1920×1080, 1440×900, 1280×800, approximately 768 px tablet, 390 px mobile and 320 CSS px reflow. Test 200% zoom, text spacing, reduced motion, OS text scaling where practical, Retina/high DPI, keyboard, pointer and touch. Do not reorder meaning between widths.

Native: macOS 14+ / Apple Silicon as proposed package boundary; Windows x64 only after exact supported Windows versions and artifact identity are established. No Intel Mac claim. Native minimum window sizes must be declared from actual package behavior. No historical-browser, translation or dark-mode expansion in this phase.

## Required cases within the rows

- Q03–05: landmarks/headings/titles/language; skip link; names and labels; focus visibility/order/containment/restoration; Escape; error association; live status; text/non-text contrast; no keyboard traps; zoom/text spacing/reflow; target sizes; hover/focus equivalence; tables; accessible downloads; no duplicate IDs; mobile virtual keyboard.
- Q09: direct entry, reload, Back, Forward, deep anchor, new tab, external destination, expired/revoked-session revisit; inspect resulting screen, not just href presence. Verify actual 404 rather than homepage fallback.
- Q10: preview credential never substitutes for artifact entitlement; entitlement bound to actual selected artifact; wrong-platform/expired/revoked/invalid fail closed; protection enforced at server entrypoints and alternative static paths. Public information may remain public. Preserve best-effort rate-limit limitations; do not claim strict distributed throttling.
- Q11–12: clean recipient environment and synthetic workspace; normal and unexpected close; evidence and receipts retained as designed; case isolation; missing/unavailable artifact; unsupported OS; security prompt. Do not weaken platform security to claim easy installation.
- Q15/Q19: no tokens, taxpayer evidence, raw exceptions, engineering task IDs or build status in practitioner UI/logs. Technical reference context can intentionally identify a contract version. Inventory runtime external hosts; no analytics without authorization.

## Performance proposal

For candidate review: target LCP ≤2.5 s, CLS ≤0.1 and interaction latency ≤200 ms on declared representative devices/networks. These are proposed product budgets, not measured results or a field-CWV claim. Record cold-load lab conditions separately from any later field percentiles. First local working feedback should appear within 200 ms of action; do not invent engine progress. Establish bounded-case compute/memory baselines without changing engine limits. Review JS/font/image weight changes; no trivial-effect dependency. Threshold misses require an explicit disposition before release, not a silently green score.

## Negative controls

On an isolated test fixture/candidate, inject a dead footer URL, broken anchor, low contrast, missing dialog label, Edge Help `/faq` local URL and remote font in offline verifier. Q09/Q03/Q06 must fail respectively. Restore mutations before any build or capture. Never inject these into production or mutate frozen engine/vector expectations. Store failing and restored-run evidence.

## Evidence and promotion

Current [anonymous production observation](ux/evidence/2026-09-30/production-observations.json): Sept 30, Chromium 153.0.8010.12, desktop/mobile screenshots and one modal keyboard sequence. It establishes neither supported-browser qualification nor founder acceptance. Production build comment identifies `preview`, not a source SHA. Exact deployment attestation remains open.

Before founder review: one complete protected pre-production candidate, all blocking journeys/states exercised, screenshot matrix, keyboard/VoiceOver and native evidence. Required screenshots include Home, Trust, About, Contact, Access idle/working/success/error, access gate, verifier results/errors, 404 and Edge Cases/Sample/Case/Finding/Receipt/Offline Verifier/Help; desktop/mobile where applicable. Candidate identity accompanies every record.

Only the founder records acceptance of the actual deployed candidate. Promote that immutable candidate, then verify production URLs, access controls, email/download journey and downloaded artifact identity. Production smoke cannot be replaced by localhost screenshots. Associate work need not wait for nonblocking aesthetic refinement after bounded release gates close.
