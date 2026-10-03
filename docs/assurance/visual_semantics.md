# VaultBasis Visual Semantics & Color Coding Invariant

## 1. Visual-Semantic Invariant (Attention, Not Tax Judgment)
VaultBasis colors convey **practitioner attention requirements**, not tax correctness or legal judgments.

| Visual Style | Meaning in VaultBasis | Regulatory / Tax Meaning | Practitioner Next Step |
|---|---|---|---|
| **Green** (`#059669`) | **AGREED / MATCHED** | Compared fields agree within declared tolerance. Does **NOT** mean return is correct. | Proceed to review next item. |
| **Amber** (`#b45309`) | **MATERIAL DIFFERENCE** | Material variance detected between broker and ledger under declared rules. | Review Finding Why and determine if adjustment or workpaper note is needed. |
| **Orange** (`#d97706`) | **UNRESOLVED** | Evidence is insufficient to determine agreement (e.g. missing basis Box 1e). | Follow up with client or broker for missing information. |
| **Red** (`#dc2626`) | **SYSTEM / INTEGRITY ERROR** | Reserved exclusively for operational failures, corrupt files, or invalid signatures. | Check file format or re-export source documents. |

---

## 2. Invariants
- VaultBasis must never display a red error merely because a difference was found between a broker and ledger. Differences are normal expected accounting observations.
- Green status must always be qualified by the standard disclaimer that tax correctness is not determined by the software.
