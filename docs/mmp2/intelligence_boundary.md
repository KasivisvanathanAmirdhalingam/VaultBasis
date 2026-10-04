# MMP-2 Intelligence & Deterministic Boundary

> **Specification Ref:** `MMP2-ARCH-002`  
> **Core Principle:** Strict Separation of Deterministic Truth from Probabilistic Intelligence

---

## 1. Architectural Firewall

In professional tax accounting, numerical results and legal filings must be deterministic, reproducible, and verifiable. Generative AI models are inherently probabilistic and cannot be permitted to calculate basis numbers, match lots, or sign receipts.

VaultBasis enforces a strict architectural firewall:

```
┌──────────────────────────────────────────────┐
│       DETERMINISTIC BOUNDARY (TRUTH)         │
│                                              │
│ • Intake CSV Parsing (Lossless Decimals)     │
│ • Tax Lot Matching (FIFO / Specific ID)      │
│ • Gain / Loss Math (RFC 8785 Canonical JSON) │
│ • Ed25519 Cryptographic Receipt Signatures   │
│ • Commercial Policy & Capacity Evaluation    │
└──────────────────────┬───────────────────────┘
                       │ READ-ONLY CONSUMPTION (MCP)
                       ▼
┌──────────────────────────────────────────────┐
│       PROBABILISTIC BOUNDARY (INSIGHT)       │
│                                              │
│ • Exception Explanation                      │
│ • Missing Basis Root-Cause Investigation     │
│ • Evidence-Gap Detection & Classification    │
│ • Client Question Drafting                   │
│ • Regulatory Guidance Retrieval & Synthesis  │
└──────────────────────────────────────────────┘
```

---

## 2. Invariant Rules of the Boundary

1. **Read-Only Access:** The intelligence runtime has zero write access to canonical SQLite tables (`cases`, `sources`, `transactions`, `receipts`, `commercial_license`, `firm_identity`). All data queries are executed via read-only MCP tools.
2. **Zero Synthetic Numbers:** Intelligence agents are strictly forbidden from inventing numbers or modifying cost basis amounts. If an acquisition price is missing in the source records, the agent outputs `MISSING_BASIS` with explicit provenance pointers—it never hallucinates an estimated dollar value.
3. **Receipt Immutability:** Outcome receipts (`outcome_receipt.json`) are generated and signed strictly by `ReceiptSigner` using Ed25519. The intelligence runtime cannot generate, sign, or alter outcome receipts.
4. **Independent Verifier Separation:** The offline verifier (`apps/verifier/verify_receipt.py`, `independent_verifier.html`) contains zero AI dependencies, zero vector databases, and zero LLM weights. Verification remains a 100% deterministic mathematical check.
