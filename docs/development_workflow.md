# Authoritative MMP-1.1 development and promotion workflow

Task: VB-GOV-001. [Founder directive](handover/directives/05-branch-ci-promotion.txt) controls. This document supersedes abbreviated historical promotion instructions; [execution standard](task_execution_standard.md) applies at every step.

| Step / task | Work boundary | Required evidence / next state |
|---|---|---|
| Preserve planning / MMP11-AUDIT-001 | Documentation branch | Accepted audit at `95708fade15efe583e25c6f5257e4bebe285f864`; acceptance is planning only |
| Verify refs / MMP11-GIT-001 | Fetch remote; compare with snapshot before branch changes | Record discrepancies before altering branches; start new Web branch from verified release baseline |
| Web implementation / MMP11-UX-001 | `fix/mmp11-ux-001`; experience plane only | Bounded task-ID commits, synchronized docs, full SHA closeout; no work on main or rejected PRES-003 |
| Local gates / MMP11-JOURNEY-001 | Source and generated output | Shared shell, correct routes/404/dialog/top control, browser/keyboard/a11y, negative controls, regressions, protected tests unchanged; clean understood working tree |
| Exact-SHA CI / MMP11-CI-UX-001 | Pushed bounded branch | Canonical gates plus UX/a11y/navigation/security/generated-output/offline checks and retained evidence. Current CI source is main-oriented; configure branch coverage as a separate implementation task. State AUTOMATED_VALIDATION_PASS only for exact CI result. |
| Preview / MMP11-PREPROD-001 | Protected immutable Vercel Preview, not production alias | Source SHA, CI run/database ID, deployment ID, immutable URL, timestamp/environment → PREPROD_DEPLOYED |
| Candidate qualification / MMP11-NFR-001 | Exact Preview URL | Browser/device matrix, all routes/states, real 404, access/auth/receipt journeys, NFR and human keyboard/VoiceOver evidence; complete screenshots with known limits |
| Founder / MMP11-FOUNDER-001 | Complete candidate only | Engineering may say READY_FOR_FOUNDER_REVIEW. Only founder issues FOUNDER_UX_ACCEPTED. PREPROD_QUALIFIED is withheld until applicable human gates including founder acceptance are recorded. |
| Edge / MMP11-EDGE-AUDIT-001 and native tasks | Independently qualify `fix/mmp11-dist-mac-001`; Windows separate | CI → native package → inspection → recipient extraction → launch/sample/finding/receipt/offline valid+tampered/help/quit/relaunch/persistence → inner hash → controlled download and repeat smoke. No terminal repair. DISTRIBUTION_QUALIFIED per OS only. |
| Integrate / MMP11-RELEASE-001 | Controlled PR into `release/mmp-1.1` after both tracks qualify | Resulting merge SHA gets new CI and applicable full release/runtime qualification. Earlier branch acceptance does not transfer automatically. |
| Promote / MMP11-PROD-001 | Exact qualified immutable candidate | Record rollback deployment/alias and candidate identity first. No rebuild substituted. PRODUCTION_PROMOTED ≠ verified. |
| Production smoke / MMP11-PROD-001 | Real user URL and actual downloaded bytes | Routes/access/security/404/real provisioning/downloads, exact artifact hash and critical journeys → PRODUCTION_VERIFIED. P0: stop, restore recorded known-good alias, record failure, fix off production. |
| Accepted main / MMP11-RELEASE-001 | Controlled integration after production verification | Record main integration identity; any new runtime candidate requires requalification. Qualified release tag only after applicable evidence. |
| Practitioner / Associate-001A, Associate-001B, CPA-001 | Uninformed external-user evidence | Associate → bounded remediation → Associate qualification → CPA evaluation; future priority follows evidence |

No force push/history rewrite, speculative cleanup merge, whole rejected-branch resurrection, kernel change or future feature contamination. Do not merge Web and Edge prematurely. Real provisioning can be explicitly manual during preview only if the interface truthfully describes the process and actual recipient communication/download is qualified. Preview credentials remain distinct from artifact entitlements.

The supplied briefing uses PREPROD_QUALIFIED in more than one position relative to founder review. This procedure applies its stricter Preview Definition of Done: READY_FOR_FOUNDER_REVIEW follows engineering evidence; PREPROD_QUALIFIED follows the recorded founder decision. This resolves terminology without assigning acceptance on the founder's behalf.

Failure states: BLOCKED, FAILED, REJECTED, SUPERSEDED, scoped to a task/candidate. Historical generic PASS/DONE is not a current qualification state. Main is accepted integrated truth, not the discovery environment for release failures.
