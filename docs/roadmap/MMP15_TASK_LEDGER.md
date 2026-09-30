# MMP-1.5 — Practice Workflow Foundation: task ledger

**Status: PROPOSED / NOT AUTHORIZED FOR IMPLEMENTATION.** Updated 2026-09-30. Priorities are provisional hypotheses to validate with practitioners, not promised release content.

See [roadmap](VAULTBASIS_PRODUCT_ROADMAP.md), [Git/evidence governance](../audit/git-and-evidence-governance.md) and [side-by-side audit ledger](../audit/traceability-matrix.md). No task has execution evidence or acceptance yet. Owners are unassigned; product and architecture must approve scope before implementation.

| Task | Feature | Current evidence | Next decision |
|---|---|---|---|
| MMP15-001 | Evidence Inbox | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP15-002 | Case Readiness and Evidence Request List | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP15-003 | Review Queue | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP15-004 | Finding Lifecycle and Practitioner Notes | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP15-005 | Workpaper Evidence Bundle | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP15-006 | Multi-case Workspace | Founder roadmap proposal only | Practitioner priority + architecture scope |

## MMP15-001 — Evidence Inbox

| Required field | Proposed contract |
|---|---|
| Task ID | MMP15-001 |
| MMP | MMP-1.5 |
| Problem | Identify which case evidence is usable and what still needs attention. |
| Practitioner Job-to-be-Done | As a practitioner, I need to identify which case evidence is usable and what still needs attention. |
| Feature | Evidence Inbox |
| Expected Value | Reduce manual evidence sorting. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic workflow |
| Inputs | Case evidence, supported profiles, immutable source identities |
| Outputs | RECEIVED / SUPPORTED / UNSUPPORTED / DUPLICATE / MISSING / REQUIRES REVIEW workflow states |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Unsupported evidence remains visible; duplicate classification has an explicit rule and never silently deletes historical evidence. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Workflow state may be mistaken for assurance outcome; unsupported evidence needs safe handling. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP15-002 — Case Readiness and Evidence Request List

| Required field | Proposed contract |
|---|---|
| Task ID | MMP15-002 |
| MMP | MMP-1.5 |
| Problem | Understand what prevents review and request the missing evidence. |
| Practitioner Job-to-be-Done | As a practitioner, I need to understand what prevents review and request the missing evidence. |
| Feature | Case Readiness and Evidence Request List |
| Expected Value | Reduce preparation uncertainty and repeated client requests. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic workflow |
| Inputs | Evidence inventory, declared requirements, authoritative unresolved reasons |
| Outputs | Readiness reasons and structured evidence request list |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Every blocker/request traces to actual inventory or declared requirements; readiness never asserts tax correctness; no automatic send. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Readiness rules may overstate completeness or imply legal sufficiency. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP15-003 — Review Queue

| Required field | Proposed contract |
|---|---|
| Task ID | MMP15-003 |
| MMP | MMP-1.5 |
| Problem | Focus attention on differences, unresolved and unsupported evidence. |
| Practitioner Job-to-be-Done | As a practitioner, I need to focus attention on differences, unresolved and unsupported evidence. |
| Feature | Review Queue |
| Expected Value | Reduce unnecessary record inspection. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic workflow |
| Inputs | Authoritative findings and supported filtering criteria |
| Outputs | Ordered/filterable review items and reconciled counts |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Counts reconcile to defined categories without hidden double counting; agreements and excluded items remain inspectable. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Overlapping categories and ranking may hide important evidence. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP15-004 — Finding Lifecycle and Practitioner Notes

| Required field | Proposed contract |
|---|---|
| Task ID | MMP15-004 |
| MMP | MMP-1.5 |
| Problem | Track professional review without overwriting machine findings. |
| Practitioner Job-to-be-Done | As a practitioner, I need to track professional review without overwriting machine findings. |
| Feature | Finding Lifecycle and Practitioner Notes |
| Expected Value | Make review handoffs and unresolved work visible. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic workflow |
| Inputs | Finding identities, annotations, authorized human actions |
| Outputs | Separate OPEN / REVIEWED / EVIDENCE REQUESTED / EVIDENCE RECEIVED / RESOLVED / PROFESSIONAL REVIEW history |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Workflow resolution never changes historical machine state; reevaluation creates traceable new machine evidence; notes are attributable. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | A workflow RESOLVED label may be confused with deterministic resolution. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP15-005 — Workpaper Evidence Bundle

| Required field | Proposed contract |
|---|---|
| Task ID | MMP15-005 |
| MMP | MMP-1.5 |
| Problem | Retain a complete human-readable record of case review. |
| Practitioner Job-to-be-Done | As a practitioner, I need to retain a complete human-readable record of case review. |
| Feature | Workpaper Evidence Bundle |
| Expected Value | Reduce manual workpaper assembly. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic export |
| Inputs | Case summary, manifest, findings, unresolved evidence, notes, provenance, receipt |
| Outputs | Versioned workpaper bundle and verification instructions |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | All included facts trace to their origin; notes are distinguishable from machine facts; signed receipt bytes remain unchanged. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Sensitive data disclosure; mismatch between export and signed history. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP15-006 — Multi-case Workspace

| Required field | Proposed contract |
|---|---|
| Task ID | MMP15-006 |
| MMP | MMP-1.5 |
| Problem | Find the right client/case and its review readiness. |
| Practitioner Job-to-be-Done | As a practitioner, I need to find the right client/case and its review readiness. |
| Feature | Multi-case Workspace |
| Expected Value | Reduce context switching while preserving case isolation. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic workflow |
| Inputs | Authorized cases, readiness and review summaries |
| Outputs | Case workspace with traceable counts and links |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Opening a case cannot show another case’s findings/receipt; readiness displays blockers rather than unsupported certainty. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Cross-case privacy leakage; dashboard may precede higher-value practitioner needs. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |
