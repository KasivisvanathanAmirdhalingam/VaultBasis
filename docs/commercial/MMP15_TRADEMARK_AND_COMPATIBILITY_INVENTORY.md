# VaultBasis MMP-1.5 Third-Party Trademark & Compatibility Inventory (LEGAL-008)

**Document ID:** `MMP15-TM-INVENTORY-001` (Control Ref: `LEGAL-008` under `MMP15-LEGAL-RISK-QUAL-001`)  
**Status:** `PRE-LAUNCH IMPLEMENTATION PASS`  
**Purpose:** Comprehensive inventory of all third-party commercial brand names and government form identifiers across customer-facing surfaces to ensure nominative fair use compliance.

---

## 1. Third-Party Mark Inventory Table

| Mark / Identifier | Surface(s) | Exact Text Context | Purpose | Logo Used? | Compatibility Claim? | Affiliation Implied? | Customer Facing? | Disposition |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **IRS Form 1099-DA** | Marketing, Edge UI, Schemas, Docs | *"Reconcile Form 1099-DA Against Client Crypto Tax Records"* | Regulatory Form Subject | **NO** | YES (Parses Form 1099-DA CSV exports) | **NO** | YES | **APPROVED — NOMINATIVE FAIR USE** |
| **Koinly** | Marketing (`/`), Edge UI, Sample data | *"Import format: Koinly Capital Gains Report CSV"* | File Format Compatibility | **NO** | YES (Parses Koinly CSV exports) | **NO** | YES | **APPROVED — FORMAT COMPATIBILITY ONLY** |
| **CoinTracker** | Connectors, Docs, Verifier schema | *"Import format: CoinTracker Tax Report CSV"* | File Format Compatibility | **NO** | YES (Parses CoinTracker CSV exports) | **NO** | YES | **APPROVED — FORMAT COMPATIBILITY ONLY** |
| **Apple / macOS** | Download page, Release notes | *"VaultBasis Edge for macOS (Apple Silicon arm64)"* | Operating System Platform | **NO** | YES (Platform architecture) | **NO** | YES | **APPROVED — PLATFORM IDENTIFIER** |
| **Microsoft / Windows** | Download page, Release notes | *"VaultBasis Edge for Windows (x64)"* | Operating System Platform | **NO** | YES (Platform architecture) | **NO** | YES | **APPROVED — PLATFORM IDENTIFIER** |
| **Paddle** | Checkout modal, Terms of Service | *"Payments securely processed via Paddle (Merchant of Record)"* | Payment Processing Disclosure | **NO** | YES (Commercial gateway) | **NO** | YES | **APPROVED — REQUIRED LEGAL DISCLOSURE** |

---

## 2. Nominative Fair Use Safeguards & Policy

1. **Zero Third-Party Logos:** No proprietary logos, badges, or brand marks belonging to Koinly, CoinTracker, Apple, Microsoft, or the IRS are used on marketing or product interfaces.
2. **Descriptive Phrasing Standard:** All UI and documentation references are strictly descriptive of file formats (e.g., *"Import format: Koinly CSV"*) rather than implying partnership or certification (e.g., *"Koinly Certified Partner"* is strictly prohibited).
3. **Published Trademark Notice:** The statutory fair use notice is published in the marketing footer and Terms of Service:
   > *"IRS Form 1099-DA is a tax form published by the Internal Revenue Service. Koinly, CoinTracker, and other referenced third-party product names are trademarks of their respective owners. Reference to them is solely for descriptive format compatibility and does not imply affiliation, sponsorship, or endorsement."*
