# MMP-2 Specification Engineering & Output Validation

> **Specification Ref:** `MMP2-SPEC-001`, `MMP2-SPEC-002`, `MMP2-SPEC-003`, `MMP2-SPEC-004`  
> **Core Concept:** Versioned Task Specifications with Strict Pydantic Output Schemas

---

## 1. Specification Engineering vs. Prompt Engineering

Prompt engineering alone is insufficient for professional accounting and legal workflows. Prompts degrade, drift across model revisions, and lack formal boundary enforcement.

**Specification Engineering** elevates workflows into formal, versioned contracts:

```
BUSINESS POLICY (e.g. IRS Basis Reporting Rules)
      │
      ▼
INTELLIGENCE SPECIFICATION (e.g. SPEC-CASE-EXCEPTION/v1.0)
      │
      ▼
CONTEXT CONTRACT (ContextProfile & Permitted Sources)
      │
      ▼
AGENT / TOOL PLAN (Deterministic Tool Sequence)
      │
      ▼
LOCAL MODEL PROMPT (Structured Template)
      │
      ▼
OUTPUT SCHEMA VALIDATOR (Pydantic / Regex Enforcement)
```

---

## 2. Standard Task Specification Example

### `Spec: CASE_EXCEPTION_EXPLANATION/v1`

- **Objective:** Explain why a deterministic reconciliation exception or missing basis finding exists.
- **Allowed Inputs:**
  - Deterministic reconciliation findings list.
  - Normalized transaction rows for the affected lot.
  - Source file ingestion metadata and hash pointers.
  - Form 1099-DA schema rules.
- **Forbidden Actions:**
  - Inventing missing dates, prices, or taxpayer intent.
  - Modifying the deterministic gain/loss calculation.
  - Offering legal tax positioning advice.
- **Mandatory Output Taxonomy:**
  Every identified factor must be categorized into one of five formal states:
  1. `KNOWN`: Established directly from ingested source documents.
  2. `INFERRED`: Derived from transfer matches with high confidence.
  3. `MISSING`: Data absent in all provided source documents.
  4. `CONFLICTING`: Contradictory records across two or more brokers/wallets.
  5. `UNSUPPORTED`: Claim made by client without source documentation.

---

## 3. Output Schema Contract

Every intelligence response must satisfy a formal Pydantic schema before presentation in the UI:

```python
class InvestigationFinding(BaseModel):
    category: Literal["KNOWN", "INFERRED", "MISSING", "CONFLICTING", "UNSUPPORTED"]
    description: str
    evidence_references: List[str]  # e.g. ["SRC-1099DA:row-14", "TX-BTC-008"]
    affected_asset: str
    unresolved_questions: List[str]

class InvestigationReport(BaseModel):
    spec_version: str = "CASE_EXCEPTION_EXPLANATION/v1"
    context_profile_id: str
    model_id: str
    model_weights_sha256: str
    findings: List[InvestigationFinding]
    confidence_class: Literal["HIGH", "MODERATE", "LOW", "INSUFFICIENT_EVIDENCE"]
    confidence_score: float
    generated_at_utc: str
```
