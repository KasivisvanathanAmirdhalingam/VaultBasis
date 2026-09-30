# MMP-2 — Evidence Intelligence: task ledger

**Status: PROPOSED / NOT AUTHORIZED FOR IMPLEMENTATION.** Updated 2026-09-30. Priorities are provisional hypotheses to validate with practitioners, not promised release content.

See [roadmap](VAULTBASIS_PRODUCT_ROADMAP.md), [Git/evidence governance](../audit/git-and-evidence-governance.md) and [side-by-side audit ledger](../audit/traceability-matrix.md). No task has execution evidence or acceptance yet. Owners are unassigned; product and architecture must approve scope before implementation.

| Task | Feature | Current evidence | Next decision |
|---|---|---|---|
| MMP2-001 | Evidence Classification | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP2-002 | Evidence Extraction | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP2-003 | Schema Mapping | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP2-004 | Evidence Gap Assistant | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP2-005 | Finding Explanation Assistant | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP2-006 | Evidence-request Drafting | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP2-007 | Case Summary and Conflict Discovery | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP2-008 | Case Q&A | Founder roadmap proposal only | Practitioner priority + architecture scope |

## MMP2-001 — Evidence Classification

| Required field | Proposed contract |
|---|---|
| Task ID | MMP2-001 |
| MMP | MMP-2 |
| Problem | Sort mixed evidence while retaining uncertainty. |
| Practitioner Job-to-be-Done | As a practitioner, I need to sort mixed evidence while retaining uncertainty. |
| Feature | Evidence Classification |
| Expected Value | Reduce initial sorting toil. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | AI proposal + deterministic validation |
| Inputs | Authorized documents and approved category definitions |
| Outputs | Suggested categories with provenance and uncertainty |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. VB-AI-INV-001 applies; human-confirmed candidates still pass supported deterministic validation. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. MMP-1.5 structured workflow or an explicitly approved bounded equivalent; isolated lab evaluation first. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Incorrect/unsupported/ambiguous classifications remain reviewable; model cannot silently authorize processing. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. For AI: grounded/ungrounded and adversarial examples, model/prompt version, uncertainty and override evaluations. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Prompt injection, sensitive-data egress, overconfident classification. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP2-002 — Evidence Extraction

| Required field | Proposed contract |
|---|---|
| Task ID | MMP2-002 |
| MMP | MMP-2 |
| Problem | Read documents into reviewable candidate values. |
| Practitioner Job-to-be-Done | As a practitioner, I need to read documents into reviewable candidate values. |
| Feature | Evidence Extraction |
| Expected Value | Reduce manual transcription. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Hybrid |
| Inputs | Authorized document pages and declared target fields |
| Outputs | Candidate values with exact page/span provenance |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. VB-AI-INV-001 applies; human-confirmed candidates still pass supported deterministic validation. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. MMP-1.5 structured workflow or an explicitly approved bounded equivalent; isolated lab evaluation first. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Every proposed value locates its source; absent/ambiguous values remain unknown; confirmed data still meets supported validation. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. For AI: grounded/ungrounded and adversarial examples, model/prompt version, uncertainty and override evaluations. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Hallucinated values, OCR errors, lost units or source attribution. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP2-003 — Schema Mapping

| Required field | Proposed contract |
|---|---|
| Task ID | MMP2-003 |
| MMP | MMP-2 |
| Problem | Map unfamiliar column labels without guessing their meaning. |
| Practitioner Job-to-be-Done | As a practitioner, I need to map unfamiliar column labels without guessing their meaning. |
| Feature | Schema Mapping |
| Expected Value | Reduce repeated format preparation. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Hybrid |
| Inputs | Unknown CSV headers, representative authorized rows, canonical field definitions |
| Outputs | Proposed mapping plus human-confirmed versioned deterministic mapping |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. VB-AI-INV-001 applies; human-confirmed candidates still pass supported deterministic validation. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. MMP-1.5 structured workflow or an explicitly approved bounded equivalent; isolated lab evaluation first. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | No ingestion under an unconfirmed mapping; ambiguous proceeds/basis/date/unit fields require review; no silent parser expansion. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. For AI: grounded/ungrounded and adversarial examples, model/prompt version, uncertainty and override evaluations. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Semantic drift and mistaken confirmation. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP2-004 — Evidence Gap Assistant

| Required field | Proposed contract |
|---|---|
| Task ID | MMP2-004 |
| MMP | MMP-2 |
| Problem | Explain what is unresolved and which evidence could help. |
| Practitioner Job-to-be-Done | As a practitioner, I need to explain what is unresolved and which evidence could help. |
| Feature | Evidence Gap Assistant |
| Expected Value | Make evidence collection more actionable. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Hybrid |
| Inputs | Actual unresolved reasons, scope and provenance |
| Outputs | Grounded explanation and suggested evidence request |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. VB-AI-INV-001 applies; human-confirmed candidates still pass supported deterministic validation. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. MMP-1.5 structured workflow or an explicitly approved bounded equivalent; isolated lab evaluation first. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Recommendations cite real unresolved items and never invent missing evidence or decide tax correctness. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. For AI: grounded/ungrounded and adversarial examples, model/prompt version, uncertainty and override evaluations. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Advice may drift into legal conclusions or request unnecessary sensitive data. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP2-005 — Finding Explanation Assistant

| Required field | Proposed contract |
|---|---|
| Task ID | MMP2-005 |
| MMP | MMP-2 |
| Problem | Understand deterministic findings in practitioner language. |
| Practitioner Job-to-be-Done | As a practitioner, I need to understand deterministic findings in practitioner language. |
| Feature | Finding Explanation Assistant |
| Expected Value | Reduce explanation effort. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Hybrid |
| Inputs | Frozen finding state, compared values and provenance |
| Outputs | Labeled AI explanation beside authoritative finding |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. VB-AI-INV-001 applies; human-confirmed candidates still pass supported deterministic validation. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. MMP-1.5 structured workflow or an explicitly approved bounded equivalent; isolated lab evaluation first. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Explanation cannot alter numbers/state or hide uncertainty; unsupported explanations are rejected or visibly unavailable. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. For AI: grounded/ungrounded and adversarial examples, model/prompt version, uncertainty and override evaluations. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Fluent but misleading explanations; loss of exact decimal meaning. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP2-006 — Evidence-request Drafting

| Required field | Proposed contract |
|---|---|
| Task ID | MMP2-006 |
| MMP | MMP-2 |
| Problem | Prepare a request for actual missing evidence. |
| Practitioner Job-to-be-Done | As a practitioner, I need to prepare a request for actual missing evidence. |
| Feature | Evidence-request Drafting |
| Expected Value | Reduce writing time while retaining human control. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Hybrid |
| Inputs | Selected evidence gaps and approved communication context |
| Outputs | Editable unsent draft linked to findings |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. VB-AI-INV-001 applies; human-confirmed candidates still pass supported deterministic validation. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. MMP-1.5 structured workflow or an explicitly approved bounded equivalent; isolated lab evaluation first. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Human approves recipients and content before any sending; drafting alone performs no external action. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. For AI: grounded/ungrounded and adversarial examples, model/prompt version, uncertainty and override evaluations. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Misaddressed sensitive information; implied consent to send. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP2-007 — Case Summary and Conflict Discovery

| Required field | Proposed contract |
|---|---|
| Task ID | MMP2-007 |
| MMP | MMP-2 |
| Problem | Understand current case state and possible source conflicts. |
| Practitioner Job-to-be-Done | As a practitioner, I need to understand current case state and possible source conflicts. |
| Feature | Case Summary and Conflict Discovery |
| Expected Value | Reduce repeated review reading. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Hybrid |
| Inputs | Authoritative case state, source references, separate human notes |
| Outputs | Summary labeling deterministic fact, unresolved evidence, annotation and AI explanation; possible conflicts |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. VB-AI-INV-001 applies; human-confirmed candidates still pass supported deterministic validation. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. MMP-1.5 structured workflow or an explicitly approved bounded equivalent; isolated lab evaluation first. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Every factual assertion is traceable; contradictions remain proposals and do not declare a source true. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. For AI: grounded/ungrounded and adversarial examples, model/prompt version, uncertainty and override evaluations. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Mixing opinion/fact; stale summaries; suppressing contradictory evidence. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP2-008 — Case Q&A

| Required field | Proposed contract |
|---|---|
| Task ID | MMP2-008 |
| MMP | MMP-2 |
| Problem | Ask bounded questions about the evidence and findings. |
| Practitioner Job-to-be-Done | As a practitioner, I need to ask bounded questions about the evidence and findings. |
| Feature | Case Q&A |
| Expected Value | Reduce navigation and query preparation. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Hybrid |
| Inputs | Authorized case plus user query |
| Outputs | Deterministic query results where possible, explained with provenance |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. VB-AI-INV-001 applies; human-confirmed candidates still pass supported deterministic validation. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. MMP-1.5 structured workflow or an explicitly approved bounded equivalent; isolated lab evaluation first. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Numeric/filter questions use declared deterministic queries; case isolation, unsupported-question refusal and exact values are tested. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. For AI: grounded/ungrounded and adversarial examples, model/prompt version, uncertainty and override evaluations. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Query ambiguity, cross-case leakage, fabricated answers. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |
