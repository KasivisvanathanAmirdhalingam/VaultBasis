# VaultBasis — Adjacent-Platform Learnings Ledger (Digital Trust & Evidence Architecture)

> **Document Version**: v1.0.0-TRUST  
> **Source of Learning**: Adjacent digital-trust platforms (e.g., Youtrust / Yousign)  
> **Status**: APPROVED STRATEGIC GUIDANCE & LEDGER  
> **Standard**: Granite-Grade / Architectural Differentiation / MMP-1.5 Freeze Invariant  

---

## 1. Architectural & Category Positioning

### 1.1 Category Differentiation: Vertical Professional Evidence vs. Horizontal Digital Trust
A surface reading of digital trust platforms (such as Youtrust) might suggest high overlap with VaultBasis because both build products centered on "trust", "verification", and "audit trails". However, their objects of trust, buyers, regulatory centers of gravity, and trust topologies are fundamentally distinct:

| Dimension | Horizontal Digital Trust (e.g. Youtrust) | Vertical Financial/Tax Evidence (VaultBasis) |
| :--- | :--- | :--- |
| **Core Category** | Digital trust services (e-Sign, Identity, Seals) | Digital-asset tax reconciliation & evidence system |
| **Primary Buyer** | SMEs, mid-market, regulated businesses (Fintech, HR, Legal) | CPAs, EAs, professional tax and accounting practices |
| **Trusted Object** | Identity, signer, company registry, bank account, document seal | Broker 1099-DA records, client tax ledgers, deterministic findings |
| **Core Action** | Sign / verify / seal | Ingest / reconcile / review / evidence / verify |
| **Evidence Output** | Transaction audit trail (JSON / PDF) | Signed Evidence Receipt & standalone Evidence Package |
| **Regulatory Gravity** | EU eIDAS, KYC/KYB, AML/CFT, GDPR | US Tax Code, Form 1099-DA, IRS broker reporting, workpapers |
| **Trust Topology** | **Cloud-Hosted**: Client $\rightarrow$ Cloud Service $\rightarrow$ Audit Trail | **Local-First / Edge**: Client files stay local $\rightarrow$ Offline Verifier |
| **Verification Scope** | Provider certifies identity / signature event | Verifier proves deterministic receipt integrity (math & schema) |

### 1.2 "Borrow Principles, Not Features"
VaultBasis does **not** compete with horizontal digital trust providers, nor does it seek to become one. Instead, VaultBasis extracts proven architectural principles from mature digital-trust platforms to reinforce its vertical wedge:
1. **Evidence is the product, not a byproduct**: The value delivered to the CPA is not merely comparing two CSV files; it is producing durable, portable, and tamper-evident proof of the reconciliation.
2. **Provenance as a first-class citizen**: Showing exactly *which* records, *what* ruleset, and *whose* review created a finding.
3. **Clean semantic boundaries**: Strict distinction between what the system verifies vs. what requires human or legal judgment.
4. **Composing primitives into professional workflows**: Keeping foundational steps decoupled.

---

## 2. Policy Statement: `ADJACENT-PLATFORM LEARNING POLICY`

```text
+-------------------------------------------------------------------------------------------------------------------+
| VAULTBASIS GOVERNANCE POLICY: ADJACENT-PLATFORM RESEARCH & ROADMAP INTEGRATION                                    |
+-------------------------------------------------------------------------------------------------------------------+
| 1. External product research may introduce architectural lessons into the VaultBasis roadmap but does NOT       |
|    authorize unvetted product changes or feature creep.                                                          |
| 2. Each identified lesson must be explicitly classified into:                                                     |
|    - NOW (MMP-1.5) : Validates or refines an existing release invariant / human test verification.                 |
|    - NEXT (MMP-2)  : Formalizes an already-planned architectural primitive or documentation standard.             |
|    - LATER (MMP-3+): Deferred until strong market pull and practitioner demand are demonstrated.                  |
|    - NON-GOAL      : Strategically outside VaultBasis scope (e.g., e-sign, KYC, document custody).                 |
| 3. No adjacent-platform feature shall enter MMP-1.5 solely because another digital-trust company provides it.    |
| 4. VaultBasis remains a digital-asset tax reconciliation and evidence product, NOT a generic trust platform.     |
+-------------------------------------------------------------------------------------------------------------------+
```

---

## 3. Trust Architecture Tasks Ledger

| Priority | Ledger ID | Task / Principle | Milestone | Action & Scope Boundary |
| :--- | :--- | :--- | :--- | :--- |
| **P0** | `TRUST-EVIDENCE-001` | **Make Evidence Receipt a first-class product concept** | MMP-1.5 | **VERIFY existing UX/copy only.** Ensure Evidence Receipt and Evidence Package are treated as primary deliverables during UAT-29 unassisted testing. |
| **P0** | `TRUST-PROV-001` | **Make provenance visible and understandable** | MMP-1.5 | **VERIFY existing implementation.** Ensure CPAs easily understand: *Source A (1099-DA) vs. Source B (Tax Ledger) under 2025 Ruleset $\rightarrow$ Findings*. No blockchain or complex crypto jargon. |
| **P0** | `TRUST-SEM-001` | **Preserve strict trust-language boundaries** | MMP-1.5 | **RELEASE INVARIANT.** Enforce semantic separation: `Receipt Verified ≠ Tax Correctness Verified`, `Sources Agree ≠ Return Is Correct`, `Reviewed ≠ IRS Approved`. |
| **P0** | `TRUST-WORKFLOW-001` | **Protect the 5-step professional journey** | MMP-1.5 | **VERIFY via UAT-29 / UAT-22.** Validate flow: `INTAKE → RECONCILE → REVIEW → EVIDENCE → VERIFY`. Do not add a workflow engine. |
| **P1** | `TRUST-PRIMITIVES-001` | **Formalize reusable trust primitives** | MMP-2 | Architectural documentation and clean separation of core engines (`Intake`, `Reconcile`, `Review`, `Evidence`, `Verify`, `Explain`). |
| **P1** | `TRUST-EVIDENCE-UX-002` | **Evidence-history / audit timeline** | MMP-2.5 | Case timeline displaying source corrections and superseded runs without building complex VCS tooling for accountants. |
| **P1** | `TRUST-MULTIYEAR-001` | **Durable multi-year client record** | MMP-2.5 | Multi-year client hierarchy (`Client / 2025`, `Client / 2026`) establishing VaultBasis as a firm-wide system of record. |
| **P2** | `TRUST-WORKFLOW-COMP-001` | **Configurable practice workflows** | MMP-3+ | Reviewer assignment, partner sign-off thresholds, and intake routing (demand-driven). |
| **P2** | `TRUST-INTEGRATION-001` | **Complement external trust providers** | MMP-3+ | Integrate with external e-signature and identity verification platforms if requested; do not reinvent them. |
| **P2** | `TRUST-PLATFORM-001` | **Category expansion evaluation** | MMP-3+ | Evaluate positioning expansion toward *Digital Asset Tax Evidence System of Record* based on customer pull. |
| **OUT** | `TRUST-NONCORE-001` | **DO NOT BUILD: Generic trust features** | **NEVER** | Explicitly excludes e-signature infrastructure, identity verification, biometric KYC/KYB, digital seals, and cloud file custody. |

---

## 4. Semantic Claims Review Invariants (`TRUST-SEM-001`)

To prevent marketing, UI, or future AI capabilities from over-claiming software authority, the following invariant table is permanently established:

```text
+-----------------------------------------------+---------------------------------------------------------+
| CLAIMED / DISPLAYED TERM                      | STRICT PRODUCT BOUNDARY & EXCLUSION                     |
+-----------------------------------------------+---------------------------------------------------------+
| "Receipt Integrity Verified"                  | Proves cryptographic signature & schema adherence ONLY. |
|                                               | Does NOT prove tax correctness or legal compliance.     |
+-----------------------------------------------+---------------------------------------------------------+
| "Sources Reconciled / Match"                  | Proves mathematical equivalence between inputs ONLY.    |
|                                               | Does NOT assert that the underlying ledger is complete. |
+-----------------------------------------------+---------------------------------------------------------+
| "Practitioner Reviewed"                       | Proves human review action was recorded in receipt.     |
|                                               | Does NOT imply IRS audit immunity or endorsement.       |
+-----------------------------------------------+---------------------------------------------------------+
| "Deterministic Findings"                      | Proves repeatability under fixed ruleset code.          |
|                                               | Does NOT represent a formal legal or tax opinion.       |
+-----------------------------------------------+---------------------------------------------------------+
```
