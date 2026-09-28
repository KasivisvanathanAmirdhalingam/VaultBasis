# VaultBasis Layer 2: Deterministic Findings & Explanations

VaultBasis enforces a strict separation between discovering differences (Reconciliation Semantics) and explaining them to a practitioner (Explanations).

## 1. Separation of Concerns
- **Reconciliation Engine**: Identifies deterministic states (`BASIS_DIFFERENCE`, `PROCEEDS_DIFFERENCE`, `MATCHED`, `UNRESOLVED_DATA`, etc.).
- **Explanation Renderer**: Takes structured finding facts and fixed linguistic templates to generate human-readable text. It **never** infers findings.

## 2. Six-Question Boundary
Every explanation answers exactly six questions:
1. **What was compared**
2. **Broker source** value
3. **Tax-ledger source** value
4. **Observed difference** or required fact missing
5. **Matched using** (e.g. Asset symbol and disposition date)
6. **Why this finding occurred**
7. **VaultBasis determination** (The canonical finding code)
8. **Boundary** (e.g. "VaultBasis identifies the difference. It does not determine which basis amount is tax-correct.")

## 3. Vocabulary Constraints
Explanations must remain neutral and objective:
- Never use "wrong", "compliant", "IRS-approved", or "audit-proof".
- "correct" is strictly limited to boundary disclaimers (e.g. "does not determine which is tax-correct").
- If data is missing (`UNRESOLVED_DATA`), the engine **refuses to infer, substitute, or default** the missing information.

## 4. Privacy Distinctions
- **Local Workpaper**: Rendered explanations (e.g. in the dashboard) may include the actual financial values, as the practitioner already has local access.
- **Portable Receipt / Provenance**: The signed receipt MUST remain free of specific financial values.

## 5. Golden Assertions
Explanations are covered by ATDD Golden Tests. Altering the wording of a standard finding template is considered a boundary violation and will intentionally fail the build unless re-authorized by the specification.
