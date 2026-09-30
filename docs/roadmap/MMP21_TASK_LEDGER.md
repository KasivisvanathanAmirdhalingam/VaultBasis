# MMP-2.1 — Evidence Connectivity: task ledger

**Status: PROPOSED / NOT AUTHORIZED FOR IMPLEMENTATION.** Updated 2026-09-30. Priorities are provisional hypotheses to validate with practitioners, not promised release content.

See [roadmap](VAULTBASIS_PRODUCT_ROADMAP.md), [Git/evidence governance](../audit/git-and-evidence-governance.md) and [side-by-side audit ledger](../audit/traceability-matrix.md). No task has execution evidence or acceptance yet. Owners are unassigned; product and architecture must approve scope before implementation.

| Task | Feature | Current evidence | Next decision |
|---|---|---|---|
| MMP21-001 | Versioned Source Adapters | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP21-002 | Controlled Document Intake | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP21-003 | Firm Mappings and Tax-software Export | Founder roadmap proposal only | Practitioner priority + architecture scope |
| MMP21-004 | Connector Health and Lineage | Founder roadmap proposal only | Practitioner priority + architecture scope |

## MMP21-001 — Versioned Source Adapters

| Required field | Proposed contract |
|---|---|
| Task ID | MMP21-001 |
| MMP | MMP-2.1 |
| Problem | Acquire broker, exchange, tax-ledger and 1099-DA evidence consistently. |
| Practitioner Job-to-be-Done | As a practitioner, I need to acquire broker, exchange, tax-ledger and 1099-DA evidence consistently. |
| Feature | Versioned Source Adapters |
| Expected Value | Reduce repetitive preparation. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic integration |
| Inputs | Authorized external systems and versioned source profiles |
| Outputs | Source bytes/metadata through canonical validation |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Reproducible acquisition retains lineage and adapter version; changed/unsupported profiles fail visibly; kernel authority unchanged. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | API/schema drift, permissions, rate limits and nondeterministic source updates. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP21-002 — Controlled Document Intake

| Required field | Proposed contract |
|---|---|
| Task ID | MMP21-002 |
| MMP | MMP-2.1 |
| Problem | Bring cloud documents into a case deliberately. |
| Practitioner Job-to-be-Done | As a practitioner, I need to bring cloud documents into a case deliberately. |
| Feature | Controlled Document Intake |
| Expected Value | Reduce evidence collection friction. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic integration |
| Inputs | User-authorized document selection; later controlled email intake only after separate approval |
| Outputs | Imported evidence with origin and permission history |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Minimum permissions, explicit destination case and no silent import or send; duplicate/failure handling is traceable. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Broad cloud permissions and accidental taxpayer data exposure. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP21-003 — Firm Mappings and Tax-software Export

| Required field | Proposed contract |
|---|---|
| Task ID | MMP21-003 |
| MMP | MMP-2.1 |
| Problem | Reuse validated mappings and hand reviewed work to downstream software. |
| Practitioner Job-to-be-Done | As a practitioner, I need to reuse validated mappings and hand reviewed work to downstream software. |
| Feature | Firm Mappings and Tax-software Export |
| Expected Value | Reduce repeated transformation and re-entry. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic integration |
| Inputs | Confirmed mapping versions and authorized export selection |
| Outputs | Reusable mappings and versioned export artifacts |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Mappings cannot silently expand semantics; exports preserve origin and do not represent tax-law determinations. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | Mapping drift, incorrect export interpretation, unsupported target profiles. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |

## MMP21-004 — Connector Health and Lineage

| Required field | Proposed contract |
|---|---|
| Task ID | MMP21-004 |
| MMP | MMP-2.1 |
| Problem | Know whether acquired evidence is complete and current. |
| Practitioner Job-to-be-Done | As a practitioner, I need to know whether acquired evidence is complete and current. |
| Feature | Connector Health and Lineage |
| Expected Value | Prevent hidden preparation failures. |
| Priority | Proposed stage capability; order and inclusion pending Associate/CPA evidence. |
| Deterministic / AI / Hybrid | Deterministic integration |
| Inputs | Connector versions, fetch outcomes and source identities |
| Outputs | Health/failure states and lineage record |
| Human Judgment Boundary | Human professional judgment remains separate; workflow/AI/integration cannot change authoritative findings, provenance or signed receipts. External actions require explicit approval. |
| Dependencies | Qualified product baseline, approved stage architecture, protected evidence contract, practitioner observations and defined data/access interfaces. |
| Security / Privacy Impact | Potential sensitive case evidence: minimize collection, enforce case/firm permissions, document processing location and retention, prevent secrets/evidence in logs. No new egress or analytics by implication. |
| Acceptance Criteria | Partial/failed fetch never reports complete; retry and version changes remain visible without changing prior evidence. |
| Evidence Required | Versioned task cases with expected/actual results, relevant negative controls, provenance and isolation checks, practitioner before/after task observations, exact source/artifact identity and reviewer decision. |
| Implementation commit IDs | None — no implementation yet; record full SHA(s) at task closeout. |
| Documentation closeout | Required six-category review under [execution standard](../task_execution_standard.md); [registry](../task_registry.json). |
| Status | PROPOSED; no implementation, measured value or qualification claimed. |
| Risks | False completeness, excessive logging, leakage of external credentials. |

| Implementation / change | Automated evidence | Human / practitioner evidence | Qualification / decision |
|---|---|---|---|
| Not started | Not executed | Not collected | Pending scope approval |
