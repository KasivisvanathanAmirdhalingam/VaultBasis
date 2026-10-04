# MMP-2 Model Context Protocol (MCP) Tool Contract

> **Specification Ref:** `MMP2-MCP-001`  
> **Core Concept:** Standardized, Read-Only MCP Tool Interface Between Agents and VaultBasis Core

---

## 1. The MCP Security Boundary

To prevent agents from executing arbitrary SQL queries or corrupting SQLite data files, agents interact with VaultBasis strictly through an embedded **Model Context Protocol (MCP) Server**:

```
┌────────────────────────┐
│     SPECIALIST AGENT   │
└───────────┬────────────┘
            │ MCP JSON-RPC Invocation
            ▼
┌────────────────────────┐
│ VAULTBASIS MCP SERVER  │  (Schema validation & access policy enforcement)
└───────────┬────────────┘
            │ Internal Python / SQLite API (Strict Read-Only)
            ▼
┌────────────────────────┐
│ VAULTBASIS CORE STORE  │
└────────────────────────┘
```

---

## 2. Enumerated MCP Tool Surface

The VaultBasis local MCP server exposes the following authorized tools:

| Tool Name | Parameters | Return Type | Description |
|---|---|---|---|
| `get_case` | `case_id: str` | `CanonicalCase` | Retrieves top-level case summary, tax year, and status |
| `list_case_findings` | `case_id: str` | `List[Finding]` | Lists deterministic reconciliation exceptions & missing basis lots |
| `get_transaction` | `transaction_id: str` | `CanonicalTransaction` | Retrieves normalized transaction details and raw row fields |
| `trace_provenance` | `case_id: str, lot_id: str` | `ProvenanceGraph` | Traces exact chain: lot -> transaction -> source document -> byte hash |
| `get_evidence_excerpt`| `source_id: str, row_range: [int, int]` | `List[str]` | Fetches raw CSV/PDF lines from content-addressed evidence store |
| `get_receipt` | `case_id: str` | `OutcomeReceipt` | Fetches signed outcome receipt payload |
| `verify_receipt` | `receipt_json: str` | `VerificationResult` | Calls deterministic verifier to validate signature & schema |
| `search_regulatory_corpus` | `query: str, tax_year: int` | `List[Citation]` | Searches versioned IRS/Treasury guidance corpus (RAG-D) |
| `get_system_version` | None | `SystemVersionInfo` | Returns build SHA, schema version, and compatibility matrix |

---

## 3. Auditing & Security

Every MCP tool invocation is logged with timestamp, caller agent ID, parameter hash, and response size to ensure complete transparency during professional audit review.
