# MMP15 Counsel Review Packet: Legal, Regulatory & Commercial Qualification

**Target Entity:** VaultBasis (French EURL)  
**Target Market:** United States Certified Public Accountants (CPAs), Enrolled Agents (EAs), and Digital Asset Tax Practitioners  
**Product:** VaultBasis Edge v1.5.0-rc3 (macOS arm64 / Windows x64 desktop software) & vaultbasis.com (public marketing & independent verifier)  
**Prepared For:** U.S. Tax, Privacy, and Cross-Border Technology Legal Counsel  
**Date:** October 2026  

---

## 1. Executive Summary & Product Architecture

VaultBasis Edge is a desktop software application designed for tax professionals reconciling cryptocurrency transaction data. Specifically, it compares:
1. **Source A:** Broker-reported IRS Form 1099-DA evidence (CSV export from digital asset brokers/exchanges).
2. **Source B:** Taxpayer accounting ledger evidence (CSV export from crypto tax software like Koinly, CoinTracker, or firm general ledgers).

### Key Architectural Invariants:
- **Local-First Execution:** VaultBasis Edge runs entirely on the practitioner's local computer.
- **Zero Cloud Ingestion for Case Processing:** Client tax records, transactions, wallet addresses, and Form 1099-DA documents are parsed and stored exclusively in a local SQLite database on the practitioner's machine. No taxpayer data is uploaded to VaultBasis cloud servers during normal Edge case processing.
- **Cryptographic Evidence Receipt:** The software generates an Ed25519 digitally signed outcome receipt (JSON) recording deterministic mathematical agreement or variance under a published ruleset (`VB_US_1099DA_2025_R1`).
- **Independent Verification:** An offline verification tool (`verify_receipt.py` / `VERIFY.html`) allows third parties to verify receipt payload integrity without communicating with VaultBasis servers.
- **Declared Outcome Limitation:** Every generated receipt and verifier result explicitly asserts:
  ```json
  "checks": {
    "installation_identity": "NOT_AUTHENTICATED",
    "tax_correctness": "NOT_DETERMINED"
  }
  ```

---

## 2. Specific Questions for Legal Counsel

---

### Question 1 (LEGAL-001): Scope & Applicability of Internal Revenue Code § 7216

**Background:** 26 U.S. Code § 7216 and Treas. Reg. § 301.7216-1 impose criminal and civil penalties for unauthorized disclosure or use of tax return information by "tax return preparers", which includes persons providing auxiliary services or developing software used to prepare or file returns.

**Questions for Counsel:**
1. Given that VaultBasis Edge is an analytical/reconciliation tool used by tax professionals prior to return preparation, and does not itself prepare, calculate tax liability, or file Form 1040/8949, does VaultBasis (or its corporate entity) qualify as a "tax return preparer" under Treas. Reg. § 301.7216-1(b)(2)?
2. In light of VaultBasis Edge's local-first architecture (where VaultBasis never receives or accesses taxpayer data), what affirmative disclosures, consent mechanisms (under § 301.7216-3), or data handling policies are recommended for:
   - The desktop application Terms of Service;
   - Customer support interactions (e.g., when a user submits an inquiry);
   - License activation and payments via Paddle?

---

### Question 2 (LEGAL-002): Gramm-Leach-Bliley Act (GLBA) & FTC Safeguards Rule Scope

**Background:** The FTC Safeguards Rule (16 C.F.R. Part 314) establishes data security requirements for non-bank "financial institutions," defined by activity, including financial data processing and tax preparation services.

**Questions for Counsel:**
1. Does VaultBasis EURL constitute a "financial institution" subject to the FTC Safeguards Rule solely by licensing local-first tax reconciliation software to accounting firms?
2. Given that VaultBasis maintains no central repository of consumer non-public personal information (NPI) from Edge cases, what specific administrative, technical, and organizational security policies should be documented to ensure full compliance?

---

### Question 3 (LEGAL-003 & LEGAL-011): Cross-Border Contracting, Terms of Service & Governing Law

**Background:** VaultBasis is structured as a French EURL selling software subscriptions primarily to U.S.-based tax accounting firms via Paddle (acting as Merchant of Record).

**Questions for Counsel:**
1. What governing law and dispute resolution/venue provisions are optimal for the Terms of Service (e.g., Delaware law with arbitration vs. French law)?
2. Are the limitation of liability clauses (capping liability to fees paid in the prior 12 months and excluding indirect/consequential damages) and "AS IS" warranty disclaimers sufficiently robust under U.S. Uniform Commercial Code (UCC) and applicable state laws?
3. What exact legal disclosures are required on the website and invoices to maintain seamless consistency between the French EURL entity, Paddle Merchant of Record representation, and U.S. customers?

---

### Question 4 (LEGAL-008 & LEGAL-009): Trademark Fair Use & Professional Liability Positioning

**Background:** VaultBasis references third-party tax software formats ("Koinly CSV", "CoinTracker CSV") and IRS tax forms ("IRS Form 1099-DA") in UI parsers and documentation.

**Questions for Counsel:**
1. Is the proposed nominative fair use notice sufficient to protect against trademark infringement and false affiliation claims under the Lanham Act?
   - *Draft Notice:* "IRS Form 1099-DA is a tax form published by the United States Internal Revenue Service. Koinly, CoinTracker, and other referenced third-party product names are trademarks of their respective owners. Reference to them is solely for descriptive format compatibility and does not imply affiliation, sponsorship, or endorsement."
2. Does the software's `tax_correctness: NOT_DETERMINED` boundary adequately insulate VaultBasis from state Unauthorized Practice of Law (UPL) claims and IRS Circular 230 practitioner liability?

---

### Question 5 (LEGAL-012 & LEGAL-013): Commercial Terms, Refunds & Incident Escalation

**Background:** Subscriptions are sold annually (Practitioner: $499/yr for 10 cases; Firm: $1499/yr for 50 cases). License expiration disables new case creation while preserving local read access to existing receipts.

**Questions for Counsel:**
1. Does the annual subscription, no-grace-period renewal, and refund policy comply with U.S. federal and state consumer/commercial protection statutes?
2. What incident notification obligations apply to VaultBasis EURL if website/account or support systems (containing business contact info, but no case tax data) experience a security event?

---

## 3. Attachments & Technical References

1. **Current Terms of Service:** [`apps/web-marketing/terms-of-service.html`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/apps/web-marketing/terms-of-service.html)
2. **Current Privacy Policy:** [`apps/web-marketing/privacy-policy.html`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/apps/web-marketing/privacy-policy.html)
3. **Receipt & Verifier Schema Specification:** [`schemas/receipt/receipt-v0.1.json`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/schemas/receipt/receipt-v0.1.json)
4. **Legal Risk Qualification Ledger:** [`docs/qualification/mmp15_legal_risk_qualification.md`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/docs/qualification/mmp15_legal_risk_qualification.md)
