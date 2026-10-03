# MMP15-COMM-001 — Professional Pricing & Capacity Architecture

> **Status:** FUTURE DESIGN RECORD (MMP-1.5 SPECIFICATION) — NOT IMPLEMENTED IN MMP-1.1

## 1. Commercial Thesis
VaultBasis is designed as professional assurance software for CPA and EA practices, not a consumer SaaS or monthly per-user subscription.

The economic value of VaultBasis corresponds directly to **professional assurance capacity and evidence work performed**.

---

## 2. Invariants
- **VB-COMM-INV-001 (Bounded Commercial Capacity):** No VaultBasis commercial tier may promise "unlimited" cases, clients, reconciliations, or receipts without explicit authorization. Unlimited models create revenue bleed and misalign incentives.
- **Verification is Never Metered:** Independent verification of an Outcome Receipt (via Offline Verifier or Web Verifier) must never consume paid case capacity. Receipt verification strengthens the network value of the receipt.
- **Reconciliation Re-runs:** Re-running a case with identical sources does not consume additional case capacity.

---

## 3. Commercial Tiers (Hypotheses to Validate)

| Tier | Target Persona | Structure | Included Capacity |
|---|---|---|---|
| **Essential Practice** | Solo practitioner / Boutique CPA | Annual Practice License | Included N completed reconciliation cases |
| **Practice** | Multi-preparer accounting firm | Annual Practice License | Higher included case capacity + reviewer workflows |
| **Firm / Enterprise** | Regional/National accounting firms | Annual Firm License | High volume capacity + multi-office management |
| **Capacity Blocks** | Any active tier | Add-on blocks | Incremental bundles of completed reconciliation cases |

---

## 4. Counting Events
- **Billable Event:** A reconciliation case is counted when a qualifying reconciliation reaches a completed/committed assurance state and issues an Outcome Receipt.
- **Non-Billable Events:** Opening cases, preflight readiness checks, viewing receipts, re-running identical sources, and verifying receipts.
