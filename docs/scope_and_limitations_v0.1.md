# VaultBasis Supported Scope & Limitations

**Version:** v0.1  
**Release:** VaultBasis Edge v0.1.0 / RC3 Candidate

---

## 1. Supported Source File Formats

VaultBasis deterministically parses and reconciles the following source file formats:

- **IRS Form 1099-DA CSV**
  - Supported columns: Asset/Property, Date Sold, Date Acquired, Gross Proceeds, Cost Basis, and the basis-reporting indicator field.
  - 2025 transitional reporting: Within the supported profile, when the relevant basis-reporting indicator is absent or indicates that basis was not reported, VaultBasis does not silently interpret missing basis as zero. The applicable supported reconciliation state or unresolved treatment is applied under the declared semantics.

- **Koinly Capital Gains CSV Export**
  - Supported columns: Date, Asset, Amount/Quantity, Cost Basis, Proceeds, Gain/Loss, Date Acquired.

- **VaultBasis Canonical Reconciliation CSV**
  - Standardized 12-column format for direct ledger-to-broker comparisons.

---

## 2. How VaultBasis Evaluates Records

VaultBasis performs a bounded, deterministic comparison across supported source files using the following declared rules:

- **Matching:** Records are compared using the identifiers and normalization rules defined for the supported source profiles. Where required date, time, timezone, or other matching evidence is insufficient for a deterministic comparison, VaultBasis preserves the condition as unresolved rather than inventing missing information.
- **Arithmetic:** Supported numeric fields are processed using deterministic decimal semantics rather than binary floating-point arithmetic. Precision, validation, and presentation are governed by the declared semantic specification.
- **Outcome States:** Each transaction record is assigned one of 13 declared outcome states: Matched, Proceeds Difference, Basis Difference, Acquisition Date Difference, Disposition Date Difference, Missing from 1099-DA, Missing from Ledger, Ambiguous Match, Aggregated Line, Transfer Related, Reporting Scope Difference, Source Error Suspected, or Unresolved Data.
- **Missing Value Handling:** VaultBasis strictly distinguishes between a reported value of $0.00 (known zero), a field that was not provided in the source (not reported), and a field that is required for comparison but absent (unresolved).
- **Outcome Receipt:** A completed supported reconciliation can produce an Ed25519-signed Outcome Receipt containing a canonical payload digest. The receipt can be independently verified for payload integrity and signature authenticity. Verification does not determine tax correctness, source truth, legal compliance, or professional judgment.

---

## 3. What VaultBasis Does Not Determine

To preserve the professional authority of the filing practitioner, VaultBasis explicitly does **not**:

- **Determine tax correctness.** VaultBasis does not determine whether a taxpayer's tax position is legally correct, optimal, or acceptable to the IRS.
- **Determine legal compliance.** VaultBasis does not determine compliance with the Internal Revenue Code (e.g., IRC § 1012, § 1221, § 6045), Treasury Regulations, or state revenue laws.
- **Establish source truth.** A Matched outcome does not prove that either source file is authentic, complete, or free of error or fraud.
- **Determine safe harbor eligibility.** VaultBasis does not determine whether a taxpayer satisfies the statutory eligibility criteria for any safe harbor, election, or relief provision.
- **Determine lot-identification compliance or relief eligibility.** VaultBasis does not determine whether a taxpayer's specific identification, standing order, or other lot-identification method satisfies applicable Treasury Regulations, IRS guidance, or temporary relief provisions.
- **Assign Form 8949 tax codes.** VaultBasis does not assign tax reporting codes or prepare tax returns.
- **Replace professional judgment.** VaultBasis does not replace the professional due diligence, interpretation, or signature of the CPA, Enrolled Agent, or Tax Attorney.

---

## 4. What Is Not Supported

The following capabilities are outside the scope of this release:

- Ingestion of PDF statements or scanned documents.
- Real-time automated synchronization via exchange or wallet APIs.
- Automated tax-lot selection (HIFO, FIFO, or Specific Identification optimization).
- Wallet-level basis re-allocation.
- Automated tax return filing or Form 8949 preparation.
- AI-generated or heuristic tax determinations.
- Automated deletion or modification of ingested source files.

---

## 5. Local Processing & Record Retention

VaultBasis Edge is designed to process supported evidence locally within the declared application boundary. VaultBasis does not provide cloud backup or archival storage for source evidence or Outcome Receipts as part of this release.

Users remain responsible for retaining source records, workpapers, Outcome Receipts, and other documentation required for their professional, legal, regulatory, or tax obligations. VaultBasis does not determine the retention period applicable to a particular taxpayer, practitioner, engagement, or record.

Where a taxpayer relies on a particular safe harbor, election, relief provision, or other tax rule, the taxpayer and practitioner remain responsible for satisfying and documenting the applicable requirements.
