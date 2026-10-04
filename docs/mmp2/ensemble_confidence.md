# MMP-2 Evidence-Grounded Confidence & Ensemble Framework

> **Specification Ref:** `MMP2-ENS-001`, `MMP2-ENS-002`, `MMP2-ENS-003`  
> **Core Concept:** Confidence as Mathematical Evidence Quality Rather Than LLM Linguistic Persuasion

---

## 1. The Core Principle

A pervasive flaw in generative AI is that models write confidently even when hallucinating. In professional tax compliance, **Confidence MUST represent verifiable evidence support**, never the model's internal self-reported certainty.

---

## 2. Multi-Signal Confidence Formula

VaultBasis computes an explicit, multi-signal composite score ($0.00 - 1.00$):

$$\text{Confidence Score} = w_1 S_{\text{det}} + w_2 S_{\text{cov}} + w_3 S_{\text{rag}} + w_4 S_{\text{agree}} + w_5 S_{\text{cite}} - P_{\text{contra}} - P_{\text{missing}}$$

| Signal Component | Weight | Description |
|---|---|---|
| **Deterministic Support ($S_{\text{det}}$)** | **40%** | Fraction of facts directly backed by deterministic database rows |
| **Source Coverage ($S_{\text{cov}}$)** | **20%** | Percentage of affected transaction rows present in ingested files |
| **Retriever Agreement ($S_{\text{rag}}$)** | **15%** | Overlap between RAG-A (Evidence) and RAG-B (Provenance) |
| **Model Agreement ($S_{\text{agree}}$)** | **10%** | Agreement between Primary Model B and Critic Model C |
| **Citation Completeness ($S_{\text{cite}}$)** | **10%** | Valid, resolvable references for every factual claim |
| **Contradiction Penalty ($P_{\text{contra}}$)** | Variable | Penalty applied if contradictory broker rows exist (up to -50%) |
| **Missing Evidence Penalty ($P_{\text{missing}}$)**| Variable | Penalty applied for unlinked transfers / missing wallets (up to -40%) |

---

## 3. Four-Tier Confidence Classification

The numerical score is mapped into deterministic practitioner tiers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HIGH (Score >= 0.85)                                                        │
│ All facts grounded in primary source documents; deterministic provenance    │
│ complete; zero contradictory records.                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ MODERATE (0.65 <= Score < 0.85)                                             │
│ Inferred transfers with high probabilistic match; secondary source present;  │
│ minor non-material date ambiguities.                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ LOW (0.40 <= Score < 0.65)                                                  │
│ Key acquisition source missing; conflicting records between two brokers.    │
│ Requires explicit practitioner review.                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ INSUFFICIENT_EVIDENCE (Score < 0.40)                                        │
│ Critical records absent; transfer origins completely unmapped.              │
│ Automated question drafting triggered for client follow-up.                 │
└─────────────────────────────────────────────────────────────────────────────┘
```
