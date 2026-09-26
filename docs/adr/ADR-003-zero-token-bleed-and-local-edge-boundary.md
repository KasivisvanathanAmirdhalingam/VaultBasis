# ADR-003: Zero Token Bleed and Customer-Premises Local Edge Boundary

* **Status**: ACCEPTED / FROZEN  
* **Date**: 2026-09-23  
* **Deciders**: VaultBasis Architecture Group  
* **PRD Reference**: §2.4 (Local-First by Architecture), §18 (Edge Runtime), §21 (Zero Token Bleed / Zero Cloud Inference)  

---

## Context and Problem Statement

Financial transactions, tax forms (1099-DA), wallet addresses, and cost basis ledgers constitute sensitive non-public personal information (NPI) subject to Gramm-Leach-Bliley Act (GLBA), IRC §7216 tax preparer confidentiality rules, and GDPR.

Traditional SaaS models require uploading all raw ledger data to cloud servers. Modern "AI" platforms send financial text to commercial LLM APIs (OpenAI, Anthropic, Google), creating immediate confidentiality breach risks and token egress ("token bleed").

## Decision Drivers

* Institutional CPAs and enterprises cannot adopt tools that transmit unredacted client financial records to third-party cloud infrastructure.
* VaultBasis must operate within the customer's declared trust boundary without requiring cloud accounts or remote server dependencies.

## Decision Outcome

1. **Local-First Edge Runtime**:
   - VaultBasis Edge runs locally on customer premises as a single Docker/OCI container or local process.
   - All state, uploaded documents, transactions, and SQLite databases persist exclusively on local disk.
2. **Zero Cloud Inference in MMP-1**:
   - MMP-1 reconciliation core uses pure deterministic algorithms on local CPU.
   - LLMs, cloud RAG, and MCP servers are excluded from MMP-1 (reserved for MMP-2).
3. **Zero Transaction Egress**:
   - Zero outbound network packets containing transaction rows, client names, cost basis, or evidence payloads.
   - Network calls are strictly restricted to optional local airgapped verification or customer-directed export.

### Positive Consequences
* Complies with IRC §7216 without requiring complex third-party data processing agreements (DPAs).
* Eliminates cloud infrastructure hosting COGS for transaction computation.
* Allows offline execution in airgapped environments.

### Negative Consequences
* Compute resources are limited by customer local host capacity.
* Product telemetry is limited to sanitized local diagnostics.
