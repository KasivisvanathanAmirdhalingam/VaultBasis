# MMP-3 — Evidence Assurance Platform: task ledger

**Status: PROPOSED / NOT AUTHORIZED FOR IMPLEMENTATION.** Updated 2026-09-30. Priorities are provisional hypotheses to validate with practitioners, not promised release content.

See [roadmap](VAULTBASIS_PRODUCT_ROADMAP.md), [Git/evidence governance](../audit/git-and-evidence-governance.md) and [side-by-side audit ledger](../audit/traceability-matrix.md). No task has execution evidence or acceptance yet. Owners are unassigned; product and architecture must approve scope before implementation.

| Task | Feature | Current evidence | Next decision |
|---|---|---|---|
| MMP3-001 | Assurance API, Receipt SDK and Verifier Ecosystem | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP3-002 | Portable Evidence Graph and Review History | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP3-003 | Enterprise Identity, Policy and Deployment | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP3-004 | Enterprise Connectors and Additional Assurance Domains | Founder roadmap proposal only | Practitioner priority + architecture scope |

## MMP3-001 — Assurance API, Receipt SDK and Verifier Ecosystem

| Required field | Proposed contract |
|---|---|
| Task ID | MMP3-001 |
| MMP | MMP-3 |
| Problem | Integrate bounded assurance across professional systems. |
| Practitioner Job-to-be-Done | As a practitioner, I need to integrate bounded assurance across professional systems. |
| Feature | Assurance API, Receipt SDK and Verifier Ecosystem |
| Expected Value | Enable portable independently verifiable outcomes. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic platform |
| Inputs | Versioned authorized evidence/API requests and contract definitions |
| Outputs | APIs/SDK and interoperable receipt verification |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | External implementations pass declared conformance vectors; API does not delegate assurance authority to AI. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Contract drift, inconsistent verifiers, overbroad API claims. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP3-002 — Portable Evidence Graph and Review History

| Required field | Proposed contract |
|---|---|
| Task ID | MMP3-002 |
| MMP | MMP-3 |
| Problem | Carry provenance and review history across tools. |
| Practitioner Job-to-be-Done | As a practitioner, I need to carry provenance and review history across tools. |
| Feature | Portable Evidence Graph and Review History |
| Expected Value | Improve audit continuity. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic platform |
| Inputs | Canonical evidence identities, provenance and separate review events |
| Outputs | Portable graph and tamper-evident history |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | History preserves machine/human/AI distinctions and verifies change lineage without modifying prior signed records. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Privacy leakage, ambiguous graph semantics, false tamper-proof claims. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP3-003 — Enterprise Identity, Policy and Deployment

| Required field | Proposed contract |
|---|---|
| Task ID | MMP3-003 |
| MMP | MMP-3 |
| Problem | Operate firm-wide controls in an approved environment. |
| Practitioner Job-to-be-Done | As a practitioner, I need to operate firm-wide controls in an approved environment. |
| Feature | Enterprise Identity, Policy and Deployment |
| Expected Value | Enable enterprise governance and deployment choice. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic platform |
| Inputs | Approved RBAC/policies, tenancy boundary and deployment requirements |
| Outputs | Identity controls, private-cloud/OCI packaging and reproducible infrastructure where justified |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Tenant isolation, least privilege, recovery and deployment evidence are qualified; firm policy never becomes a tax determination. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Complexity, policy bypass, supply-chain risk, pulling enterprise scope into stabilization. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP3-004 — Enterprise Connectors and Additional Assurance Domains

| Required field | Proposed contract |
|---|---|
| Task ID | MMP3-004 |
| MMP | MMP-3 |
| Problem | Apply the assurance model across approved sources/domains, including AI-output evidence. |
| Practitioner Job-to-be-Done | As a practitioner, I need to apply the assurance model across approved sources/domains, including AI-output evidence. |
| Feature | Enterprise Connectors and Additional Assurance Domains |
| Expected Value | Test whether the model generalizes beyond current workflow. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Hybrid integration around deterministic contracts |
| Inputs | Domain-specific evidence and separately approved semantic specifications |
| Outputs | Versioned connectors/domain adapters and bounded assurance records |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Each new domain has an explicit contract, corpus, uncertainty boundary and independent qualification; no inherited claims of correctness. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. For AI: grounded/ungrounded and adversarial examples, model/prompt version, uncertainty and override evaluations. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Unvalidated generalization, new semantic authority, unbounded connector scope. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |
