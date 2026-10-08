# VaultBasis Known Limitations & Scope Boundaries
**Document ID:** VB-SPEC-LIMITS-001  
**Classification:** NORMATIVE  
**Authority:** Core Engine Lead / Tax Domain Authority  
**Status:** ACTIVE  
**Applies To:** VaultBasis Edge v1.5.0 (MMP-1.5)  
**Last Reviewed:** 2026-10-08  

---

## 1. Supported Tax Scenarios & Jurisdictions

| Feature / Dimension | Supported in v1.5.0 | Scope Boundary & Policy |
|---|---|---|
| **Tax Jurisdiction** | United States (IRS) Only | Non-US tax jurisdictions (HMRC, CRA, ATO) are not supported in 1.5.0. |
| **Tax Year Calibration** | Tax Year 2025 | Calibration ruleset `VB_US_1099DA_2025_R1`. Prior tax years can be processed under 2025 reconciliation grammar. |
| **IRS Forms Covered** | Form 1099-DA & Form 8949 | Generates reconciliation evidence and Form 8949 worksheet exports. Form 1040 Schedule D generation is handled by external tax preparation software. |
| **E-Filing Submission** | Out of Scope | VaultBasis is a reconciliation and evidence assurance engine; it does not transmit returns directly to the IRS. |

---

## 2. Ingestion & Data Source Scope

| Source Type | Supported Formats | Limitations & Handling |
|---|---|---|
| **Broker Form 1099-DA** | CSV, PDF (Standard Broker Layouts) | Digital/scanned image PDFs without extractable text layers require OCR pre-processing. |
| **Client Ledgers** | Koinly CSV, Coinbase Reports, Kraken Ledgers, Generic CSV | Bespoke proprietary CSVs with custom column syntax require mapping to the standard 6-column generic schema. |
| **Data Size per Case** | Up to 100,000 transactions per case | Cases exceeding 100k rows should be segmented by asset or account for optimal desktop memory footprint. |

---

## 3. Runtime & Network Architecture Boundaries

| Dimension | Supported Architecture | Intentional Limitation |
|---|---|---|
| **Deployment Model** | Local Single-Seat Desktop Runtime | No cloud multi-tenant backend; no central server synchronization. |
| **Network Egress** | Zero Network Egress | The core engine operates 100% air-gapped without internet access. |
| **Multi-Seat Collaboration** | File-based Evidence Sharing | Team collaboration is achieved by transferring exported cryptographic receipts (`.json`) or case bundles, not live simultaneous database access. |
| **License Provisioning** | Offline Ed25519 Token | Activation does not call a central DRM licensing server. |

---

## 4. Verification & Cryptographic Guarantees

* **Receipt Authenticity:** Standalone verifier ([`apps/verifier/verify_receipt.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/apps/verifier/verify_receipt.py)) guarantees that the receipt was issued by the installation key and that no row, amount, or hash has been altered since signing.
* **Tax Advice Disclaimer:** Verification confirms mathematical and evidentiary consistency between provided broker 1099-DA files and client ledgers. It does not constitute legal or tax advice, nor does it certify the underlying factual truth of broker records.
