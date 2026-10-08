# VaultBasis Authoritative Documentation Index
**Document ID:** VB-DOC-INDEX-001  
**Classification:** NORMATIVE  
**Authority:** Release Engineering Authority  
**Target Release:** VaultBasis Edge v1.5.0 (MMP-1.5)  
**Status:** ACTIVE  
**Last Reviewed:** 2026-10-08  

---

## 1. Documentation Authority & Evidence Status Taxonomy

Every document in the VaultBasis project belongs to one of six explicit authority classifications and tracks an evidence verification state:

### Authority Classifications
| Classification | Meaning & Policy | Conflict Precedence |
|---|---|---|
| **NORMATIVE** | Defines system requirements, semantics, schemas, security boundaries, and immutable gate standards. Changes require formal review and versioning. | **1 (Highest)** |
| **OPERATIONAL** | Defines executable procedures, runbooks, maintenance tasks, signing ceremonies, and recovery workflows. Must be periodically tested and verified. | **2** |
| **CUSTOMER-FACING** | Guides, documentation, and trust materials presented directly to CPAs, tax professionals, IT reviewers, and website visitors. | **3** |
| **EVIDENCE** | Machine-generated or audit-recorded test outputs, cryptographic proofs, scan reports, and qualification summaries. Strictly immutable once created. | **4** |
| **REFERENCE** | Architecture summaries, ADRs, conceptual explanations, and supporting background technical documentation. | **5** |
| **HISTORICAL** | Superseded artifacts, legacy milestone records, obsolete qualification runs, and deprecated schemas preserved for audit integrity. | **6 (Lowest)** |

### Evidence Verification States
* **`DRAFT`**: Document under active development; not yet fully aligned with code.
* **`IMPLEMENTATION_ALIGNED`**: Technically reviewed and confirmed to accurately describe current codebase.
* **`EXECUTED`**: Operational runbook or procedure successfully executed in target environment.
* **`ARTIFACT_VERIFIED`**: Validated directly against candidate binary artifacts (DMG / EXE).
* **`FROZEN`**: Normative specification locked for external compatibility.
* **`SUPERSEDED`**: Replaced by a newer revision or artifact digest.

---

## 2. Master Document Directory

### 2.1 Release Governance & Qualification
| Document Path | Title / Purpose | Classification | Applies To | Evidence Status | Authority |
|---|---|---|---|---|---|
| [`docs/qualification/canonical_prod_gates.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/qualification/canonical_prod_gates.md) | Canonical Production Release Gates (PROD-GATE-01..18) | **NORMATIVE** | v1.5.0+ | **FROZEN** | Release Authority |
| [`docs/qualification/mmp15_traceability_matrix.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/qualification/mmp15_traceability_matrix.md) | End-to-End Requirement → Implementation → Test → Gate Matrix | **NORMATIVE** | v1.5.0-rc3 | **IMPLEMENTATION_ALIGNED** | Release Authority |
| [`docs/qualification/mmp15_release_claims_ledger.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/qualification/mmp15_release_claims_ledger.md) | Public Release Claims & Evidence Linkage Ledger | **NORMATIVE** | v1.5.0-rc3 | **IMPLEMENTATION_ALIGNED** | Product / Compliance |
| [`docs/qualification/MMP15_GOLDEN_JOURNEY_QUALIFICATION_PROTOCOL.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/qualification/MMP15_GOLDEN_JOURNEY_QUALIFICATION_PROTOCOL.md) | Standard Qualification Protocol for 1099-DA Reconciliation | **OPERATIONAL** | v1.5.0-rc3 | **ARTIFACT_VERIFIED** (Mac) | Quality Engineering |
| [`docs/definition_of_done.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/definition_of_done.md) | Engineering Definition of Done (4-Question DoD & Docs Invariant) | **NORMATIVE** | All PRs/Tasks | **IMPLEMENTATION_ALIGNED** | Lead Architect |
| [`docs/mmp15_task_ledger.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/mmp15_task_ledger.md) | MMP-1.5 Release Execution Task Ledger | **OPERATIONAL** | v1.5.0 | **IMPLEMENTATION_ALIGNED** | Release Ops |
| [`docs/RELEASE_NOTES_1.5.0.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/RELEASE_NOTES_1.5.0.md) | Normative Release Notes for v1.5.0-rc3 | **CUSTOMER-FACING** | v1.5.0-rc3 | **IMPLEMENTATION_ALIGNED** | Product Lead |
| [`docs/KNOWN_LIMITATIONS.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/KNOWN_LIMITATIONS.md) | Explicit Scope Boundaries & System Constraints | **NORMATIVE** | v1.5.0 | **FROZEN** | Core Engine Lead |

### 2.2 Core Product & Reconciliation Semantics
| Document Path | Title / Purpose | Classification | Applies To | Evidence Status | Authority |
|---|---|---|---|---|---|
| [`docs/reconciliation-semantics-v0.1.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/reconciliation-semantics-v0.1.md) | Exact Decimal Arithmetic, Trailing Zero, & Matching Grammar | **NORMATIVE** | Semantics v0.1 | **FROZEN (v0.1)** | Core Engine Lead |
| [`schemas/canonical/transaction.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/schemas/canonical/transaction.py) | Canonical Transaction Data Model & Field Normalization | **NORMATIVE** | v1.5.0 | **IMPLEMENTATION_ALIGNED** | Core Engine Lead |
| [`schemas/receipt/receipt-v0.1.json`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/schemas/receipt/receipt-v0.1.json) | Normative JSON Schema for RFC 8785 Ed25519 Receipts | **NORMATIVE** | Receipt Schema v0.1 | **FROZEN (v0.1)** | Protocol Lead |
| [`docs/scope_and_limitations_v0.1.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/scope_and_limitations_v0.1.md) | Supported Tax Scenarios & Unsupported Edge Cases | **NORMATIVE** | Tax Year 2025 | **IMPLEMENTATION_ALIGNED** | Tax Domain Lead |

### 2.3 Security, Runtime Boundary & Threat Model
| Document Path | Title / Purpose | Classification | Applies To | Evidence Status | Authority |
|---|---|---|---|---|---|
| [`docs/security/threat-model.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/security/threat-model.md) | Localhost Boundary, Host Header, Origin & Capability Threat Model | **NORMATIVE** | Edge Runtime | **IMPLEMENTATION_ALIGNED** | Security Lead |
| [`docs/enterprise/VaultBasis_IT_Deployment_and_Security_Profile.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/enterprise/VaultBasis_IT_Deployment_and_Security_Profile.md) | Enterprise IT Security & Deployment Profile | **CUSTOMER-FACING** | v1.5.0-rc3 | **IMPLEMENTATION_ALIGNED** | Security Lead |
| [`docs/commercial/VaultBasis_Subprocessor_Register.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/commercial/VaultBasis_Subprocessor_Register.md) | Subprocessor Register & Zero Data Transfer Policy | **NORMATIVE** | Privacy Policy | **IMPLEMENTATION_ALIGNED** | Compliance Lead |

### 2.4 Commercial & Licensing Policy
| Document Path | Title / Purpose | Classification | Applies To | Evidence Status | Authority |
|---|---|---|---|---|---|
| [`docs/commercial/license_token_v1.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/commercial/license_token_v1.md) | Offline Ed25519 License Token Specification (v1.0) | **NORMATIVE** | License Protocol v1.0 | **FROZEN (v1.0)** | Commercial Lead |
| [`docs/commercial/pricing_and_capacity_v1.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/commercial/pricing_and_capacity_v1.md) | Commercial Tiers, Pricing Cards & Case Capacity Invariants | **NORMATIVE** | Catalog v1.0 | **IMPLEMENTATION_ALIGNED** | Commercial Lead |
| [`docs/commercial/design_partner_program.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/commercial/design_partner_program.md) | Early CPA Design Partner Program Specifications | **OPERATIONAL** | Early Access | **IMPLEMENTATION_ALIGNED** | Founder |

### 2.5 Operational Runbooks & Procedures
| Document Path | Title / Purpose | Classification | Applies To | Evidence Status | Authority |
|---|---|---|---|---|---|
| [`docs/runbooks/release_signing.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/runbooks/release_signing.md) | Windows Authenticode & macOS Developer ID / Notary Runbook | **OPERATIONAL** | Platform Signing | **IMPLEMENTATION_ALIGNED** (Pre-Execution) | Release Ops |
| [`docs/runbooks/device_replacement_runbook.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/runbooks/device_replacement_runbook.md) | CPA Device Migration, Key Re-Pairing & License Reissue | **OPERATIONAL** | Support Operations | **IMPLEMENTATION_ALIGNED** | Support Lead |
| [`docs/runbooks/backup_restore.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/runbooks/backup_restore.md) | Consistent Online Backup & Verified Restore Runbook | **OPERATIONAL** | SQLite WAL | **IMPLEMENTATION_ALIGNED** | Persistence Lead |
| [`docs/runbooks/release_revocation.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/runbooks/release_revocation.md) | Trust Domain Separation & Emergency Incident Runbook | **OPERATIONAL** | Security Incidents | **IMPLEMENTATION_ALIGNED** | Security Lead |

### 2.6 Customer Documentation & User Guides
| Document Path | Title / Purpose | Classification | Applies To | Evidence Status | Authority |
|---|---|---|---|---|---|
| [`docs/Edge_Quick_Start.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/Edge_Quick_Start.md) | CPA First-Run Quick Start Guide | **CUSTOMER-FACING** | v1.5.0-rc3 | **IMPLEMENTATION_ALIGNED** | Support Lead |
| [`docs/Independent_Verifier_Guide.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/Independent_Verifier_Guide.md) | Auditor Offline Receipt Verification Guide | **CUSTOMER-FACING** | Verifier CLI v0.1 | **ARTIFACT_VERIFIED** | Tools Lead |
| [`docs/L2_Explanations.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/L2_Explanations.md) | Reconciliation Finding Explanations for Tax Practitioners | **CUSTOMER-FACING** | Tax Year 2025 | **IMPLEMENTATION_ALIGNED** | Tax Domain Lead |

---

## 3. Continuous Documentation Invariants

1. **Atomic Updates:** Every pull request or code commit that alters runtime behavior, security controls, packaging, data schemas, or commercial rules **must** update the corresponding authoritative document in the same change set.
2. **Zero Undocumented Behavior:** If an implementation behaves differently from its governing document, either the bug must be fixed or the normative specification deliberately revised and approved. No accidental bug may be documented as intended behavior without explicit domain authority sign-off.
3. **Immutability of Historical Records:** Historical candidate qualification evidence, superseded release manifests, and retired schemas are immutable and must be classified as `HISTORICAL` or `SUPERSEDED` rather than edited in place.
