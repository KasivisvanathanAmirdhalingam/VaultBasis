# MMP-2 Five-Domain Isolated RAG Architecture

> **Specification Ref:** `MMP2-RAG-001`, `MMP2-RAG-002`, `MMP2-RAG-003`, `MMP2-RAG-004`, `MMP2-RAG-005`  
> **Core Concept:** Preventing Retrieval Contamination Through Domain-Isolated Vector & Graph Stores

---

## 1. Why Five Isolated RAG Systems?

A major failure mode of enterprise AI is dumping heterogeneous documents (client tax CSVs, IRS instructions, product manuals, case notes) into a single shared vector index. This causes cross-domain hallucination, semantic collisions, and compliance leaks.

VaultBasis partitions retrieval into **five strictly bounded RAG domains**:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         FIVE ISOLATED RETRIEVAL DOMAINS                          │
│                                                                                  │
│   ┌─────────────────────┐   ┌─────────────────────┐   ┌──────────────────────┐   │
│   │ RAG-A: CASE EVIDENCE│   │ RAG-B: DETERMINISTIC│   │ RAG-C: PRODUCT /     │   │
│   │                     │   │        PROVENANCE   │   │        CONTRACT      │   │
│   │ • Source CSV rows   │   │ • Exact Graph Map:  │   │ • Receipt Schemas    │   │
│   │ • Broker 1099-DAs   │   │   Receipt -> Result │   │ • Matching Rules     │   │
│   │ • Ingested PDFs     │   │   -> Tx -> Source   │   │ • Assurance Levels   │   │
│   │ • Client notes      │   │ • Hash-addressed    │   │ • Error definitions  │   │
│   └─────────────────────┘   └─────────────────────┘   └──────────────────────┘   │
│                 │                         │                         │            │
│                 ▼                         ▼                         ▼            │
│   ┌──────────────────────────────────────────────────────────────────────────┐   │
│   │                        AGENT QUERY DISPATCHER                            │   │
│   └──────────────────────────────────────────────────────────────────────────┘   │
│                 ▲                                                   ▲            │
│                 │                                                   │            │
│   ┌─────────────────────┐                               ┌────────────────────┐   │
│   │ RAG-D: REGULATORY   │                               │ RAG-E: HISTORICAL  │   │
│   │        TAX KNOWLEDGE│                               │        MULTI-YEAR  │   │
│   │ • IRS Notices       │                               │ • Prior Year (2024)│   │
│   │ • Treas. Regs       │                               │ • Prior Year (2025)│   │
│   │ • Form Instructions │                               │ • Historical Lots  │   │
│   │ • Effective dates   │                               │ • Carried Forward  │   │
│   └─────────────────────┘                               └────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Domain Deep Dive

### RAG-A: Case Evidence Store
- **Contents:** Raw ingested CSV chunks, PDF statements, broker exports, wallet transaction records for the active case.
- **Query Type:** Dense vector similarity + BM25 keyword hybrid search.
- **Example:** *"Find transaction where 2.5 ETH was transferred out on April 14, 2025."*

### RAG-B: Deterministic Provenance Store (Graph Lookup)
- **Contents:** The exact, deterministic relational lineage linking:
  `Receipt Field -> Reconciliation Result -> Canonical Tx -> Parser Output -> Raw Source Row -> Ingested File Hash`
- **Query Type:** Pure deterministic graph traversal (no embedding approximation).
- **Example:** *"What exact CSV row and file hash generated Tax Lot #12's acquisition date?"*

### RAG-C: Product / Contract Store
- **Contents:** VaultBasis normative schema definitions, reconciliation rules, assurance level requirements, and error code taxonomy.
- **Query Type:** Dense semantic search over curated product documentation.
- **Example:** *"Why was this transaction assigned Assurance Level L2 instead of L1?"*

### RAG-D: Regulatory Tax Knowledge Store
- **Contents:** Official, versioned IRS guidance, Form 1099-DA draft instructions, Notice 2014-21, Rev. Rul. 2019-24, and Treasury regulations with mandatory metadata (Tax Year, Effective Date, Authority Level, Document Version).
- **Query Type:** Dense vector search with strict metadata filtering.
- **Example:** *"What are the reporting requirements for Box 2 of Form 1099-DA in tax year 2025?"*

### RAG-E: Historical / Multi-Year Store
- **Contents:** Archived VaultBasis cases from preceding tax years (2024, 2025, 2026).
- **Query Type:** Relational lookup + vector search across historical workpapers.
- **Example:** *"Where did this 2027 opening Bitcoin tax lot originate in the 2025 filing?"*
