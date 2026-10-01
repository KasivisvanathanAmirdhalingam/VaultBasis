# VaultBasis engineering knowledge base

Current operational knowledge; update during every task under [the execution standard](task_execution_standard.md). Historical engineering evidence is retained separately from current qualification.

| Knowledge ID / task | Established knowledge | Evidence / consequence |
|---|---|---|
| KB-001 / MMP11-AUDIT-001 | Passing local tests or screenshots does not establish founder acceptance | [Evidence register](ux/evidence-register.md); only founder accepts exact deployed candidate |
| KB-002 / MMP11-AUDIT-001 | Production dialog focus escapes; unknown route serves Home/200 | [Experience map](ux/current-experience-map.md); remediate under MMP11-A11Y-001 and MMP11-NAV-404-001 |
| KB-003 / MMP11-AUDIT-001 | Request API test SMTP and credential/entitlement mismatch block a truthful end-to-end claim | [Traceability](audit/traceability-matrix.md); real or explicitly manual provisioning must be operationally qualified |
| KB-004 / MMP11-AUDIT-001 | Local Mac manifest is not the designated Edge candidate | [Evidence register](ux/evidence-register.md); qualify exact CI/recipient artifact separately per OS |
| KB-005 / VB-GOV-001 | Commit cannot contain its own final SHA | Implementation commit followed by task evidence commit; no repeated amend, fake SHA or per-task release tag |
| KB-006 / VB-GOV-001 | Planning-baseline acceptance does not mean FOUNDER_UX_ACCEPTED | [Current status](status.md); controlled implementation authorized, runtime qualification pending |
| KB-007 / VB-GOV-001 | Public marketing and protected product access have different access rules | [Promotion workflow](development_workflow.md); do not solve capability security by inventing a whole-domain requirement |

Add task-linked facts and troubleshooting as behavior changes. Do not store secrets, tokens, taxpayer data or unverified operational claims here.

## First implementation findings

- MMP11-CI-UX-001: use the gate runner’s Python interpreter for subprocess pytest; PATH selected Anaconda locally. Sandbox bytecode-cache failures are environment failures, not syntax failures; use a writable cache prefix.
- MMP11-A11Y-001: native dialog modality plus keyboard wrapping keeps focus within content; preserve the mobile menu when closing a dialog so the exact invoking control remains focusable.
- MMP11-NAV-404-001: a rendered 404 file does not by itself prove the deployed route returns HTTP 404. Test status and content at the actual Preview URL.
- MMP11-ACCESS-001: service success is not email delivery or a preview credential. Interim presentation states unconfirmed delivery; operational provisioning remains open.

- MMP11-NFR-001: Playwright WebKit is engine evidence; it cannot substitute for Safari/VoiceOver or an iPhone recipient check. Firefox and Chromium results likewise do not establish physical-device acceptance.

- MMP11-A11Y-001: pointer activation in WebKit may leave the invoking button unfocused. Pass the invoking element explicitly; modal keyboard traversal must also account for platform settings that skip buttons/links. The expanded tests exposed both behaviors.
