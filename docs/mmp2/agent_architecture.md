# MMP-2 Bounded Specialist Agent Architecture

> **Specification Ref:** `MMP2-AGT-001`, `MMP2-AGT-002`, `MMP2-AGT-003`, `MMP2-AGT-004`  
> **Core Concept:** Specialist, Tool-Bounded Agents Instead of Generic Autonomous Bots

---

## 1. Agent Architecture Philosophy

Rather than building unpredictable, open-ended autonomous agents, VaultBasis deploys **six bounded specialist agents**. Each agent has a single responsibility, a strictly defined toolset (via MCP), and a versioned output schema.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         VAULTBASIS SPECIALIST AGENT ROSTER                       │
│                                                                                  │
│   ┌───────────────────────────┐   ┌───────────────────────────┐                  │
│   │ 1. CASE INVESTIGATOR AGENT│   │ 2. EVIDENCE GAP ANALYST   │                  │
│   │ • Answers case questions  │   │ • Root-cause missing basis│                  │
│   │ • Explains findings       │   │ • Classifies known/missing│                  │
│   │ • Traces provenance links │   │ • Flags conflicting data  │                  │
│   └───────────────────────────┘   └───────────────────────────┘                  │
│                                                                                  │
│   ┌───────────────────────────┐   ┌───────────────────────────┐                  │
│   │ 3. REVIEWER RISK AGENT    │   │ 4. CLIENT QUESTION AGENT  │                  │
│   │ • Ranks high-risk items   │   │ • Drafts bounded inquiries│                  │
│   │ • Pre-audit CPA triage    │   │ • Requests missing files  │                  │
│   │ • Discontinuity detection │   │ • Explains why data needed│                  │
│   └───────────────────────────┘   └───────────────────────────┘                  │
│                                                                                  │
│   ┌───────────────────────────┐   ┌───────────────────────────┐                  │
│   │ 5. REGULATORY AGENT       │   │ 6. MULTI-YEAR CONTINUITY  │                  │
│   │ • Cites IRS notices       │   │ • Carry-forward tracking  │                  │
│   │ • Checks effective dates  │   │ • Prior-year lot audits   │                  │
│   │ • Jurisdictional bounds   │   │ • Amendment reconciliation│                  │
│   └───────────────────────────┘   └───────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Agent Specifications

### Agent 1: Case Investigator Agent
- **Purpose:** Answers practitioner inquiries regarding active case evidence and reconciliation results.
- **Allowed Tools:** `get_case`, `list_case_findings`, `get_transaction`, `trace_provenance`, `get_evidence_excerpt`.
- **Output:** Grounded explanation with specific file and row references.

### Agent 2: Evidence Gap Analyst Agent
- **Purpose:** Analyzes unresolved dispositions to diagnose *why* cost basis is missing or unestablished.
- **Output Taxonomy:** Classifies factors strictly as `KNOWN`, `INFERRED`, `MISSING`, `CONFLICTING`, or `UNSUPPORTED`.
- **Example:** *"Lot #14 has missing basis because transfer TX-991 arrived from an unlinked external wallet 0xabc... with no preceding acquisition record in provided statements."*

### Agent 3: Reviewer Risk Agent
- **Purpose:** Assists senior CPAs and EAs by prioritizing lots and findings requiring professional review.
- **Risk Ranking Factors:** High-dollar dispositions with missing basis, manual practitioner overrides, inconsistent broker 1099-DA Box 2 flags, prior-year basis discrepancies.

### Agent 4: Client Question Agent
- **Purpose:** Consumes findings from the Evidence Gap Analyst and generates precise, professional data requests to send to the taxpayer.
- **Example Output:** *"Please provide the 2024-2025 CSV transaction export or Form 1099-B from Kraken account ending in ...491 to establish the acquisition date and cost basis for 4.2 SOL disposed on Sept 10, 2025."*

### Agent 5: Regulatory Research Agent
- **Purpose:** Retrieves official IRS notices, Treasury regulations, and Form 1099-DA instructions matching the case's specific fact pattern.
- **Invariants:** Mandatory citation metadata (Title, Tax Year, Effective Date, URL/Reference); strict uncertainty declaration when guidance is non-binding or draft.

### Agent 6: Multi-Year Continuity Agent
- **Purpose:** Reconciles basis carry-forward between prior-year VaultBasis archives and the current tax year.
- **Example:** Validates that opening 2025 Bitcoin lots match the closing 2024 unliquidated inventory byte-for-byte.
