# MMP-2 Multi-Agent Orchestration & Local A2A Protocol

> **Specification Ref:** `MMP2-A2A-001`  
> **Core Concept:** Internal Localhost Agent-to-Agent (A2A) Coordination via Structured Evidence Packets

---

## 1. Orchestration Workflow

When a practitioner poses a complex query (e.g., *"Why is this $84,200 disposition marked UNRESOLVED?"*), the system does not prompt an LLM to answer in one shot. It coordinates specialized sub-agents through an internal **A2A Bus**:

```
                       PRACTITIONER QUERY
                                │
                                ▼
                       A2A COORDINATOR
                                │
       ┌────────────────────────┼────────────────────────┐
       │ Dispatch               │ Dispatch               │ Dispatch
       ▼                        ▼                        ▼
PROVENANCE AGENT         EVIDENCE AGENT           REGULATORY AGENT
  (RAG-B Graph)            (RAG-A Chunks)           (RAG-D Rules)
       │                        │                        │
       └────────────────────────┼────────────────────────┘
                                │ Structured Evidence Packets
                                ▼
                     REVIEWER / SYNTHESIZER
                                │
                                ▼ (Cross-Model Critic Check)
                         CRITIC MODEL
                                │
                                ▼
                     GROUNDED PRACTITIONER ANSWER
```

---

## 2. Structured Evidence Packets

Sub-agents communicate exclusively via typed **Evidence Packets** rather than free-form conversational text:

```json
{
  "packet_id": "PKT-20261004-9812",
  "source_agent": "ProvenanceAgent",
  "target_agent": "Synthesizer",
  "finding_type": "MISSING_ACQUISITION_SOURCE",
  "confidence": 0.96,
  "evidence_references": [
    {
      "source_id": "SRC-COINBASE-01",
      "row_index": 441,
      "sha256": "3152df830089f2d1e2b4676573c387b99adfe092",
      "field_excerpt": "TRANSFER_IN, 1.5 BTC, 2025-04-10"
    }
  ],
  "unsupported_claims": [],
  "provenance_chain_complete": false
}
```

---

## 3. Localhost-Only Invariant

The A2A protocol operates entirely within local memory / loopback IPC. No agent endpoints or A2A communication channels are exposed over the network, ensuring zero external attack surface.
