# MMP11-NFR-001 — Automated browser-engine qualification

State: IN_PROGRESS. Complete NFR acceptance remains open.

The existing public-foundation suite now runs in Chromium, Firefox and WebKit on the same generated output. Each engine checks nine public pages at 1440, 1280, 768, 390 and 320 pixels; dialog focus/validation/working/error states; mobile navigation; real local 404 response; link/fragment crawl; axe checks; and four negative controls. CI installs all three engines and retains exact-SHA results.

The initial expanded run passed 36/39 and exposed three WebKit failures: forward Tab could leave the modal and pointer activation did not establish the correct return-focus target. MMP11-A11Y-001 now passes the explicit invoking element and traverses the visible enabled dialog controls in both directions. The focus assertion was strengthened to check the starting state before Tab as well: WebKit could otherwise re-enter a deliberately escaped non-modal dialog and conceal the negative control. No checks were skipped. Native dialog modality still keeps background content inert.

## Evidence boundaries

The original foundation passed GitHub run 36820918387 at `3ddbbf34d834d03d516e0a10bb68caf0af164a24`. That run does not qualify the expanded matrix or subsequent fix. Local rerun results and new implementation SHA are recorded at closeout.

These are Playwright browser-engine checks on generated local output, not branded Edge/Safari, physical iPhone/Android, VoiceOver, deployed routing, real provisioning, authenticated verifier or native distribution qualification. No founder or production acceptance is assigned.

## Documentation dispositions

| Category | Disposition |
|---|---|
| Technical | UPDATED: [technical register](../../../technical_change_register.md); explicit focus traversal and expanded workflow described here. |
| Knowledge base | UPDATED: [knowledge base](../../../knowledge_base.md); engine evidence and pointer-focus differences. |
| Status | UPDATED: [current status](../../../status.md), active ledger and task registry; complete NFR task remains in progress. |
| ADR | NO_CHANGE: reviewed ADR-003 and ADR-007; presentation/test coverage changes no assurance or authorization boundary. |
| Internal audit | UPDATED: this record, original CI evidence in batch-a-validation.json and the separate new run. |
| External audit | UPDATED: [local disclosure draft](../../external/README.md); bounded automated coverage only. |

Local follow-up validation: 39/39 browser tests passed (13 per engine), all 11 canonical gates passed, full Python regression 235 passed/1 skipped, SEC-002 27 passed and SEC-003 6 passed. Task traceability: 142 IDs, 0 errors. Protected-path diff against release: unchanged. The new exact-SHA CI run remains separate from these local results.

Browser-matrix/focus implementation commit: `ff360e5cafb450ba384c72a301347dac7010283b`. Local validation above applies to these changes; release qualification remains open.

Exact-SHA remote result: **AUTOMATED_VALIDATION_PASS** — [run 36822478917](https://github.com/KasivisvanathanAmirdhalingam/VaultBasis/actions/runs/36822478917), source `1bfaf377aab5b61c234e03d59fda78d1eb398e34`. All workflow steps succeeded, including the three-engine browser matrix. This observation does not qualify later runtime changes or assign Preview/human/founder/production acceptance. The following evidence-only commit records the result; the qualified source remains the SHA above.
