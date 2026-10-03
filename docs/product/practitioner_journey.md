# VaultBasis Practitioner Journey

## 1. Zero-Knowledge Onboarding
A practitioner (CPA or EA) opening VaultBasis for the first time experiences a guided narrative flow:

```
Launch App
   ↓
Dashboard: [ Explore Sample Case ] (1-Click Launch)
   ↓
Case Context: Sample Client (Acme Holdings LLC) · Tax Year 2025
   ↓
Stage 1 (Evidence Readiness):
  • Source A (Broker Evidence · Form 1099-DA) [READY ✓]
  • Source B (Tax-Ledger Evidence · Koinly CSV) [READY ✓]
   ↓
Stage 2 (Reconcile): Click [ ⚡ Run Deterministic Reconciliation ]
   ↓
Stage 3 (Review Findings):
  • Evaluated: 5 records
  • Agreed: 2 records (Green)
  • Material Differences: 2 records (Amber — Basis & Proceeds Variance)
  • Unresolved Items: 1 record (Orange — Missing Cost Basis / Box 1e)
   ↓
Stage 4 (Preserve & Verify):
  • Inspect Outcome Receipt
  • Open Offline Verifier → Drop Receipt → [ VALID ✓ ]
  • Tamper Receipt → Drop Receipt → [ INVALID ✗ ]
  • Understand: Tax Correctness = NOT DETERMINED
```

---

## 2. Core Questions Answered in the UI
1. **Whose case is this?** Clearly identified by Client Reference and Tax Year at the top of the workspace.
2. **What are the two sources?** Source A is Broker Evidence (what broker reported to IRS). Source B is Tax-Ledger Evidence (client's independently calculated tax ledger).
3. **What is VaultBasis doing?** Normalizing records, aligning transaction dates and asset symbols, applying declared IRC 1099-DA reconciliation rules, and computing exact variances using deterministic Decimal arithmetic.
4. **What should the practitioner inspect?** Amber material differences (review why broker and ledger diverge) and Orange unresolved items (determine if missing records or non-covered status requires workpaper notes).
5. **What does the receipt prove?** The receipt proves the exact reconciliation result was produced by VaultBasis under the declared schema and signed by the installation key. It does not establish that the taxpayer's return is legally or factually correct.
