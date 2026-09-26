# VaultBasis — Manual Validation Runbook & Scenarios Directory
**Document Version:** 1.0.0 (MMP-1 Preview)  
**Target Audience:** CPAs, QA Engineers, Compliance Officers, Regulatory Auditors  
**Standard:** Granite-Grade Left-Shift Industrial Standard  
**Normative Reference:** PRD v26.0 §41 (Preview Gates AC-01 to AC-07), §13 (Evidence Contract v0.1), §14 (13 Outcome States)

---

## 1. Executive Summary & Objective

This runbook provides exhaustive, step-by-step manual validation scenarios to certify the functional correctness, regulatory fidelity, cryptographic authenticity, and zero-egress security posture of VaultBasis Edge.

Every scenario specifies:
- **Scenario ID & Title**
- **Objective & Regulatory Invariant**
- **Prerequisites & Fixtures**
- **Exact Action Steps (UI, CLI, and REST API)**
- **Expected Deterministic Output (Screenshots / Payloads / Badges)**
- **Disqualifying Failure Indicators (Anti-Patterns & Red Flags)**
- **Audit Sign-off Criteria**

---

## 2. Pre-Flight Checklist & Environment Setup

Before initiating any manual validation scenario, ensure the runtime environment passes this checklist:

| Check | Requirement | Verification Command | Pass Criterion |
| :--- | :--- | :--- | :--- |
| **Python Version** | Python 3.10+ | `python3 --version` | `>= 3.10.0` |
| **Local Service** | Edge daemon running on localhost | `curl -s http://127.0.0.1:8000/api/health` | HTTP 200, `status: "HEALTHY"` |
| **Network Egress** | Zero outbound WAN connections | `lsof -i :8000` | Bound strictly to `127.0.0.1:8000` |
| **Key Permissions** | Ed25519 installation key secured | `stat -f "%Lp" data/keys/installation_ed25519.key` | POSIX mode `0600` |
| **Clean Machine** | Independent verifier available | `python3 apps/verifier/verify_receipt.py --help` | CLI options displayed cleanly |

To start the local stack for manual testing:
```bash
./scripts/launch.sh
```
The dashboard is accessible at `http://127.0.0.1:8000/`.

---

## 3. Standard Test Fixtures

Use these standardized CSV datasets when executing manual scenarios:

### Fixture A: Broker Form 1099-DA (`broker_1099da_sample.csv`)
```csv
Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2
BTC,2025-11-20,18400.00,2025-02-11,12100.00,YES
ETH,2025-12-05,3200.00,2025-03-01,2800.00,YES
SOL,2025-08-14,4500.00,2025-01-10,,NO
```

### Fixture B: Taxpayer Software Ledger (`koinly_ledger_sample.csv`)
```csv
Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired
2025-11-20,BTC,1.0,16300.00,18400.00,2100.00,2025-02-11
2025-12-05,ETH,1.0,2800.00,3200.00,400.00,2025-03-01
2025-08-14,SOL,30.0,4000.00,4500.00,500.00,2025-01-10
```

---

## 4. Master Manual Scenarios Matrix

| Scenario ID | Category | Primary Focus | Target Surface | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **MAN-01** | CPA Workflow | Basis Difference Detection & Provenance | Web Dashboard (Screen 1 & 2) | P0 (Critical) |
| **MAN-02** | Happy Path | Perfect 1:1 Matched Reconciliation | Web Dashboard (Screen 2 & 3) | P0 (Critical) |
| **MAN-03** | Regulatory | 2025 Transitional Non-Covered Scope (Box 2 NO) | Web Dashboard (Screen 2) | P0 (Critical) |
| **MAN-04** | Invariant | Unresolved Data Preservation (No $0.00 Drift) | Web Dashboard & REST API | P0 (Critical) |
| **MAN-05** | Discrepancy | Orphan Detection (Missing from Ledger/1099) | Web Dashboard (Screen 2) | P1 |
| **MAN-06** | Resilience | Malformed CSV & Corrupted Input Fail-Closed | Web Dashboard (Screen 1) | P0 (Critical) |
| **MAN-07** | Verification | Drag-and-Drop Web Verifier Inspection | Public Web Verifier (`/verifier`) | P0 (Critical) |
| **MAN-08** | Anti-Tamper | Cryptographic Signature Tamper Rejection | CLI Verifier & Web Verifier | P0 (Critical) |
| **MAN-09** | Evidence | Self-Contained ZIP Export & Offline Verification | Air-Gapped Terminal | P0 (Critical) |
| **MAN-10** | Security | Zero Token Bleed & Zero Egress Audit | Terminal (`lsof` / `tcpdump`) | P0 (Critical) |

---

## 5. Granular Step-by-Step Scenarios

### Scenario MAN-01: End-to-End CPA Basis Difference Workflow
- **Objective:** Verify that a real-world basis variance ($12,100 reported by broker vs. $16,300 tracked by taxpayer) is detected, classified as `BASIS_DIFFERENCE`, proven with shallow links, and signed into a receipt.
- **Surface:** Web Dashboard (`http://127.0.0.1:8000/`)
- **Execution Steps:**
  1. Open browser to `http://127.0.0.1:8000/`.
  2. In Screen 1 (Case Intake), enter Case ID: `CASE-MANUAL-001`, Tax Year: `2025`, Jurisdiction: `US`. Click **Create Case**.
  3. Drag and drop `broker_1099da_sample.csv` into Source A dropzone. Verify badge shows `IRS_1099DA_2025_PREVIEW` with 3 rows.
  4. Drag and drop `koinly_ledger_sample.csv` into Source B dropzone. Verify badge shows `KOINLY_CAPITAL_GAINS_CSV_V1` with 3 rows.
  5. Click **Execute Deterministic Reconciliation**.
  6. On Screen 2 (Case Review), locate the BTC row.
- **Expected Results:**
  - Outcome State badge displays: `BASIS_DIFFERENCE` (Amber color).
  - BTC variance card displays: Proceeds: `$18,400.00` (Match), Broker Basis: `$12,100.00`, Ledger Basis: `$16,300.00`, Variance: `$4,200.00`.
  - Provenance links point to exact row references in Source A and Source B.
  - Receipt ID and Ed25519 signature hash are populated.
- **Disqualifying Failure Indicators:**
  - Green "MATCHED" badge displayed despite $4,200 variance (Greenwashing defect).
  - Floating point rounding error (e.g. `$4199.999999999999`).
  - Missing provenance file hashes.

---

### Scenario MAN-02: Clean Matched Reconciliation Workflow
- **Objective:** Verify that perfectly aligned records result in clean `MATCHED` outcome with zero false positives.
- **Surface:** Web Dashboard (`http://127.0.0.1:8000/`)
- **Execution Steps:**
  1. Create single-row 1099-DA: `BTC, 2025-05-01, Proceeds: 10000.00, Cost Basis: 8000.00, Box 2: YES`.
  2. Create single-row Koinly CSV: `BTC, 2025-05-01, Proceeds: 10000.00, Cost Basis: 8000.00`.
  3. Create Case `CASE-MANUAL-MATCHED` and upload both files.
  4. Click **Execute Deterministic Reconciliation**.
- **Expected Results:**
  - Outcome State badge displays: `MATCHED` (Green color).
  - Material Differences section displays: "0 Material Differences Detected".
  - Proceeds and Cost Basis totals match exactly: `$10,000.00` and `$8,000.00`.
- **Disqualifying Failure Indicators:**
  - Amber or red warning badge on identical data.

---

### Scenario MAN-03: 2025 Transitional Non-Covered Scope (Box 2 NO)
- **Objective:** Verify that missing basis for 2025 non-covered assets is recognized as `REPORTING_SCOPE_DIFFERENCE` rather than an accounting discrepancy or broker error (PRD §14.3).
- **Surface:** Web Dashboard (`http://127.0.0.1:8000/`)
- **Execution Steps:**
  1. Upload `broker_1099da_sample.csv` (contains SOL disposition with Box 2: "NO" and blank basis).
  2. Upload `koinly_ledger_sample.csv` (contains SOL disposition with basis `$4,000.00`).
  3. Reconcile case.
- **Expected Results:**
  - Difference record for SOL displays `REPORTING_SCOPE_DIFFERENCE`.
  - Broker Value displays: `"NOT_REPORTED (Box 2)"`.
  - Description states: *"Reporting scope difference: Broker 1099-DA does not report basis for 2025 non-covered disposition."*
- **Disqualifying Failure Indicators:**
  - System flags broker for "discrepancy" or "fraud" when Box 2 is legally non-covered.

---

### Scenario MAN-04: Unresolved Data Preservation (No $0.00 Coercion)
- **Objective:** Verify that missing prices or basis are never coerced to `$0.00` (PRD AC-03 invariant).
- **Surface:** REST API & Web Dashboard
- **Execution Steps:**
  1. Create CSV with missing basis where Box 2 is YES:
     ```csv
     Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2
     AVAX,2025-09-01,1200.00,2025-01-01,,YES
     ```
  2. Upload and inspect parsed transaction via API: `GET /api/cases/{case_id}`.
- **Expected Results:**
  - In JSON payload: `cost_basis: null` (or omitted).
  - `is_unresolved: true`.
  - `unresolved_reason: "BASIS_UNAVAILABLE"`.
  - In UI: Badge reads `UNRESOLVED_DATA` (never `$0.00`).
- **Disqualifying Failure Indicators:**
  - Cost basis displayed as `$0.00` or `0.0`.
  - Artificial capital gain of `$1,200.00` calculated on unverified basis.

---

### Scenario MAN-05: Orphan Transaction Detection
- **Objective:** Detect when transactions exist in broker records but are completely absent from taxpayer ledger, and vice versa.
- **Surface:** Web Dashboard
- **Execution Steps:**
  1. Source A (1099-DA) has transaction: `SOL, 2025-04-10, $500.00`.
  2. Source B (Ledger) has NO transaction for SOL in April 2025.
  3. Reconcile case.
- **Expected Results:**
  - Difference list shows state: `MISSING_FROM_LEDGER`.
  - Ledger reference indicates: `NOT_FOUND`.
  - System flags unrecorded disposition requiring CPA inquiry.

---

### Scenario MAN-06: Malformed Input Fail-Closed Rejection
- **Objective:** Confirm that corrupted files, schema drift, or non-financial files fail gracefully without corrupting state or crashing the server (PRD AC-04).
- **Surface:** Web Dashboard & API
- **Execution Steps:**
  1. Create a corrupt text file `corrupt.csv`:
     ```text
     Not,A,Valid,Financial,Table
     Foo,Bar,Baz,Qux,Quux
     ```
  2. Attempt to upload to Case Intake.
- **Expected Results:**
  - Upload fails with explicit error message: *"Unrecognized schema or missing required columns"*.
  - HTTP 400 Bad Request returned by API.
  - Zero partial transactions saved in SQLite.
  - Service daemon continues operating with 100% stability.
- **Disqualifying Failure Indicators:**
  - Unhandled 500 Internal Server Error.
  - Zombie case record created with zero valid data.

---

### Scenario MAN-07: Public Web Verifier Offline Inspection
- **Objective:** Verify that receipts can be drag-and-dropped into the standalone web verifier in a browser with zero backend dependency (PRD §34.3).
- **Surface:** Public Web Verifier (`http://127.0.0.1:8000/verifier`)
- **Execution Steps:**
  1. Export a valid `receipt-v0.1.json` from Screen 3 of the dashboard.
  2. Navigate to `http://127.0.0.1:8000/verifier`.
  3. Turn off local network / Wi-Fi (optional, to test offline capability).
  4. Drag and drop `receipt-v0.1.json` into the dropzone.
- **Expected Results:**
  - Report Banner: **VAULTBASIS INDEPENDENT VERIFICATION — PASS** (Green).
  - Checks checklist renders 4 green ticks:
    - [✓] JSON Schema Conformance: PASS (Draft-07 compliant)
    - [✓] Evidence Contract Version: PASS (v0.1)
    - [✓] Key Fingerprint Match: PASS
    - [✓] Ed25519 Cryptographic Signature: PASS (Valid over RFC 8785 canonical digest)
  - Statutory Limitation Notice rendered at bottom.
- **Disqualifying Failure Indicators:**
  - Network error modal or outgoing HTTP request detected in browser DevTools.

---

### Scenario MAN-08: Cryptographic Signature Tamper Rejection
- **Objective:** Prove that altering even a single cent or single character in a signed receipt causes instant, categorical verification failure (PRD AC-06).
- **Surface:** Standalone CLI Verifier (`apps/verifier/verify_receipt.py`)
- **Execution Steps:**
  1. Take `tests/fixtures/golden_receipt_valid.json`.
  2. Open in text editor and change variance from `"4200.00"` to `"4200.01"`.
  3. Save as `tampered_test.json`.
  4. Run CLI verifier:
     ```bash
     python3 apps/verifier/verify_receipt.py tampered_test.json --no-color
     ```
- **Expected Results:**
  - Output Header: **VAULTBASIS INDEPENDENT OUTCOME VERIFICATION REPORT — FAIL**.
  - Check `[4] Ed25519 Signature Match` displays `FAIL`.
  - Process exits with returncode `1`.
  - Explicit error: *"Ed25519 signature verification FAILED: Receipt payload has been tampered with or corrupted."*
- **Disqualifying Failure Indicators:**
  - Verifier reports PASS on altered receipt.

---

### Scenario MAN-09: Self-Contained ZIP Export & Clean-Machine Audit
- **Objective:** Verify that the exported ZIP evidence bundle contains everything required for a third party (IRS auditor, court, CPA) to verify the case offline.
- **Surface:** Clean Air-Gapped Terminal
- **Execution Steps:**
  1. On Screen 3 of dashboard, click **Download Evidence Bundle (.ZIP)**.
  2. Move `VaultBasis_Evidence_CASE-MANUAL-001.zip` to a fresh directory `/tmp/airgap_test/`.
  3. Unzip the bundle:
     ```bash
     unzip VaultBasis_Evidence_CASE-MANUAL-001.zip
     ```
  4. Verify contents:
     - `receipt-v0.1.json` (Signed receipt)
     - `verify_receipt.py` (Standalone verifier)
     - `schemas/receipt-v0.1.json` (Normative schema)
     - `evidence/` (Raw source documents with SHA-256 hashes in filenames)
     - `VERIFY_INSTRUCTIONS.txt` (Third-party audit instructions)
  5. Run independent verification:
     ```bash
     python3 verify_receipt.py receipt-v0.1.json --evidence-dir evidence/ --no-color
     ```
- **Expected Results:**
  - Check `[5] Source Hashes Match` reports `PASS` for all files in `evidence/`.
  - Overall status reports `PASS`.
- **Disqualifying Failure Indicators:**
  - Missing verifier script or schemas in exported ZIP.
  - Python import errors (e.g. `No module named 'edge'`).

---

### Scenario MAN-10: Zero-Egress Network Isolation Audit
- **Objective:** Formally prove that VaultBasis Edge does not send transaction data to cloud endpoints, telemetry trackers, or AI model providers (PRD §21.1, AC-07).
- **Surface:** Terminal / Network Monitor
- **Execution Steps:**
  1. In a terminal, run active listening socket query:
     ```bash
     lsof -nP -iTCP:8000 -sTCP:LISTEN
     ```
  2. Verify daemon is bound exclusively to `127.0.0.1` or localhost.
  3. Execute full Case Intake, Reconciliation, and Receipt Generation workflow.
  4. Inspect network logs:
     ```bash
     netstat -an | grep 8000
     ```
- **Expected Results:**
  - Zero foreign IP addresses or remote hostnames contacted.
  - `/api/health` reports `"egress_policy": "STRICT_LOCAL_ONLY"`.
- **Disqualifying Failure Indicators:**
  - Outbound DNS lookups or HTTPS connections to external cloud providers.

---

## 6. Manual Test Execution Log Template

Use this template to record the results of manual testing rounds:

```text
================================================================================
                    VAULTBASIS MANUAL VALIDATION LOG
================================================================================
Execution Date:    YYYY-MM-DD
Tester / Operator: [Name, Title]
Environment:       [macOS / Ubuntu / Air-Gapped Docker]
Edge Version:      v0.1.0-preview
Commit SHA:        [git rev-parse --short HEAD]

SCENARIO RESULTS:
[ ] MAN-01: CPA Basis Difference Workflow          -> [PASS / FAIL]
[ ] MAN-02: Clean Matched Reconciliation Workflow  -> [PASS / FAIL]
[ ] MAN-03: 2025 Transitional Non-Covered Scope    -> [PASS / FAIL]
[ ] MAN-04: Unresolved Data Preservation           -> [PASS / FAIL]
[ ] MAN-05: Orphan Transaction Detection           -> [PASS / FAIL]
[ ] MAN-06: Malformed Input Fail-Closed Rejection   -> [PASS / FAIL]
[ ] MAN-07: Public Web Verifier Offline Inspection -> [PASS / FAIL]
[ ] MAN-08: Cryptographic Signature Tamper Check   -> [PASS / FAIL]
[ ] MAN-09: Self-Contained ZIP Export Audit        -> [PASS / FAIL]
[ ] MAN-10: Zero-Egress Network Isolation Audit    -> [PASS / FAIL]

OVERALL ROUND STATUS: [CERTIFIED READY / REJECTED]
Lead Auditor Signature: ___________________________
================================================================================
```
