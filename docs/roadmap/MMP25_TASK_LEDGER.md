# MMP-2.5 — Firm Review Automation: task ledger

**Status: PROPOSED / NOT AUTHORIZED FOR IMPLEMENTATION.** Updated 2026-09-30. Priorities are provisional hypotheses to validate with practitioners, not promised release content.

See [roadmap](VAULTBASIS_PRODUCT_ROADMAP.md), [Git/evidence governance](../audit/git-and-evidence-governance.md) and [side-by-side audit ledger](../audit/traceability-matrix.md). No task has execution evidence or acceptance yet. Owners are unassigned; product and architecture must approve scope before implementation.

| Task | Feature | Current evidence | Next decision |
|---|---|---|---|
| MMP25-001 | Firm Queue and Maker/Reviewer Controls | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP25-002 | Evidence-request Workflow | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP25-003 | Change Impact and Reviewer Delta | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP25-004 | Operational Review Metrics | Founder roadmap proposal only | Practitioner priority + architecture scope |

## MMP25-001 — Firm Queue and Maker/Reviewer Controls

| Required field | Proposed contract |
|---|---|
| Task ID | MMP25-001 |
| MMP | MMP-2.5 |
| Problem | Route cases to preparer, reviewer and professional approver. |
| Practitioner Job-to-be-Done | As a practitioner, I need to route cases to preparer, reviewer and professional approver. |
| Feature | Firm Queue and Maker/Reviewer Controls |
| Expected Value | Focus attention on real review needs. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic workflow |
| Inputs | Authorized firm roles, case states and declared firm thresholds |
| Outputs | Review queues and attributable approvals |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Policy routes review without determining tax correctness; unsupported evidence requires declared review; no self-approval bypass where forbidden. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Role escalation, mistaken threshold authority, cross-client disclosure. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP25-002 — Evidence-request Workflow

| Required field | Proposed contract |
|---|---|
| Task ID | MMP25-002 |
| MMP | MMP-2.5 |
| Problem | Track request, approval, response, receipt and reevaluation. |
| Practitioner Job-to-be-Done | As a practitioner, I need to track request, approval, response, receipt and reevaluation. |
| Feature | Evidence-request Workflow |
| Expected Value | Reduce follow-up administration. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Hybrid workflow |
| Inputs | Actual unresolved evidence, approved draft/recipient, received evidence |
| Outputs | Attributable communication state and new deterministic reevaluation record |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Every external send is approved; arrival never silently resolves findings; new evidence passes supported validation. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. For AI: grounded/ungrounded and adversarial examples, model/prompt version, uncertainty and override evaluations. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Duplicate sends, incorrect recipient, false resolved state. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP25-003 — Change Impact and Reviewer Delta

| Required field | Proposed contract |
|---|---|
| Task ID | MMP25-003 |
| MMP | MMP-2.5 |
| Problem | Review what changed since the prior evidence review. |
| Practitioner Job-to-be-Done | As a practitioner, I need to review what changed since the prior evidence review. |
| Feature | Change Impact and Reviewer Delta |
| Expected Value | Avoid re-reviewing unchanged findings. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic workflow |
| Inputs | Versioned evidence and before/after authoritative findings |
| Outputs | Changed/new/resolved/unchanged classifications with provenance |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Delta counts reconcile to stable comparison rules; unchanged findings remain inspectable; historical signed records preserved. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Identity drift, false unchanged classification, comparing incompatible versions. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP25-004 — Operational Review Metrics

| Required field | Proposed contract |
|---|---|
| Task ID | MMP25-004 |
| MMP | MMP-2.5 |
| Problem | Understand case cycle time and evidence/review bottlenecks. |
| Practitioner Job-to-be-Done | As a practitioner, I need to understand case cycle time and evidence/review bottlenecks. |
| Feature | Operational Review Metrics |
| Expected Value | Improve firm operations. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic analysis |
| Inputs | Authorized workflow timestamps and defined operational events |
| Outputs | Cycle time, unresolved aging, turnaround and bottleneck measures |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Definitions/denominators and access boundaries are documented; no taxpayer behavioral analytics; no metrics collection before authorization. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Misleading productivity inference, surveillance, retention of unnecessary sensitive data. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |
