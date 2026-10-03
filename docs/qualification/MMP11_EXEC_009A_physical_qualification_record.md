# MMP11-EXEC-009A Physical Recipient Qualification Record

> **Governance State:** `READY_FOR_PHYSICAL_RECIPIENT_QUALIFICATION`  
> **Rule:** No distribution to Associate-001 or CPA until physical recipient tests pass without developer intervention.

---

## 1. Candidate Identity & Governance Freeze

### Active Candidate Under CI / Packaging (Candidate 3)
- **Source SHA:** `377c0562d095e9d2e18e303c91c432d4fb7362f1`
- **Candidate Governance State:** `LOCAL_AUTOMATED_VALIDATION_PASS / CI_PENDING`
- **CI Run ID:** `[PENDING CI EXECUTION]`
- **Mac arm64 Inner-ZIP SHA-256:** `[PENDING CI BUILD]`
- **Windows x64 Inner-ZIP SHA-256:** `[PENDING CI BUILD]`
- **Included Task Scope & Dispositions:**
  - `MMP11-DIST-WIN-002`: Explicit `encoding="utf-8"` in `edge/api/app.py` for all template/static reads on Windows non-UTF8 locales.
  - `MMP11-DIST-GATE-002`: Strengthened packager launch gates (`build_rc3_windows.py` and `build_rc3_macos.py`) asserting `GET /api/health` == 200, `GET /` == 200 + HTML marker, and `POST /api/sample-case/load` == 200.
  - `VB-CASE-INV-001` / `MMP11-CASE-001`: In-memory draft case isolation — canceling, abandoning, or uploading invalid evidence creates zero additional persistent SQLite records.
  - `MMP11-UI-HDR-001`: Streamlined single-line non-wrapping header navigation layout.
  - `VB-REG-GAP-001`: Form 1099-DA / TD 10000 / Rev. Proc. 2024-28 regulatory evidence context disposition.
  - `MMP11-TEST-SMPL-001`: 3 Conformance test sample datasets in `samples/`.

### Historical Failed Candidates (Preserved Failure Evidence)
- **Candidate 1 (Mac Launch Failure):** Source SHA `641d2b135ab0dcfa3bdf3b5edc95f4d1a3d5511d` (CI Run `37120319044`)
  - Mac arm64 Inner-ZIP SHA-256: `8e8e77290a8544c0e9fe72f5c862cb942e2dcc293ce80b9f8d93ff7565c2bb24` (FAILED: Gatekeeper / port contention)
  - Windows x64 Inner-ZIP SHA-256: `6f25843188aaf91b6688902e87bc487f68bc76999f077745876ca0b926bc52f3`
- **Candidate 2 (Windows HTTP 500 Failure):** Source SHA `160f4d7f8cfceebbcac2b33a12d1c0e67b7d0659` (CI Run `37123027673`)
  - Mac arm64 Inner-ZIP SHA-256: `4f6c0f1cc98319e5f21e4beb2a00c7ee54260c2e2a9eeb421884a8e0e633e832`
  - Windows x64 Inner-ZIP SHA-256: `7b9a99c6af97dbaf2ee896938e67df41181c125e2095296da57498843f8c2061` (FAILED: `GET /` returned HTTP 500 "Internal Server Error" on physical Windows machine)

---

## 2. Windows x64 Physical Recipient Qualification (Run 1 on 7b9a99... Record)

- **Target Machine:** Physical Windows x64 Machine (French locale / Windows 11)
- **OS / Version:** Windows 11 x64
- **Architecture:** x64
- **Tester Role:** Independent Recipient (No developer assistance)

| Check | Gate Description | Expected | Actual Result |
|---|---|---|---|
| **DOWNLOAD** | Download ZIP from Google Drive | Full archive downloaded | `PASS` (after recipient disk space freed) |
| **NORMAL EXTRACTION** | Extract ZIP via Windows Explorer standard Extract All | Clean folder layout, `VaultBasis.exe` beside `_internal/` | `PASS` |
| **APPLICATION_RUNTIME** | Double-click `VaultBasis.exe` in Explorer | Process starts, local port becomes reachable | `PASS` |
| **AUTO_WORKSPACE_OPEN** | Default web browser automatically launches and opens workspace | Browser loads `http://127.0.0.1:8000` automatically | `PASS` |
| **WORKSPACE_RESPONSE** | Root dashboard (`GET /`) renders functional UI | HTTP 200 with VaultBasis Edge UI | `FAIL` (Observed: HTTP 500 "Internal Server Error") |
| **INTERVENTION REQUIRED** | Developer tools, Terminal, Python, or code repair | Must be `NONE` | `NONE` (Test stopped immediately upon 500 error) |

**Overall Windows Run 1 Result:** `FAIL` (Stopped at initial workspace load)  
**Defect Classification:** `MMP11-DIST-WIN-002` — Packaged Windows Workspace HTTP 500.  
**Root Cause:** Unspecified encoding on `read_text()` inside `app.py` defaulted to Windows platform ANSI codepage (`cp1252`), failing on UTF-8 symbols in `index.html`.  
**Remediation:** Enforced `encoding="utf-8"` across all `read_text()` calls in `edge/api/app.py` and upgraded native CI launch gates to assert `GET /` and `POST /api/sample-case/load`.

---

## 3. macOS arm64 Physical Recipient Qualification

- **Target Machine:** Apple Silicon Mac (M1/M2/M3/M4)
- **OS / Version:** macOS 14 Sonoma / macOS 15 Sequoia / macOS 13 Ventura
- **Architecture:** arm64
- **Tester Role:** Founder / Independent Recipient

| Check | Gate Description | Expected | Actual Result |
|---|---|---|---|
| **NORMAL EXTRACTION** | Extract ZIP via Archive Utility in Finder | `VaultBasis.app` intact | `PASS` |
| **APPLICATION_RUNTIME** | Open `VaultBasis.app` (handle Gatekeeper via System Settings → Open Anyway) | App starts cleanly | `FAIL` (App did not open after Open Anyway) |
| **AUTO_WORKSPACE_OPEN** | Browser automatically opens workspace without manual URL entry | Default browser opens `http://127.0.0.1:8000` | `NOT TESTED` |
| **CASE MEANING UNDERSTOOD** | Practitioner understands what a Case represents | Bounded reconciliation activity | `NOT TESTED` |
| **CLIENT / TAX-YEAR CONTEXT CLEAR** | Client reference & 2025 tax year clear | Context visible | `NOT TESTED` |
| **TWO EVIDENCE ROLES UNDERSTOOD** | Source A (Broker) vs Source B (Tax Ledger) | Roles and extracted fields explicit | `NOT TESTED` |
| **EVIDENCE READINESS UNDERSTOOD** | Readiness state understood as structural suitability, not factual truth | Readiness disclaimers clear | `NOT TESTED` |
| **SAMPLE CASE** | 1-Click "Explore Sample Case" loads complete multi-asset scenario | Instant preload | `NOT TESTED` |
| **WORKFLOW ORIENTATION** | 4-Stage persistent workflow bar shows progress | 1. Sources → 2. Reconcile → 3. Findings → 4. Receipt | `NOT TESTED` |
| **RECONCILIATION** | Click "⚡ Run Deterministic Reconciliation" executes cleanly | Deterministic output generated | `NOT TESTED` |
| **RESULT NARRATIVE** | Evaluated count, Agreed (Green), Differences (Amber), Unresolved (Orange) | Attention items highlighted | `NOT TESTED` |
| **FINDING WHY** | Open Finding Why: explains what was compared, values, rule, provenance | Explainable without tax advice | `NOT TESTED` |
| **OUTCOME RECEIPT GENERATION** | Generate case's live signed Outcome Receipt and download/export JSON | Live receipt JSON generated and exported | `NOT TESTED` |
| **LIVE RECEIPT VERIFICATION** | Drop generated live receipt into GUI Offline Verifier | Displays `PASS — Receipt Valid` | `NOT TESTED` |
| **TAMPERED RECEIPT VERIFICATION** | Make copy of live receipt, edit 1 value, drop into GUI Offline Verifier | Displays `FAIL — Receipt Invalid or Tampered` | `NOT TESTED` |
| **QUIT** | Terminate VaultBasis process cleanly | Process exits | `NOT TESTED` |
| **RELAUNCH** | Double-click `VaultBasis.app` again in Finder | Boots cleanly | `NOT TESTED` |
| **PERSISTENCE** | Confirm previously created cases and receipts persist | Data intact in local SQLite | `NOT TESTED` |
| **INTERVENTION REQUIRED** | Terminal, xattr, chmod, Python, or developer repair | Must be `NONE` | Standard Gatekeeper Open Anyway attempted, app did not open |

**Recipient Explanation (Verbatim Unprompted Response):**  
> *"In your own words, what did VaultBasis just do, and what would you investigate next?"*  
> [NOT TESTED — Execution blocked at launch]

**Logged Findings Classification:**
- `BLOCKER`: Standard Gatekeeper GUI Open Anyway completed in System Settings, but double-clicking `VaultBasis.app` does not start the application.
- `COMPREHENSION FAILURE`: [None recorded yet]
- `OBSERVATION`: [None]

**macOS arm64 Result:** `FAIL`  
**Stopped At:** `Normal GUI launch after documented Gatekeeper Open Anyway procedure`

---

## 4. State Transition Rule
- macOS: `macOS DISTRIBUTION_QUALIFIED = NO` (`MMP11-DIST-MAC-002 = FAIL`)
- Windows: Independent qualification pending physical test on Windows x64.

