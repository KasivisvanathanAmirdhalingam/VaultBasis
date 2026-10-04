# MMP-2 Local Intelligence Architecture & Topology

> **Specification Ref:** `MMP2-ARCH-001`  
> **Topology:** Dual-Process Loopback Daemon & Intelligence Sidecar

---

## 1. System Topology Overview

VaultBasis MMP-2 operates as a decoupled, local-first system. The core application runs the deterministic engine and commercial control plane on `127.0.0.1:8000`. The optional Intelligence Runtime runs as an isolated sidecar process on loopback (e.g. `127.0.0.1:8100` or internal IPC).

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   VAULTBASIS DESKTOP RUNTIME                                     │
│                                                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                   PRACTITIONER UI                                        │   │
│   │    • Cases / Workpapers Dashboard        • Deterministic Outcome View                    │   │
│   │    • Receipt Verifier                    • Intelligence & Review Pane                    │   │
│   │    • Context Profile Inspector           • Model & Policy Settings                       │   │
│   └─────────────────────────────────────────────┬────────────────────────────────────────────┘   │
│                                                 │ Loopback HTTP / IPC                            │
│                                                 ▼                                                │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                         VAULTBASIS CORE DAEMON (127.0.0.1:8000)                          │   │
│   │                                                                                          │   │
│   │   ┌──────────────────────────┐ ┌──────────────────────────┐ ┌────────────────────────┐  │   │
│   │   │  DETERMINISTIC RECONCILE │ │   COMMERCIAL CONTROL     │ │  LOCAL PERSISTENCE STORE │  │   │
│   │   │  • Intake Normalization  │ │   • Offline Licensing    │ │  • SQLite Store (WAL)    │  │   │
│   │   │  • Basis Lot Matching    │ │   • Capacity Metering    │ │  • Canonical Cases       │  │   │
│   │   │  • Ed25519 Signer        │ │   • Firm Identity        │ │  • Content-Addressed     │  │   │
│   │   │  • Unmetered Verifier    │ │   • Audit Event Log      │ │    Evidence Blobs        │  │   │
│   │   └──────────────────────────┘ └──────────────────────────┘ └───────────┬────────────┘  │   │
│   └─────────────────────────────────────────────┬───────────────────────────│────────────────┘   │
│                                                 │ MCP Tool Calls            │ Canonical Read     │
│                                                 ▼                           ▼ Only               │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                    VAULTBASIS INTELLIGENCE SIDECAR (127.0.0.1:8100)                      │   │
│   │                                                                                          │   │
│   │   ┌──────────────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │                         AGENT ORCHESTRATION & A2A BUS                            │   │   │
│   │   │   • Case Investigator Agent               • Evidence Gap Analyst Agent           │   │   │
│   │   │   • Reviewer Risk Agent                   • Client Question Agent                │   │   │
│   │   │   • Regulatory Research Agent             • Multi-Year Continuity Agent          │   │   │
│   │   └──────────────────────────────────────────────────────────────────────────────────┘   │   │
│   │        │                               │                               │                 │   │
│   │        ▼                               ▼                               ▼                 │   │
│   │   ┌───────────────────────┐   ┌──────────────────────────┐   ┌───────────────────────┐   │   │
│   │   │   LOCAL MODEL RUNTIME │   │    5 ISOLATED RAG STORES │   │   SPEC & CONTEXT ENG  │   │   │
│   │   │   • Fast Router LLM   │   │    • RAG-A: Case Evidence│   │   • Context Profiler  │   │   │
│   │   │   • Reasoning LLM     │   │    • RAG-B: Provenance   │   │   • Spec Executor     │   │   │
│   │   │   • Critic / Verifier │   │    • RAG-C: Product Spec │   │   • Confidence Matrix │   │   │
│   │   │     LLM               │   │    • RAG-D: Regulatory   │   │   • Output Validator  │   │   │
│   │   │   • Regional Policy   │   │    • RAG-E: Multi-Year   │   │                       │   │   │
│   │   └───────────────────────┘   └────────────┬─────────────┘   └───────────────────────┘   │   │
│   └────────────────────────────────────────────│─────────────────────────────────────────────┘   │
│                                                ▼                                                 │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                       DISPOSABLE DERIVED STORAGE (intelligence/)                         │   │
│   │   • Vector Embeddings Cache       • Regulatory Knowledge Packs       • Model Weights     │   │
│   └──────────────────────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Process Boundary & Zero-Downtime Contract

To guarantee that AI features never jeopardize core tax reconciliation, the Core Daemon and Intelligence Sidecar run in separate process boundaries with a formal **Zero-Downtime Contract**:

| Core State | AI Sidecar State | Operational Outcome | Core Status |
|---|---|---|---|
| `RUNNING` | `AI_OFF` (Disabled by user) | Standard deterministic reconciliation & receipt verification active | **PASS (100% Core Function)** |
| `RUNNING` | `AI_STARTING` (Loading model) | Core fully accessible; UI shows intelligence spinner | **PASS (100% Core Function)** |
| `RUNNING` | `AI_FAILED` (OOM / Crash) | Error displayed in Intelligence pane; core reconciles without interruption | **PASS (100% Core Function)** |
| `RUNNING` | `AI_UPDATING` (Model weights upgrade) | Core operational; background sidecar downloads/swaps weights | **PASS (100% Core Function)** |
| `RUNNING` | `INDEX_REBUILD` (Regenerating vectors) | Core reads existing data; AI displays reindexing progress bar | **PASS (100% Core Function)** |

---

## 3. Communication Protocol

1. **Core to UI:** HTTP/REST on `127.0.0.1:8000` (Cases, Ingestion, Receipts, Commercial Policy, Identity).
2. **Intelligence to UI:** WebSocket / SSE streaming on `127.0.0.1:8100` (Investigation streaming, Agent thought processes, Citations).
3. **Intelligence to Core:** Model Context Protocol (MCP) tool invocation over loopback HTTP/JSON-RPC (Read-only data access).
