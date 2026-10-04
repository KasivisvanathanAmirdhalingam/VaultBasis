# VaultBasis MMP-2: Local Intelligence & Agentic Control Plane — Master Tasks Ledger

> **Release Phase:** MMP-2 — Local Professional Intelligence, Investigation & Multi-Agent Architecture  
> **Directive:** Local-first, evidence-grounded intelligence running over localhost data plane without cloud dependence.

---

## 1. Master Task Decomposition

| Task ID | Component / Capability | Category | Scope & Objective | Adjacent System Boundary (Complements vs Excludes) | Dependencies | Target Output / Deliverable | Status |
|---|---|---|---|---|---|---|---|
| **MMP2-SEC-001** | Intelligence Threat Model & Security Contract | Security | Threat modeling for indirect prompt injection, RAG poisoning, tool escalation, sidecar token auth, and DoS | **Complements:** Firm IT security policies.<br>**Excludes:** Remote SIEM / antivirus agent. | None | `docs/mmp2/threat_model.md` | `BASELINED` |
| **MMP2-ARCH-001** | Local Intelligence Architecture Contract | Foundation | Dual-process sidecar architecture, loopback IPC/REST binding, Zero-Downtime Contract | **Complements:** Local OS process manager.<br>**Excludes:** SaaS cloud orchestrator. | MMP-1.5 Baseline | `edge/intelligence/daemon.py` | `PLANNED` |
| **MMP2-MODEL-001** | Local Model Runtime Engine | Foundation | Open-weight GGUF inference engine bindings (Metal/AVX2/DirectX) with RAM caps | **Complements:** Local workstation compute.<br>**Excludes:** Cloud LLM API gateway. | None | `edge/intelligence/runtime.py` | `PLANNED` |
| **MMP2-MCP-001** | VaultBasis MCP Tool Server | Foundation | Read-only MCP JSON-RPC server exposing case, finding, transaction, and receipt tools | **Complements:** Desktop UI.<br>**Excludes:** Direct arbitrary SQL shell. | MMP-1.1, MMP-1.5 | `edge/intelligence/mcp_server.py` | `PLANNED` |
| **MMP2-RAG-001** | Case Evidence RAG (Domain A) | Retrieval | Chunking and vector indexing of active case CSVs, PDFs, and broker statements | **Complements:** File system exports.<br>**Excludes:** General web search index. | SQLite Store | `edge/intelligence/rag/evidence.py` | `PLANNED` |
| **MMP2-RAG-002** | Deterministic Provenance RAG (Domain B) | Retrieval | Exact graph traversal linking receipts to normalized transactions and source rows | **Complements:** Workpaper audit trails.<br>**Excludes:** Synthetic tax calculations. | Reconciliation Core | `edge/intelligence/rag/provenance.py`| `PLANNED` |
| **MMP2-RAG-003** | Regulatory Tax Knowledge RAG (Domain D) | Retrieval | Versioned IRS notices, Form 1099-DA draft rules, and Treasury regulations index | **Complements:** Checkpoint/CCH research.<br>**Excludes:** Interactive legal advisory. | Knowledge Pack | `edge/intelligence/rag/regulatory.py`| `PLANNED` |
| **MMP2-IDX-001** | Disposable Vector Index Manager | Storage | Automated rebuild of derived vector indexes from canonical SQLite tables | **Complements:** SQLite persistent store.<br>**Excludes:** Distributed vector cloud. | SQLite Store | `edge/intelligence/indexer.py` | `PLANNED` |
| **MMP2-CTX-001** | Context Profile Contract & Engine | Context Eng | `ContextProfile` schema, evidence scoping, prior-year toggles, and token budgeter | **Complements:** Case file manager.<br>**Excludes:** Unbounded prompt buffers. | None | `edge/intelligence/context.py` | `PLANNED` |
| **MMP2-CTX-002** | Practitioner Context Inspector | UI / View | Context drawer in UI displaying exact sources, rules, and model settings in context | **Complements:** CPA review UI.<br>**Excludes:** Opaque prompt engineering. | Context Engine | Web Dashboard Component | `PLANNED` |
| **MMP2-SPEC-001** | Specification Framework & Validation | Spec Eng | Versioned task specifications (`CASE_EXCEPTION_EXPLANATION/v1`, etc.) with Pydantic schemas | **Complements:** Audit workpaper specs.<br>**Excludes:** Freeform conversational chat. | None | `edge/intelligence/specs/` | `PLANNED` |
| **MMP2-POL-001** | Model Provenance & Registry | Governance | Cryptographic SHA-256 weight verification, license tracker, and SBOM auditor | **Complements:** Corporate IT compliance.<br>**Excludes:** Public app store hub. | None | `edge/intelligence/models.py` | `PLANNED` |
| **MMP2-POL-002** | Regional & Organizational Policy Engine | Policy | Compliance profiles (`US_FIRM_RESTRICTED`, `EU_LOCAL_AI`, `LOCAL_STRICT`) | **Complements:** Firm compliance rules.<br>**Excludes:** Geo-IP blocking services. | Model Registry | `edge/intelligence/policy.py` | `PLANNED` |
| **MMP2-AGT-001** | Specialist Agent Runtime & Dispatcher | Agentic | Bounded agent runner with tool invocation loop and state machine | **Complements:** Local API daemon.<br>**Excludes:** Autonomous web agents. | MCP Server | `edge/intelligence/agent_runner.py`| `PLANNED` |
| **MMP2-AGT-002** | Case Investigator Agent | Agentic | Interactive Q&A over case facts, finding explanations, and lot inquiries | **Complements:** Tax return workpaper.<br>**Excludes:** Tax return filing. | Agent Runtime | `edge/intelligence/agents/investigator.py` | `PLANNED` |
| **MMP2-AGT-003** | Evidence Gap Analyst Agent | Agentic | Root-cause analysis of missing basis with `KNOWN/MISSING/CONFLICTING` taxonomy | **Complements:** CPA tax review.<br>**Excludes:** Automatic guessing of cost. | Agent Runtime | `edge/intelligence/agents/gap_analyst.py` | `PLANNED` |
| **MMP2-AGT-004** | Reviewer Risk Agent | Agentic | Pre-filing CPA risk triage and prioritization of unverified lots | **Complements:** Tax manager review.<br>**Excludes:** Sign-off / filing authority. | Agent Runtime | `edge/intelligence/agents/reviewer.py` | `PLANNED` |
| **MMP2-AGT-005** | Client Question Drafting Agent | Agentic | Precise taxpayer inquiry generator requesting missing source files | **Complements:** Email / Practice Mgmt.<br>**Excludes:** Direct email dispatch / CRM. | Agent Runtime | `edge/intelligence/agents/question_drafter.py` | `PLANNED` |
| **MMP2-A2A-001** | Local Agent-to-Agent Bus | Agentic | Coordinator protocol distributing sub-tasks and aggregating typed Evidence Packets | **Complements:** Local memory bus.<br>**Excludes:** Distributed internet A2A. | Agent Runtime | `edge/intelligence/a2a_bus.py` | `PLANNED` |
| **MMP2-ENS-001** | Multi-Signal Confidence Calculator | Ensemble | Composite scoring: Deterministic support, Source coverage, RAG consistency | **Complements:** Audit evidence ranking.<br>**Excludes:** Subjective probability claims. | Agent Runtime | `edge/intelligence/confidence.py` | `PLANNED` |
| **MMP2-ENS-002** | Critic & Verification Model Check | Ensemble | Cross-model validator checking for ungrounded statements or hallucinated citations | **Complements:** Peer-review QA.<br>**Excludes:** Cloud verification API. | Local Model Runtime| `edge/intelligence/critic.py` | `PLANNED` |
| **MMP2-DIST-001** | Native Desktop Intelligence Packager | Packaging | Bundles sidecar engine into macOS (.dmg) and Windows (.exe) single-click installers | **Complements:** Native desktop OS.<br>**Excludes:** Mandatory Docker Desktop. | CI Pipeline | Build Scripts | `PLANNED` |
| **MMP2-DIST-002** | Enterprise OCI / Docker Images | Packaging | Standalone container images for firm IT departments deploying on local Kubernetes/Podman | **Complements:** On-prem Kubernetes.<br>**Excludes:** Multi-tenant SaaS hosting. | Containerfile | CI Pipeline | `PLANNED` |
| **MMP2-UPG-001** | Zero-Drift Upgrade Migration Suite | Persistence | Pre-upgrade snapshot, integrity gate, and proof that existing receipt hashes never drift | **Complements:** SQLite backup API.<br>**Excludes:** Schema-forking rewrites. | SQLite Store | `tests/quality/test_mmp2_upgrade.py` | `PLANNED` |
| **MMP2-VLT-001** | Forward Storage Abstraction Interfaces | Future Vault | `EvidenceStorageProvider` interface decoupling core from physical storage backends | **Complements:** Local evidence folder.<br>**Excludes:** Paid cloud storage quota. | Storage Layer | `edge/storage/provider.py` | `PLANNED` |

---

## 2. Critical Path Execution Waves

```
WAVE 1: FOUNDATION & INTERFACES (Weeks 1-3)
├── MMP2-ARCH-001: Sidecar Process & Zero-Downtime Contract
├── MMP2-MODEL-001: Local Inference Runtime Abstraction
├── MMP2-MCP-001: Read-Only VaultBasis MCP Tool Server
└── MMP2-VLT-001: Evidence Storage Provider Interface

WAVE 2: CONTEXT, SPEC & DOMAIN RAGS (Weeks 4-6)
├── MMP2-CTX-001: Context Profile Engine & Token Scoping
├── MMP2-SPEC-001: Versioned Task Specifications & Output Schemas
├── MMP2-RAG-001: Case Evidence RAG (Domain A)
├── MMP2-RAG-002: Deterministic Provenance RAG (Domain B)
└── MMP2-RAG-003: Regulatory Tax Knowledge RAG (Domain D)

WAVE 3: SPECIALIST AGENTS & A2A (Weeks 7-9)
├── MMP2-AGT-001: Bounded Agent Runtime Loop
├── MMP2-AGT-002: Case Investigator Agent
├── MMP2-AGT-003: Evidence Gap Analyst Agent (Taxonomy Enforcement)
├── MMP2-AGT-004: Reviewer Risk Agent
├── MMP2-AGT-005: Client Question Drafting Agent
└── MMP2-A2A-001: Local A2A Evidence Packet Bus

WAVE 4: ENSEMBLE, CONFIDENCE & GOVERNANCE (Weeks 10-12)
├── MMP2-ENS-001: Multi-Signal Evidence Confidence Calculator
├── MMP2-ENS-002: Critic & Cross-Model Verifier
├── MMP2-POL-001: Model Provenance Registry & Hash Check
└── MMP2-POL-002: Regional Policy Engine (US_FIRM_RESTRICTED, etc.)

WAVE 5: UI INSPECTOR & DISTRIBUTION (Weeks 13-15)
├── MMP2-CTX-002: Practitioner Context Inspector UI
├── MMP2-DIST-001: Native Desktop Launcher Packaging
├── MMP2-DIST-002: Optional Enterprise OCI Docker Image
└── MMP2-UPG-001: Zero-Drift Upgrade Qualification Gate
```
