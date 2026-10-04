# MMP-2 Context Engineering & Practitioner Envelope Control

> **Specification Ref:** `MMP2-CTX-001`, `MMP2-CTX-002`, `MMP2-CTX-003`  
> **Core Concept:** First-Class, Inspectable Context Profiles for Grounded AI Execution

---

## 1. Context Engineering Philosophy

In high-stakes tax investigations, the practitioner must have absolute transparency and control over what data, documents, and rules the AI is evaluating. Generic LLM chat interfaces obscure the prompt context; VaultBasis makes the **Context Envelope** an explicit, inspectable domain object.

---

## 2. ContextProfile Domain Schema

```python
class ContextProfile(BaseModel):
    """
    Explicit, auditable context envelope bounding an intelligence execution.
    """
    context_profile_id: str
    jurisdiction: str = "US"
    tax_year: int = 2025
    case_id: str
    workspace_id: str
    permitted_evidence_scopes: List[str]  # e.g., ["SRC-1099DA-01", "SRC-COINBASE-02"]
    permitted_regulatory_corpora: List[str]  # e.g., ["IRS_NOTICE_2014_21", "TREAS_REG_1_6045"]
    prior_years_enabled: bool = False
    prior_year_case_ids: List[str] = []
    deterministic_findings_enabled: bool = True
    external_network_allowed: bool = False  # STRICT AIR-GAP: Defaults False
    intelligence_policy_id: str = "US_FIRM_RESTRICTED"
    specification_version: str = "CASE_EXCEPTION_EXPLANATION/v1"
    model_policy_id: str = "LOCAL_MISTRAL_7B_Q4"
```

---

## 3. The Practitioner Context Inspector (UI Component)

The Intelligence pane provides an inspectable **Context Drawer** enabling the CPA to:

1. **View Exact Included Sources:** Inspect which CSVs, Form 1099-DAs, or prior-year workpapers are in the model's retrieval window.
2. **Exclude Sensitive or Contested Documents:** Toggle individual evidence files off to perform "what-if" analyses.
3. **Verify Regulatory Grounding:** Verify which IRS notices, Rev. Ruls., or Treasury regulations are being cited.
4. **Audit Token Consumption:** View exact context window utilization (e.g. `4,210 / 32,768 tokens`) without any cloud metering fees.

---

## 4. Dynamic Context Assembly Pipeline

```
┌───────────────────────────┐
│     PRACTITIONER QUERY    │  "Why is acquisition date missing on Lot #4?"
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│  CONTEXT PROFILER ENGINE  │  Resolves case_id, active tax_year, permitted sources
└─────────────┬─────────────┘
              │
              ├──────► Deterministic Finding Context (Case status, unmapped lots)
              ├──────► Evidence Excerpts (Raw CSV lines, broker 1099-DA Box 2 flags)
              ├──────► Provenance Chain (Transaction -> Source Document -> Ingestion Hash)
              └──────► Regulatory Authority (IRS Form 1099-DA instructions §Box 2)
              │
              ▼
┌───────────────────────────┐
│ ASSEMBLED CONTEXT ENVELOPE│  Bounded, structured, zero-leakage prompt payload
└───────────────────────────┘
```
