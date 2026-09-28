# VaultBasis MMP-1 Supported Scope & Limitations

**Artifact Reference:** `docs/scope_and_limitations_v0.1.md`  
**Specification Version:** v0.1 (FROZEN / NORMATIVE)  
**Target Release:** VaultBasis Edge v0.1.0-RC2 / Evidence Contract v0.1  

---

## 1. Supported Input Profiles

Within Evidence Contract v0.1, VaultBasis deterministically parses and reconciles the following declared source profiles:

1. **IRS Form 1099-DA Preview CSV Profile (`v0.1`)**  
   - Header fields supported: Asset/Property, Date Sold (Box 1e), Date Acquired (Box 1d), Gross Proceeds (Box 1f), Cost Basis (Box 1g), Box 2 (Basis Reported / Covered).
   - Strict 2025 transitional reporting scope awareness (Box 2 `= "NO"` / omitted basis classified as `REPORTING_SCOPE_DIFFERENCE` rather than corrupted zero-basis).

2. **Koinly Capital Gains CSV Export Profile (`v0.1`)**  
   - Header fields supported: Date, Asset, Amount/Quantity, Cost Basis, Proceeds, Gain/Loss, Date Acquired.

3. **VaultBasis Canonical Reconciliation CSV Profile (`v0.1`)**  
   - Standardized 12-column normalized format for direct ledger-to-broker comparisons.

---

## 2. Declared Evaluation Semantics

VaultBasis executes bounded deterministic comparison across supported profiles using the following rules:

* **Matching Predicate:** Matches transaction line items across sources by `(Asset Ticker + Normalized UTC Disposition Timestamp)`.
* **Arithmetic Precision:** Uses arbitrary-precision `Decimal` arithmetic. Zero floating-point drift.
* **13 Declared Outcome States:** Evaluates each record into one of 13 normative states:
  `MATCHED`, `PROCEEDS_DIFFERENCE`, `BASIS_DIFFERENCE`, `ACQUISITION_DATE_DIFFERENCE`, `DISPOSITION_DATE_DIFFERENCE`, `MISSING_FROM_1099DA`, `MISSING_FROM_LEDGER`, `AMBIGUOUS_MATCH`, `AGGREGATED_LINE`, `TRANSFER_RELATED`, `REPORTING_SCOPE_DIFFERENCE`, `SOURCE_ERROR_SUSPECTED`, `UNRESOLVED_DATA`.
* **Tri-State Fact Handling:** Strictly distinguishes between:
  - `$0.00` → **KNOWN ZERO** (Explicitly reported as $0.00 in source records).
  - `—` → **NOT PROVIDED** (Omitted or not reported under 2025 transitional rules).
  - `?` → **UNRESOLVED** (Required for deterministic comparison but missing from record).
* **Cryptographic Attestation:** Produces a portable, Ed25519-signed Outcome Receipt with canonical SHA-256 payload digest.

---

## 3. What VaultBasis Does Not Determine

To maintain strict legal defensibility and preserve the professional authority of the filing practitioner, VaultBasis explicitly does **not**:

* **Determine Tax Correctness:** VaultBasis does not determine whether a taxpayer's tax position is legally correct, optimal, or acceptable to the IRS.
* **Determine Legal Compliance:** VaultBasis does not determine compliance with the Internal Revenue Code (e.g., IRC § 1012, § 1221, § 6045), Treasury Regulations, or state revenue laws.
* **Establish Source Truth:** A successful comparison or `MATCHED` outcome does not prove that either source file is authentic, complete, or free of fraud.
* **Determine Safe Harbor Eligibility:** VaultBasis does not determine whether a taxpayer satisfies the statutory eligibility criteria for Revenue Procedure 2024-28.
* **Determine Lot-Selection Validity:** VaultBasis does not assess whether a standing order or specific identification satisfies Notice 2026-20.
* **Assign Form 8949 Tax Codes:** VaultBasis does not assign tax reporting codes (e.g., Code "O" or Code "H") or prepare tax returns.
* **Replace Professional Judgment:** VaultBasis never replaces the professional due diligence, interpretation, and signature of the CPA, Enrolled Agent, or Tax Attorney.

---

## 4. Unsupported in MMP-1

The following capabilities are explicitly outside the scope of MMP-1:

* Ingestion of unparsed, raw PDF statements or scanned documents.
* Real-time automated synchronization via third-party exchange or wallet APIs.
* Autonomous HIFO/FIFO/Specific ID tax-lot optimization.
* Wallet-level basis re-allocation engines.
* Automated tax return filing or Form 8949 XML generation.
* AI-derived, LLM-generated, or heuristic tax determinations.
* Automated deletion or mutation of ingested source files.

---

## 5. Record Retention Obligation

VaultBasis operates as a 100% offline, local edge tool. It does not perpetually store, backup, or transmit client data to the cloud. Pursuant to IRS Revenue Procedure 2024-28 and general Treasury record-keeping requirements, **the filing practitioner and taxpayer retain sole responsibility for archiving source files, workpaper summaries, and signed Outcome Receipts in their local document retention systems.**
