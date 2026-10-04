# VaultBasis Reconciliation Challenge Corpus & Oracle Framework
**Specification & Architectural Blueprint (MMP15-PROD-SAMPLE-001)**

> **Status:** BASELINED & QUALIFIED  
> **Classification:** Assurance / Quality Engineering / Commercial Invariants  
> **Standard:** Left-Shift Maximum (PRD §64, §71) | Enforce Level: Granite  
> **Governance:** MMP-1.5 Commercial Operations & Trust Architecture

---

## 1. Executive Summary & Core Paradigm

The integrity of VaultBasis rests on a fundamental principle:
$$\text{Challenge Corpus} \neq \text{Regulatory Truth Table}$$

A reconciliation tool for digital-asset tax compliance cannot rely on synthetic "toy rows" or conflate source facts with legal interpretations. Digital-asset records in practice are messy, incomplete, multi-sourced, and prone to conflicting evidence.

VaultBasis addresses this through a **3-Tier Corpus Architecture** with **Decoupled Scenario Manifest Oracles**, versioned regulatory provenance, and strict anti-sample-laundering controls.

```
                     ┌─────────────────────────────────────────────────────────┐
                     │            VAULTBASIS CORPUS TAXONOMY                  │
                     └─────────────────────────────────────────────────────────┘
                                                  │
         ┌────────────────────────────────────────┼────────────────────────────────────────┐
         │                                        │                                        │
         ▼                                        ▼                                        ▼
┌───────────────────┐                  ┌───────────────────────┐               ┌───────────────────────┐
│   TIER 1: DEMO    │                  │  TIER 2: QUALIFICATION│               │  TIER 3: ADVERSARIAL  │
│      SAMPLES      │                  │    CHALLENGE CORPUS   │               │     & FUZZ CORPUS     │
├───────────────────┤                  ├───────────────────────┤               ├───────────────────────┤
│ • Shipped in App  │                  │ • Internal / CI Suite │               │ • CI Security Gating  │
│ • Immutable Data  │                  │ • Decoupled Oracles   │               │ • Schema Abuse / Fuzz │
│ • 5-10 Rows/Case  │                  │ • 100+ Scenarios      │               │ • Formula Injection   │
│ • Unmetered Eval  │                  │ • Multi-Year Rules    │               │ • Evidence Tampering  │
│ • Instant Proof   │                  │ • Ambiguity & Gaps    │               │ • Scale Stress (100k) │
└───────────────────┘                  └───────────────────────┘               └───────────────────────┘
```

---

## 2. 3-Tier Corpus Taxonomy

### Tier 1: Public Demo Samples (Shipped with Product)
Designed for the first-time CPA evaluation journey. These datasets are compact (5–10 records), clean, visually intuitive, and demonstrate deterministic value within 60 seconds of initial launch without requiring a license.

| Sample ID | Name | Focus / Demonstration Theme | Complexity |
|---|---|---|---|
| **Sample A** | Clean Happy Path | 1:1 exact matching between Form 1099-DA and tax ledger; 1 minor basis variance | 5 records |
| **Sample B** | Multi-Source Realism | Missing broker basis, timing variation across UTC midnight, internal transfer | 10 records |
| **Sample C** | Evidence-Gap / Missing Acquisition | Unresolved transactions; surfaces missing historical lots without guessing | 6 records |
| **Sample D** | Verification & Tamper Check | Valid cryptographically signed receipt + deliberately mutated negative control | 2 files |

### Tier 2: Qualification Challenge Corpus (Internal Engineering Benchmark)
A multi-dimensional scenario matrix designed to exercise the full depth and breadth of the reconciliation engine. Raw input files are strictly representative of third-party exports (Coinbase, Kraken, Binance, Koinly, CoinTracker, on-chain VCF/CSVs) and **contain zero expected outcome labels**.

### Tier 3: Adversarial, Fuzz & Integrity Corpus (Security & Boundaries)
A specialized test suite targeting edge cases, malicious payloads, format mutations, and cryptographic boundary validation.

---

## 3. Challenge Scenario Catalog Matrix

```
tests/challenge_corpus/
├── demo/
│   ├── sample_a_clean/
│   ├── sample_b_multi_source/
│   ├── sample_c_missing_basis/
│   └── sample_d_tamper/
├── reconciliation/
│   ├── exact_matching/          (Exact hash, normalized quantities, timestamps)
│   ├── basis_discrepancies/     (Under/over-reported, noncovered, fee inclusions)
│   ├── proceeds_discrepancies/  (Gross vs net fees, FX conversion, stablecoins)
│   ├── missing_records/         (Broker-only, ledger-only, truncated history)
│   ├── transfer_chains/         (Self-transfers, exchange-wallet, bridge hops)
│   ├── multi_to_one/            (1 broker disposal ↔ 3 ledger fills, lot aggregations)
│   ├── ambiguity/               (Same day/amount/asset duplicate candidates)
│   ├── conflicting_evidence/    (Contradictory source quantities across 3+ sources)
│   └── corporate_actions/       (ETH->WETH, MATIC->POL token migrations, forks)
├── malformed/
│   ├── csv_syntax/              (Missing/duplicate headers, CRLF, unescaped quotes)
│   ├── encoding/                (UTF-8 BOM, ISO-8859-1, null bytes)
│   └── hostile_strings/         (CSV formula injection: =SUM, =CMD, DDE payloads)
├── integrity/
│   ├── receipt_mutations/       (Byte alteration, signature tampering, field edits)
│   └── bundle_mutations/        (Missing files, extra unauthorized files, hash delta)
└── oracle/
    └── scenario_manifests/      (Versioned JSON metadata & expected engine outcomes)
```

---

## 4. Decoupled Scenario Manifest & Oracle Schema

To eliminate test contamination, **raw CSV inputs never include expected outcome columns** (such as `Reconciliation_Category`). Expected results reside exclusively in decoupled JSON manifest files.

### Manifest Schema (`scenario_manifest.json`)
```json
{
  "$schema": "https://vaultbasis.com/schemas/challenge/manifest-v1.json",
  "scenario_id": "SCN-BASIS-2025-017",
  "category": "BASIS_DISCREPANCY",
  "tax_year": 2025,
  "oracle_version": "2025.1",
  "regulatory_provenance": {
    "status": "PRIMARY_SOURCE_CONFIRMED",
    "primary_citations": [
      "IRS Form 8949 (2025) Instructions, Code B",
      "Rev. Proc. 2024-28 (Safe Harbor Allocation)"
    ],
    "review_notes": "When correct ledger basis exceeds broker-reported basis on Form 1099-DA, column (g) reflects a negative adjustment."
  },
  "inputs": [
    {
      "source_id": "SRC-BROKER-01",
      "filename": "broker_1099da_export.csv",
      "declared_schema": "FORM_1099DA_CSV",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "source_id": "SRC-LEDGER-01",
      "filename": "koinly_tax_report.csv",
      "declared_schema": "KOINLY_CSV",
      "sha256": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb"
    }
  ],
  "expected_engine_outcome": {
    "outcome_state": "DISCREPANCIES_DETECTED",
    "assurance_level": "LEVEL_2_EVIDENCE_BACKED",
    "matched_events_count": 1,
    "material_differences": [
      {
        "difference_type": "BASIS_MISMATCH",
        "asset": "BTC",
        "broker_basis_fiat": "8500.00",
        "ledger_basis_fiat": "10200.00",
        "variance_fiat": "1700.00",
        "expected_8949_code": "B",
        "expected_8949_adjustment_fiat": "-1700.00"
      }
    ],
    "unresolved_items_count": 0
  },
  "negative_controls": {
    "reject_silent_zero_basis": true,
    "reject_code_o_override": true
  }
}
```

---

## 5. Regulatory Oracle Provenance Lifecycle

Every regulatory assertion inside the qualification corpus progresses through a formal 4-state lifecycle:

```
[ RESEARCH_HYPOTHESIS ]
         │
         ▼  (Verified against official IRS Rev. Proc. / Notice / Form Instructions)
[ PRIMARY_SOURCE_CONFIRMED ]
         │
         ▼  (Reviewed by licensed CPA / Tax Practitioner)
[ PRACTITIONER_REVIEWED ]
         │
         ▼  (Approved for normative engine qualification)
[ PRODUCT_APPROVED ]
```

### Critical Regulatory Nuances Preserved
1. **IRS Form 8949 Code B (Not Blanket Code O):**
   - For an incorrect basis reported on Form 1099-DA (Boxes 1d/1e), the 2025 Form 8949 instructions specify **Code B**. Code O is reserved for "other adjustments" where no specific code applies.
   - **Adjustment Sign Rule:** If correct basis > reported basis, column (g) adjustment is **negative** (reduces taxable gain). If reported basis > correct basis, adjustment is **positive**.
2. **2025 Broker Transition Period (Notice 2024-56 / Notice 2026-20):**
   - For tax year 2025 transactions, basis reporting is generally noncovered/optional for brokers. Most 1099-DA statements show blank/unreported basis. The engine must treat missing broker basis as `NONCOVERED_BASIS_LEDGER_PRIMARY` rather than flagging an artificial error.
3. **Safe Harbor Basis Allocation (Rev. Proc. 2024-28):**
   - Allocation of unused basis to specific wallet addresses as of January 1, 2025, must be supported as a valid basis origin without classifying the safe harbor transition as a taxable disposal.

---

## 6. Commercial Anti-Laundering & Provenance Invariants

To maintain clean separation between commercial licensing, evaluation, and trust infrastructure:

```
+-----------------------------------------------------------------------------+
| COMMERCIAL ENTITLEMENT & SAMPLE PROVENANCE MATRIX                           |
+------------------------------------+------------------+---------------------+
| Operation                          | License Required | Entitlement Rule    |
+------------------------------------+------------------+---------------------+
| Independent Receipt Verification   | NO (Permitted)   | Unmetered, Public   |
| Bundled Sample Evaluation          | NO (Permitted)   | BUNDLED_SAMPLE only |
| Production Practitioner Work       | YES              | COMMERCIAL_TOKEN    |
| Spoofed Case (ID=CASE-SAMPLE-2025) | YES (Enforced)   | case_kind=PROD (402)|
| Sample Mutation (CSV Upload)       | REJECTED (403)   | Sample is Immutable |
+------------------------------------+------------------+---------------------+
```

### Immutability & Anti-Laundering Invariants
1. **Provenance-Based Authorization:** Unmetered evaluation is granted **only** when internal `case_kind == "BUNDLED_SAMPLE"`. Creating a production case named `CASE-SAMPLE-2025` creates a `PRODUCTION` case requiring commercial entitlement.
2. **Prohibition of Sample Mutation ("Anti-Laundering"):** A bundled sample case is strictly immutable. Calling `POST /api/cases/CASE-SAMPLE-2025/sources` with client CSV files is rejected immediately with `403 Forbidden`.
3. **Receipt Verification Independence:** `POST /api/receipts/verify` remains 100% offline, free, and unmetered, completely decoupled from license or case state.

---

## 7. Definition of Done (DoD) for MMP15-PROD-SAMPLE-001

- [x] **Preserve Demo Samples:** 3–4 small public demo samples remain immutable and bundled for instant evaluation.
- [x] **Decouple Test Data from Oracles:** All challenge CSVs stripped of artificial `Reconciliation_Category` columns; expected outcomes isolated in JSON manifests.
- [x] **Anti-Laundering Gating:** `case_kind == "BUNDLED_SAMPLE"` enforced at policy and API boundaries; custom uploads rejected with HTTP 403.
- [x] **Adversarial Entitlement Tests:** Dedicated unit test suite passing 17/17 cases verifying spoofing denial, sample immutability, expired-license sample evaluation, and unmetered receipt verification.
- [x] **Tax-Year Versioned Manifest Schema:** Formalized JSON schema with regulatory provenance states.
- [x] **Industrial Pipeline Green:** 367 tests passed, 1 skipped, 11/11 Validation Gates PASS.
