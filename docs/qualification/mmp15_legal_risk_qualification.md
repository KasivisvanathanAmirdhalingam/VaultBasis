# MMP15-LEGAL-RISK-QUAL-001: Legal, Regulatory, Contractual & Claims Qualification Ledger

**Document ID:** `MMP15-LEGAL-RISK-QUAL-001`  
**Parent Milestone:** Pre-Sign / Commercial Distribution Authorization (Feeds Canonical `PROD-GATE-18`)  
**Status:** `IN PROGRESS`  
**Governance Note:** This document tracks legal, regulatory, contractual, and claims controls. It does **not** create a new production gate (`PROD-GATE-19`), but directly qualifies the legal, commercial, and distribution prerequisites feeding release authorization.

---

## 1. Status Vocabulary & Governance Rules

The following strictly defined operational vocabulary governs this ledger:

| Status | Meaning |
| :--- | :--- |
| `PASS / CLOSED` | Requirement fully satisfied with verified implementation, test evidence, approved copy, and counsel sign-off where required. |
| `FAIL / REMEDIATE` | Control failed validation or an actionable legal/risk violation was identified requiring engineering or copy remediation. |
| `BLOCKED — EXTERNAL DEPENDENCY` | Blocked on an external third party (e.g., Microsoft Trusted Signing, Paddle, external corporate registrar). |
| `PENDING — SCHEDULED` | Engineering or operational activity queued for execution in sequence. |
| `PENDING — COUNSEL REVIEW` | Formal legal review packet prepared; awaiting qualified legal counsel written determination. |

> **Governance Rule:** Subjective conclusions such as `LOW RISK`, `MINIMAL`, `IMMUNE`, `LEGALLY PROTECTED`, or `COMPLIANT` are prohibited as closure states.

---

## 2. Canonical Legal, Regulatory & Claims Risk Ledger

| ID | Priority | Control / Risk Area | Owner | Initial Status | Closure Evidence / DoD | Release Effect |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| **LEGAL-001** | **P0** | **IRC § 7216 Applicability & Taxpayer Data Boundary** | Founder + U.S. Tax/Privacy Counsel | `PENDING — COUNSEL REVIEW` | Written counsel disposition on VaultBasis Edge software-provider status, support, licensing, and consent implications. | GA Blocker |
| **LEGAL-002** | **P0** | **GLBA / FTC Safeguards Rule Scope** | Founder + Privacy Counsel | `PENDING — COUNSEL REVIEW` | Written entity/activity applicability determination and review of local-first data-flow boundaries. | GA Blocker |
| **LEGAL-003** | **P0** | **Terms of Service, Privacy Policy & Governing Law** | Founder + Counsel (Developer Implements) | `PENDING — COUNSEL REVIEW` | Counsel-approved production Terms/Privacy; exact France EURL legal identity; governing law/venue; liability caps; versioned production copies. | GA Blocker |
| **LEGAL-004** | **P0** | **Pre-Purchase Clickwrap & Contract Formation** | Developer + Founder | `PRE-LAUNCH TECHNICAL QUALIFICATION PASS`<br>`(PADDLE PRODUCTION CHECKOUT PENDING)` | 15-point server-authoritative test suite verified in `test_clickwrap_contract_formation.py`; independent `acceptance_id` generated; direct-link bypass blocked; order linked to prior acceptance with zero taxpayer data. | Commerce / GA Blocker |
| **LEGAL-005** | **P0** | **Privacy & Marketing Claims Accuracy** | Developer + Founder | `PRE-LAUNCH IMPLEMENTATION PASS`<br>`(FINAL GA SURFACE VERIFICATION PENDING)` | Repository-wide sweep completed; ungrounded absolute claims prohibited; canonical bounded claim enforced (`CLAIM-LOCAL-01`). GA closure requires production deployment verification. | GA Claims Blocker |
| **LEGAL-006** | **P0** | **Support-Channel Taxpayer Data Boundary** | Developer + Founder + Counsel | `PRE-LAUNCH IMPLEMENTATION PASS`<br>`(FINAL SUPPORT-SURFACE VERIFICATION PENDING)` | Customer-facing instruction verified on contact/privacy surfaces strictly barring transmission of client tax records; zero auto-attachment. GA closure requires production support ecosystem check. | GA Blocker |
| **LEGAL-007** | **P1** | **Open Source (OSS) License Compliance & SBOM** | Developer | `PRE-SIGN OSS QUALIFICATION PASS`<br>`(FINAL SIGNED-ARTIFACT VERIFICATION PENDING)` | Artifact-bound SBOM, dependency classification, and third-party notices generated (`OSS_LICENSE_LEDGER.md`, `THIRD_PARTY_NOTICES.md`). Final closure requires verification against exact signed packages. | Signing / Artifact Blocker |
| **LEGAL-008** | **P1** | **Trademark & Compatibility Representations** | Founder/Counsel + Developer | `PRE-LAUNCH IMPLEMENTATION PASS`<br>`(COUNSEL REVIEW PENDING)` | Inventory of Koinly/CoinTracker/IRS references documented in `MMP15_TRADEMARK_AND_COMPATIBILITY_INVENTORY.md`; descriptive format compatibility wording only; statutory fair use notice published. | GA Content Blocker |
| **LEGAL-009** | **P1** | **Professional & Tax-Advice Positioning** | Developer + Founder + Counsel | `PRE-LAUNCH IMPLEMENTATION PASS`<br>`(COUNSEL REVIEW PENDING)` | `tax_correctness: NOT_DETERMINED` enforced; zero IRS approval/endorsement or audit-proof claims; permanent semantic invariants protected: Receipt Integrity Verified ≠ Tax Correctness Verified, Sources Agree ≠ Return Is Correct, Practitioner Reviewed ≠ IRS Approved, Deterministic ≠ Legally Correct, Evidence Package ≠ Legal Opinion. | Legal / Claims Blocker |
| **LEGAL-010** | **P1** | **Production Claims Evidence Ledger** | Developer | `PRE-LAUNCH IMPLEMENTATION PASS`<br>`(GA CONTENT VERIFICATION PENDING)` | Complete control plane established in `docs/qualification/mmp15_release_claims_ledger.md` mapping all claims to technical evidence, approval requirements, and revalidation triggers. | Launch Content Blocker |
| **LEGAL-011** | **P1** | **France EURL ↔ U.S. Customer Contracting Consistency** | Founder + Cross-Border Counsel | `PENDING — COUNSEL REVIEW` | Legal seller entity name, registered address, invoicing identity, Paddle merchant representation, Terms, Privacy, refund/support pages all consistent. | GA Blocker |
| **LEGAL-012** | **P1** | **Commercial Consistency (Pricing / Renewal / Refund)** | Founder + Counsel + Developer | `PRE-LAUNCH IMPLEMENTATION PASS`<br>`(PADDLE LIVE + COUNSEL REVIEW PENDING)` | Cross-surface matrix verified in `MMP15_COMMERCIAL_CONSISTENCY_MATRIX.md`; 0 contradictions between pricing, Terms, Paddle catalog, license engine, and dashboard representations. | Commerce Blocker |
| **LEGAL-013** | **P1** | **Security & Privacy Incident Response Protocol** | Founder + Developer + Counsel | `PRE-LAUNCH IMPLEMENTATION PASS`<br>`(COUNSEL REVIEW PENDING)` | Technical incident response runbook completed in `docs/runbooks/technical_incident_response.md`; system inventories, data classes, log sources, credential rotation, and containment protocols defined; counsel owns notification and legal escalation. | Operational Readiness Blocker |
| **LEGAL-014** | **P2** | **IP Ownership & Contributor Chain-of-Title** | Founder | `PENDING — SCHEDULED` | Documentation confirming company owns all source, branding, copy, and commissioned work; contractor assignments archived. | GA Blocker (if gap found) |
| **LEGAL-015** | **P2** | **Export, Sanctions & Distribution Eligibility** | Founder + Counsel / Provider | `PENDING — COUNSEL REVIEW` | Sales and distribution territory policies aligned with Paddle and applicable export regulations. | Distribution Blocker |
| **LEGAL-016** | **P2** | **Accessibility & Customer-Facing Web Legal Exposure** | Developer + Founder / Counsel | `PRE-LAUNCH IMPLEMENTATION PASS` | Practical WCAG 2.1 AA baseline verified in `docs/qualification/mmp15_accessibility_baseline.md`; keyboard navigation, visible focus, ARIA labels, semantic hierarchy, and contrast verified across marketing web and dashboard. | Risk-Based Quality Check |
| **LEGAL-017** | **P2 / FUTURE** | **MMP-2 AI Legal & Privacy Review** | Founder + Counsel + Developer | `DEFERRED — MMP2` | Fresh legal and privacy review before any AI production authorization (data flows, explanations, model provider terms). | MMP-2 Blocker (Not MMP-1.5) |

---

## 3. Counsel Review Packet Requirements

For items marked `PENDING — COUNSEL REVIEW` (`LEGAL-001`, `LEGAL-002`, `LEGAL-003`, `LEGAL-011`, `LEGAL-013`, `LEGAL-015`), engineering produces a structured Counsel Packet containing:
1. **Specific Legal Questions:** Formulated concisely for specialized tax/privacy counsel.
2. **Current Product Behavior & Data Flow:** Explicit local vs cloud boundary description.
3. **What VaultBasis Does and Does Not Do:** Scope limitations and deterministic engine definition.
4. **Current Proposed Copy & Disclaimers:** Versioned draft terms, notices, and UI strings.
5. **Downstream Technical Consequences:** Clear statement of engineering changes resulting from counsel's determination.

---

## 4. Frozen Canonical Privacy Claim

All customer-facing and documentation surfaces must use the established bounded claim:

> **"VaultBasis Edge processes client reconciliation and evidence locally on your computer. Client tax records and ledger data are not uploaded to VaultBasis cloud services for normal Edge case processing."**
