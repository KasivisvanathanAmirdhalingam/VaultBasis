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
