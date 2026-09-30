# VaultBasis product roadmap

Source: [founder roadmap/Git directive](../handover/directives/03-product-evolution-and-git-governance.txt), 2026-09-30. Status: **direction and proposed task scope; not delivery commitments or authorization to implement future stages**. [Git governance](../audit/git-and-evidence-governance.md) and [side-by-side audit ledger](../audit/traceability-matrix.md) apply throughout.

VaultBasis independently compares supported evidence, preserves agreements, differences and unresolved information, explains findings and provenance, and produces a portable Outcome Receipt. It does not become a tax calculator by adding workflow, AI or connectivity. Missing evidence never silently becomes certainty: UNKNOWN ≠ ZERO; UNRESOLVED ≠ MATCHED.

| Stage | Practitioner/business hypothesis | Capability boundary | Exit evidence | Current status / ledger |
|---|---|---|---|---|
| MMP-1 | Can deterministic independent assurance work? | Supported intake, deterministic reconciliation, findings/provenance, local signing, independent verification, Golden Corpus | Bounded reproducibility, contract and independent-verifier evidence | Foundational implementation and historical evidence exist; no blanket current release certification. [Master ledger](../master_tasks_ledger.md) is historical scope evidence. |
| MMP-1.1 | Can an uninformed practitioner consume it safely and professionally? | Native distribution, web/Edge UX, access/security/entitlement, help, offline/hosted verifier, accessibility, Associate/CPA validation | Obtain → install → understand → use → receipt → independent verification without developer explanation | Active stabilization; [existing ledger](../mmp11_task_ledger.md), [UX blueprint](../ux/canonical-ux-blueprint.md), [NFR](../non_functional_requirements.md). |
| MMP-1.5 | Does evidence workflow management reduce practitioner work? | Evidence inbox/readiness/request list/review queue/lifecycle/notes/workpaper/multi-case organization | Observed case-review effort and completeness against a baseline, with machine history intact | Proposed; [MMP15 tasks](MMP15_TASK_LEDGER.md) |
| MMP-2 | Can intelligence reduce evidence toil while retaining trust? | Classification/extraction/mapping/gap explanation/drafting/summaries/conflict discovery/Q&A | Provenance-grounded evaluations, uncertainty handling, human confirmation, no altered assurance outcomes | Research only until approved; [MMP2 tasks](MMP2_TASK_LEDGER.md) |
| MMP-2.1 | Does connectivity reduce case preparation friction? | Adapters, controlled import/export, firm mappings, source lineage and connector version/health | Versioned reproducible acquisition and privacy/permission evidence | Proposed; [MMP21 tasks](MMP21_TASK_LEDGER.md) |
| MMP-2.5 | Can exception-driven review reduce firm-wide effort? | Maker/reviewer workflow, requests, change-impact/delta review, firm policy controls, operational metrics | Preserved history, correct review routing and measured effort improvements | Proposed; [MMP25 tasks](MMP25_TASK_LEDGER.md) |
| MMP-3 | Can independent assurance generalize across systems and workflows? | APIs/SDK, portable evidence graph, enterprise identity, tamper-evident review, connector framework, private deployment, additional domains | Interoperability, isolation, governance, domain-specific validation and external verification | Proposed; [MMP3 tasks](MMP3_TASK_LEDGER.md) |

## Three product planes

| Plane | Responsibilities | Authority / change boundary |
|---|---|---|
| Assurance | Canonicalization, reconciliation, findings, provenance, receipt, signing, verification | Authoritative machine evidence; highest change control; frozen contracts remain protected |
| Experience / Workflow | Cases, evidence inbox, review queue, workpapers, access, Help, web/Edge interactions | Human workflow state and annotations are separate from machine determination |
| Intelligence / Integration | Classification, extraction, schema proposals, retrieval, connectors and automation | Proposals/acquisition only; validated inputs enter deterministic processing through declared boundaries |

These product planes describe responsibilities. They are distinct from deployment/privacy boundaries (local evidence processing, website/access, artifact distribution); do not conflate the two taxonomies.

**VB-AI-INV-001 — Intelligence Is Subordinate to Evidence.** AI may classify, extract candidate values, propose mappings, explain, summarize, retrieve, prioritize, draft and flag possible conflicts. AI may not alter outcomes, fabricate missing evidence, convert unresolved to matched, determine tax correctness/compliance, overwrite provenance, alter signed receipts, conceal uncertainty or silently act externally. Human confirmation does not waive supported-source validation or authorize unreviewed kernel changes. Evidence-request drafts require human approval before sending.

External evidence → versioned connector → canonical evidence boundary → validation → deterministic kernel → findings/provenance → signed receipt → verification. Intelligence assists around this chain; it does not supply an authoritative tax conclusion.

## Sequencing and exclusions

MMP-1.1 excludes AI, new tax semantics/reconciliation algorithms, billing, analytics, CRM, large connector ecosystems and firm automation. Docker/OCI, Terraform and enterprise deployment are future capabilities unless a concrete earlier requirement is approved. The older master ledger's commercialization work is not current stabilization authorization.

Practitioner evidence controls priority: readiness may matter more than AI explanations; delta review may matter more than a dashboard. Ledger priorities are proposals awaiting Associate/CPA evidence. No numerical example in a briefing is measured customer data or an acceptance threshold. Each stage needs a bounded hypothesis, baseline, acceptance decision and evidence before promotion.

Documentation, stage planning, isolated lab research and connector research can progress alongside stabilization. Future production implementation waits for approved architecture/tasks and a qualified base. Preserve `lab/mmp-2-ai` isolation; no experimental code enters `release/mmp-1.1`. Do not create all future branches now.

## Shared task evidence rules

Every task ledger records problem, practitioner job, proposed feature/value/priority, computation type, inputs/outputs, human judgment boundary, dependencies, security/privacy impact, acceptance criteria, required evidence, status and risks. Each entry is PROPOSED, not implemented or accepted. On implementation, add named owner, source/PR, exact tests/results, immutable artifact/deployment identity and acceptance decision using the [change record](../audit/git-and-evidence-governance.md). Keep observed evidence beside the requirement; do not erase failed runs when a fix passes.
