# VaultBasis Evidence Ontology v0.1 Research

**Status**: Post-Preview Architecture Candidate
**Date**: 2026-09-27

## 1. Architectural Philosophy

VaultBasis is not a tax calculation engine, and it is not an IRS compliance schema generator. It is an independent edge node that takes claims from independent systems, preserves their provenance, applies explicit deterministic rules, exposes disagreement and uncertainty, and produces a portable, independently verifiable outcome.

Therefore, the core architecture will evolve from the MMP-1 Evidence Contract into a formalized **VaultBasis Evidence Ontology**.

```text
                    EVIDENCE ONTOLOGY
                           │
       ┌───────────────────┼────────────────────┐
       ↓                   ↓                    ↓
   Source Evidence     Assertions         Regulatory Context
       │                   │                    │
       └──────────────┬────┘                    │
                      ↓                         │
               Transformations ←───────────────┘
                      ↓
                Reconciliation
                      ↓
              Bounded Finding
                      ↓
               Outcome Receipt
                      ↓
               Ed25519 Signature
                      ↓
          Independent Verification
```

This model separates raw evidence from subjective interpretation and isolates system inferences from regulatory constraints.

---

## 2. Evidence Primitives

Future versions of VaultBasis will formalize these primitives rather than encoding tax law directly into monolithic JSON schemas.

### A. EvidenceSource
Represents what VaultBasis actually received, preserving source integrity.
*Fields:* `evidence_id`, `evidence_type`, `source_system`, `source_format`, `source_filename`, `content_hash`, `ingested_at`, `parser_version`, `schema_version`.
*Examples:* Form 1099-DA PDF/CSV, Koinly export, CPA spreadsheet.

### B. AccountReference
Decouples identifiers from the legal definition of a "wallet."
*Fields:* `account_ref_id`, `source_account_identifier`, `identifier_type`, `custody_classification`, `network`, `parent_account_ref`, `source_system`, `classification_status`, `classification_basis`.
*Enums for `classification_status`:* `DECLARED`, `SOURCE_REPORTED`, `INFERRED`, `UNRESOLVED`.
*Reasoning:* VaultBasis can document that "Koinly calls these addresses Wallet A" without legally declaring "The IRS considers this xpub one wallet."

### C. AssetQuantity
Decouples source precision from internal normalization.
*Fields:* `asset_identifier`, `asset_identifier_scheme`, `quantity_raw`, `quantity_normalized`, `source_precision`, `normalization_rule`, `normalization_status`.
*Reasoning:* Form 1099-DA in 2026 supports up to 18 decimal places. Hardcoding precision by asset ticker is anti-fragile.

### D. TaxLotAssertion
Records subjective claims about tax lots, not absolute "truth."
*Fields:* `lot_ref`, `account_ref`, `asset`, `acquisition_time`, `acquisition_time_precision`, `quantity`, `basis`, `basis_currency`, `basis_source`, `holding_period_source`, `asserted_by`, `evidence_refs[]`.
*Reasoning:* Captures conflicting claims (e.g., Koinly asserts basis is $2800; broker asserts $1800) for deterministic reconciliation.

### E. DispositionAssertion
Records subjective claims about sales or transfers.
*Fields:* `disposition_ref`, `account_ref`, `asset`, `quantity`, `disposition_time`, `proceeds`, `transaction_identifier`, `claimed_lots[]`, `source_evidence_refs[]`.
*Reasoning:* Supports tracking claimed lot consumption without prematurely validating them against IRS approval criteria.

### F. RegulatoryContext
Versions regulatory interpretation separately from the evidence graph.
*Fields:* `regulatory_context_id`, `jurisdiction`, `authority`, `authority_version`, `tax_year`, `effective_from`, `effective_to`, `rule_refs[]`, `applicability_status`.
*Reasoning:* Protects the platform when guidance (e.g., Rev. Proc. 2024-28, Notice 2026-20) changes.

### G. Finding
The deterministically produced bounded outcome of reconciliation.
*Fields:* `finding_id`, `finding_type`, `source_assertion_a`, `source_assertion_b`, `semantic_rule`, `raw_delta`, `normalized_delta`, `resolution`, `reason_codes[]`, `evidence_refs[]`.
*Examples:* `MATCHED`, `BASIS_DIFFERENCE`, `PROCEEDS_DIFFERENCE`, `ACQUISITION_DATE_DIFFERENCE`, `REPORTING_SCOPE_DIFFERENCE`, `UNRESOLVED_DATA`.

---

## 3. Structural Concepts

### ProvenanceEdge
Every derived value must answer: *Where did you get this?* 
Explicit links (`derived_from`, `compared_with`, `normalized_by`, `classified_by`, `supported_by`, `supersedes`) transform flat JSON files into a verifiable evidence graph.

### AssertionType (Five Types of Truth)
A value's classification of truth must never be collapsed.
1. `SOURCE_REPORTED` (e.g., Coinbase reports acquisition date X)
2. `USER_DECLARED` (e.g., Taxpayer groups addresses into Wallet A)
3. `DERIVED` (e.g., VaultBasis calculates a delta of $1,000)
4. `INFERRED` (e.g., VaultBasis matches two records via semantic rules)
5. `REGULATORY_INTERPRETATION` (e.g., A rule maps a state to a regulatory mandate)
6. `UNRESOLVED` (e.g., Conflicting or missing information)

### ExternalTimestampEvidence
Notice 2026-20 requires contemporaneous record keeping. A JSON timestamp like `"log_creation_timestamp": "2025-08-10T11:15:30Z"` only proves a `DECLARED_RECORD_TIME`. Ed25519 signatures and SHA-256 hashes prove integrity and origin, but not chronologic existence. Future chronologic proof must be explicitly segregated:
*Fields:* `timestamp_assertion`, `timestamp_authority`, `timestamp_token`, `timestamp_evidence_hash`, `verification_status`.

---

## 4. Candidate Future Assurance Cases

Based on this ontology, VaultBasis is positioned to offer targeted, deterministic verification workflows beyond basic reconciliation. These are purely independent verification problems—not tax calculation or advice.

1. **Wallet Isolation Verification**: Verify if a tax software correctly isolated basis during a disposal (Cross-Account Basis Leak detection).
2. **Basis Conservation Verification**: Verify that the sum of post-allocation basis exactly matches pre-migration unused basis.
3. **Transfer Basis Continuity**: Verify that internal transfers between accounts conserve asset quantity, basis, and acquisition metadata without resetting holding periods.
4. **Broker/Ledger Lot Divergence**: Highlight discrepancies between 1099-DA assertions and taxpayer ledger assertions (Notice 2026-20), presenting the variance, the semantic rules applied, and the supporting evidence for both sides.
5. **Safe Harbor Allocation Evidence Review**: Ensure the 12/31/2024 physical inventory snapshots map correctly to historic unused tax lots under Rev. Proc. 2024-28.
6. **Contemporaneous-Record Evidence Review**: Verify that claimed lot disposals correctly reference declared timing records and cryptographic seals to defend against default FIFO imposition.
