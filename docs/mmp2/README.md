# VaultBasis MMP-2: Local Professional Intelligence & Agentic Control Plane

> **Release Phase:** MMP-2 — Local Professional Intelligence, Investigation & Multi-Agent Architecture  
> **Positioning:** *Local Digital-Asset Tax Intelligence for Professional Review*  
> **Core Architectural Dictum:** MMP-2 does **NOT** convert VaultBasis into a SaaS product. Intelligence is an optional, local-first subsystem operating over customer-controlled localhost data. Deterministic reconciliation and receipt verification remain 100% independent of intelligence availability.

---

## 1. Executive Summary & Philosophy

VaultBasis MMP-2 elevates the qualified deterministic core (MMP-1.1) and commercial control plane (MMP-1.5) into an interactive, evidence-grounded intelligence platform for CPAs, EAs, and tax attorneys. 

Unlike generic "AI tax chatbots" that hallucinate advice or compromise client privacy by shipping financial records to multi-tenant cloud APIs, VaultBasis MMP-2 is engineered on three immutable pillars:

1. **Local-First & Air-Gapped Intelligence:** All model inference, retrieval, agent orchestration, and context assembly occur strictly within the practitioner's local host runtime (`127.0.0.1`). Network egress is denied by default (`NETWORK_EGRESS = DENIED`).
2. **Deterministic Primacy:** The AI layer is a consumer of deterministic objects—cases, intake tables, reconciliation results, provenance graphs, and signed receipts. AI never calculates tax math, never alters deterministic state, and never signs truth.
3. **Complementary Ecosystem Integration:** VaultBasis is designed to complement—not displace—existing tax preparation suites (e.g., UltraTax, CCH Axcess, Drake, Lacerte), accounting platforms, research libraries, and practice management tools.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         VAULTBASIS PLATFORM ARCHITECTURE                         │
│                                                                                  │
│   MMP-2: Local Intelligence & Agentic Pane (Optional Sidecar / MCP / RAGs)       │
│   ════════════════════════════════════════════════════════════════════════════   │
│   MMP-1.5: Commercial Policy, Durability, Firm Identity & Admin Audit Log        │
│   ════════════════════════════════════════════════════════════════════════════   │
│   MMP-1.1: Frozen Deterministic Core (Reconciliation Math & Cryptographic Receipts)│
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Key Architectural Invariants

| Dimension | Invariant Rule | Enforcement Mechanism |
|---|---|---|
| **SaaS Avoidance** | Zero cloud database reliance; zero external token metering; zero required cloud accounts. | Pure local distribution running on loopback interfaces. |
| **Zero Token Bleed** | Customer transaction records, wallet addresses, and evidence never egress to third-party APIs. | Outbound network socket isolation; local model execution only. |
| **Primacy of Truth** | AI cannot mutate reconciliation results, alter tax lots, or generate ungrounded numbers. | Read-only MCP tool interfaces; deterministic engine operates independently. |
| **Zero-Downtime Decoupling** | If the intelligence runtime fails, crashes, or updates, the core reconciliation remains 100% operational. | Sidecar process boundary; loose IPC / localhost REST coordination. |
| **Canonical Data Immutability** | Vector indexes and embeddings are disposable derived caches; canonical SQLite/files remain authoritative. | `intelligence/` directory can be deleted and rebuilt without data loss. |
| **Region & Policy Governance** | Model execution enforces firm and regional compliance (e.g., US firm restrictions). | Model Provenance Registry & Policy Compatibility Engine. |
| **Evidence-Grounded Confidence** | Confidence reflects mathematical coverage and verification, not LLM linguistic tone. | Multi-signal ensemble formula (40% deterministic, 20% source, 15% retriever, etc.). |

---

## 3. Strategic Storage Boundary (Evidence Vault Deferred)

**Formal Policy on Digital Asset Storage:**
- Extended commercial monetization of multi-year digital asset storage (**VaultBasis Evidence Vault**) is **explicitly parked for N+1th MMP** to maintain razor-sharp focus on the immediate commercial pain: Form 1099-DA reconciliation, missing basis investigation, evidence gap detection, and CPA review workflows.
- MMP-2 introduces the underlying content-addressed storage abstractions, interfaces, and retention hooks (`EvidenceStorageProvider`) so that future storage tiers can be activated with zero architectural refactoring.
- **Clarification of Scope:** VaultBasis stores professional digital-asset *evidence, statements, and receipts*—it **NEVER** acts as a cryptocurrency custodian or private-key wallet.

---

## 4. Documentation Index

The complete MMP-2 architecture is decomposed into focused domain specifications:

| Document | Topic & Focus Area |
|---|---|
| [architecture.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/architecture.md) | High-level system topology, sidecar architecture, and zero-downtime contract |
| [intelligence_boundary.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/intelligence_boundary.md) | Strict separation between Deterministic Core and Probabilistic AI |
| [context_engineering.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/context_engineering.md) | Context Profile contract, evidence scoping, and practitioner context inspector |
| [specification_engineering.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/specification_engineering.md) | Versioned specification framework, task schemas, and output validation |
| [local_model_runtime.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/local_model_runtime.md) | Local open-weight inference engine, multi-model roles, and compute budgeting |
| [model_and_tool_policy.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/model_and_tool_policy.md) | Model Provenance Registry, weights verification, and tool approval gates |
| [regional_policy.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/regional_policy.md) | Policy-driven compliance profiles (US_FIRM_RESTRICTED, EU_LOCAL_AI, etc.) |
| [rag_architecture.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/rag_architecture.md) | Five isolated RAG domains (Evidence, Provenance, Product, Regulatory, Historical) |
| [agent_architecture.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/agent_architecture.md) | Six bounded specialist agents (Investigator, Gap Analyst, Reviewer, Questions, etc.) |
| [multi_agent_a2a.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/multi_agent_a2a.md) | Local Agent-to-Agent (A2A) collaboration, evidence packets, and coordinator flow |
| [mcp_contract.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/mcp_contract.md) | Model Context Protocol (MCP) server endpoints and security tool boundaries |
| [ensemble_confidence.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/ensemble_confidence.md) | Multi-signal evidence confidence framework and critic/verifier model |
| [persistence_and_upgrade.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/persistence_and_upgrade.md) | Canonical persistence preservation, disposable vector cache, and zero-drift upgrades |
| [distribution_packaging.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/distribution_packaging.md) | Container-compatible native desktop launcher vs optional IT Docker/OCI images |
| [security_privacy_and_egress.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/security_privacy_and_egress.md) | Zero network egress guarantees, socket testing, and air-gap qualification |
| [open_source_governance.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/open_source_governance.md) | Open-source SBOM tracking, license compliance, and framework minimization |
| [future_evidence_vault_hooks.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/future_evidence_vault_hooks.md) | Forward-compatible storage abstractions for parked digital asset evidence vault |
| [task_ledger.md](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp2/task_ledger.md) | Complete MMP-2 engineering task breakdown, critical path ranking, and dependencies |
