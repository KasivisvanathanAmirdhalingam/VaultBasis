# VB-REG-GAP-001: Form 1099-DA / Basis Reconciliation Regulatory & Evidence Context Analysis

> **Status:** `RESEARCH_DISPOSITION_RECORDED`  
> **Classification:** Assurance Boundary Invariant & Multi-Era Regulatory Roadmap  
> **Release Target:** MMP-1.1 Invariant Confirmed; MMP-1.5 Evidence Context; Post-1.5 Deferred  
> **Binding Directive:** Do not alter frozen MMP-1.1 code; preserve deterministic assurance boundaries; reject automatic tax determination claims.

---

## 1. Executive Summary & Regulatory Grounding

A comprehensive review of digital asset reporting under the Internal Revenue Code (IRC), Treasury regulations (TD 10000), IRS Revenue Procedure 2024-28, IRS Notice 2025-7, IRS Notice 2026-20, and current IRS Form 1099-DA / Form 8949 instructions establishes key boundaries between **cryptographic evidence assurance** and **tax return preparation**.

VaultBasis operates strictly as an **independent, deterministic evidence assurance engine**. It is intentionally not a tax calculator, tax-return preparation software, or legal determination agent.

---

## 2. Regulatory Fact-Check & Correction of Common Market Misconceptions

| Topic / Claim | Common Misconception | Actual IRS / Treasury Regulatory Fact | VaultBasis Assurance Boundary |
|---|---|---|---|
| **Form 1099-DA Data Fields** | Transaction hashes, wallet addresses, and execution timestamps are mandatory fields on Form 1099-DA. | **False.** Treasury/IRS explicitly eliminated mandatory reporting of transaction IDs, digital asset wallet addresses, and execution times on Form 1099-DA (see TD 10000 / IRB 2024-31). Form 1099-DA focuses on asset code/name, units, dates, proceeds, basis-reported indicator (Box 2), customer info reliance (Box 8), noncovered status (Box 9), and transfer-in info (Boxes 12a/12b). | VaultBasis accepts Form 1099-DA representations as reported by brokers without demanding non-mandated on-chain fields as mandatory prerequisites for 1099-DA ingestion. |
| **Form 8949 Basis Mismatch Codes** | Code O is the standard code for correcting broker-reported digital asset basis. | **False.** IRS Form 8949 instructions specifically prescribe **Code B** when basis shown on Form 1099-DA is incorrect. Code O is the residual "Other" code. | VaultBasis isolates and reports numerical variances and provenance without automatically assigning Form 8949 codes or giving tax characterization advice. |
| **2025 vs 2026 Reporting Scope** | Broker 1099-DA basis reporting is mandatory for all 2025 dispositions. | **False.** For 2025 sales, basis reporting is optional/transitional; mandatory basis reporting phases in for covered digital assets acquired on/after January 1, 2026. | VaultBasis recognizes `Box 2 = NO` as `REPORTING_SCOPE_DIFFERENCE` (`NOT_REPORTED`), never coercing missing broker basis to `$0.00` or fabricating a phantom tax mismatch. |
| **Rev. Proc. 2024-28 Scope** | Rev. Proc. 2024-28 mandates "Per-Wallet HIFO" cost basis. | **False.** Rev. Proc. 2024-28 governs the transitional allocation of previously unallocated basis to specific wallet addresses or accounts. It supports both specific-unit and global allocation methods, not a statutory mandate for HIFO. | VaultBasis treats accounting and lot-identification methods as declared evidence attributes, never endorsing a competing software result as "True Basis". |
| **Contemporaneous Lot Identification** | Notice 2025-7 and Notice 2026-20 require immediate on-chain attestation. | **False.** Notice 2026-20 extends temporary adequate identification relief through December 31, 2026, permitting books-and-records and standing-order identification for eligible custodial accounts. | VaultBasis records lot-identification declarations as factual evidence attributes within the practitioner evidence package. |

---

## 3. Triaged Release Disposition & Roadmap

```
                                      ┌─────────────────────────────────────────┐
                                      │           VB-REG-GAP-001 SCOPE          │
                                      └────────────────────┬────────────────────┘
                                                           │
               ┌───────────────────────────────────────────┼───────────────────────────────────────────┐
               ▼                                           ▼                                           ▼
┌─────────────────────────────┐             ┌─────────────────────────────┐             ┌─────────────────────────────┐
│    MMP-1.1 (CURRENT FREEZE)  │             │   MMP-1.5 (EVIDENCE CONTEXT)│             │     POST-1.5 (PRACTICE)     │
├─────────────────────────────┤             ├─────────────────────────────┤             ├─────────────────────────────┤
│ • Unknown-Never-Zero Invar. │             │ • Versioned Era Profiles    │             │ • Practitioner-Controlled   │
│ • Absent Basis → NOT_REPT   │             │   (2025 Scope vs 2026+)     │             │   Form 8949 Workpaper Export│
│ • Zero Code Changes to Edge │             │ • Regulatory Context Panel: │             │   (Read-only, non-advisory) │
│ • 100% Deterministic Recon  │             │   - Box 2 (Basis Reported)  │             │ • Multi-client batch queues │
│                             │             │   - Box 8 (Cust Info Rely)  │             │ • Reviewer/Approver workflow│
│                             │             │   - Box 9 (Noncovered)      │             │                             │
│                             │             │   - Boxes 12a/b (Transfer)  │             │                             │
│                             │             │ • Evidence Request Lists    │             │                             │
└─────────────────────────────┘             └─────────────────────────────┘             └─────────────────────────────┘
```

### A. MMP-1.1 (Current Candidate Verification)
1. **Unknown-Never-Zero Invariant Confirmed**:
   - For 2025 non-covered sales where broker Box 2 = `NO`, the engine records `source_a_value = "NOT_REPORTED (Box 2)"` and outputs `REPORTING_SCOPE_DIFFERENCE`. It **never** sets broker basis to `$0.00`.
   - For covered dispositions where a required field is missing, the engine emits `UNRESOLVED_DATA` with specific reason codes (`BASIS_UNAVAILABLE`, `ACQUISITION_DATE_UNAVAILABLE`, `QUANTITY_UNAVAILABLE`).
2. **Frozen Implementation**: Zero feature expansion in MMP-1.1. Physical qualification proceeds with frozen candidate.

### B. MMP-1.5 (Regulatory Evidence Context & Evidence Readiness)
1. **Source Profile & Reporting Era Awareness**: Explicit modeling of 2025 Transitional vs 2026+ Mandatory Covered Era rules.
2. **Enriched Finding Context** (Objective, Non-Advisory):
   ```
   Finding: Basis Difference Detected
   ────────────────────────────────────────────────────────
   Broker-Reported Basis (1099-DA) : $30,000.00
   Tax-Ledger Basis (Koinly)       : $35,000.00
   Variance                        : $5,000.00
   
   Regulatory Evidence Context:
   • Box 2 (Basis Reported to IRS) : YES
   • Box 8 (Customer Info Relied)  : NO
   • Box 9 (Noncovered Security)   : NO
   • Transfer-In Units Indicated   : YES (Box 12a)
   • Lot-Identification Method     : Declared Specific ID / HIFO
   • Rev. Proc. 2024-28 Records    : Available in Tax Ledger
   ────────────────────────────────────────────────────────
   Practitioner Action: Evaluate transfer-in acquisition records
   and verify standing-order documentation before filing.
   ```
3. **Evidence Request Lists**: Convert missing facts (e.g., unattached transfer-in basis, missing wallet allocation schedule) into structured practitioner evidence requests.

### C. Prohibited Assumptions (Assurance Integrity Guards)
The following terms and concepts are permanently excluded from the VaultBasis assurance core:
- ❌ **"True Basis" / "True HIFO Basis"**: VaultBasis compares declared evidence; it does not declare one accounting output to be the universal "truth".
- ❌ **"Audit Defense Attestation"**: Software records and receipts provide cryptographic integrity proofs, not legal or audit defense guarantees.
- ❌ **"Estimated Tax Savings Calculation"**: VaultBasis does not apply tax brackets, estimate tax liability, or promote tax reduction strategies.
- ❌ **"Automatic Form 8949 Code Selection"**: Form 8949 adjustment codes (e.g. Code B vs Code O) depend on taxpayer-specific legal facts and practitioner determination.
