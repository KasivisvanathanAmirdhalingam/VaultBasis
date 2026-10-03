# MMP11-EXEC-009A Physical Recipient Qualification Record

> **Governance State:** `READY_FOR_PHYSICAL_RECIPIENT_QUALIFICATION`  
> **Rule:** No distribution to Associate-001 or CPA until physical recipient tests pass without developer intervention.

---

## 1. Candidate Identity Freeze
- **Source SHA:** `641d2b135ab0dcfa3bdf3b5edc95f4d1a3d5511d`
- **CI Run ID:** `37120319044`
- **Mac arm64 Inner-ZIP SHA-256:** `8e8e77290a8544c0e9fe72f5c862cb942e2dcc293ce80b9f8d93ff7565c2bb24`
- **Windows x64 Inner-ZIP SHA-256:** `6f25843188aaf91b6688902e87bc487f68bc76999f077745876ca0b926bc52f3`

---

## 2. Windows x64 Physical Recipient Qualification

- **Target Machine:** Physical Windows x64 Machine
- **OS / Version:** Windows 11 / Windows 10 x64
- **Architecture:** x64
- **Tester Role:** Independent Recipient (No developer assistance)

| Check | Gate Description | Expected | Actual Result |
|---|---|---|---|
| **NORMAL EXTRACTION** | Extract ZIP via Windows Explorer standard Extract All | Clean folder layout, `VaultBasis.exe` beside `_internal/` | PENDING / `PASS` / `FAIL` |
| **APPLICATION_RUNTIME** | Double-click `VaultBasis.exe` in Explorer (handle SmartScreen "Run anyway") | No console crash, no `Unable to configure formatter 'default'` | PENDING / `PASS` / `FAIL` |
| **AUTO_WORKSPACE_OPEN** | Default web browser automatically launches and opens workspace | Browser loads `http://127.0.0.1:8000` automatically | PENDING / `PASS` / `FAIL` |
| **CASE MEANING UNDERSTOOD** | Practitioner understands what a Case represents | Bounded reconciliation activity for a tax year | PENDING / `PASS` / `FAIL` |
| **CLIENT / TAX-YEAR CONTEXT CLEAR** | Client reference (e.g. Redwood Consulting) & 2025 clearly visible | Context visible at top of case | PENDING / `PASS` / `FAIL` |
| **TWO EVIDENCE ROLES UNDERSTOOD** | Clear distinction between Source A (Broker) and Source B (Tax Ledger) | Roles and extracted fields explicit | PENDING / `PASS` / `FAIL` |
| **EVIDENCE READINESS UNDERSTOOD** | Readiness state understood as structural suitability, not factual truth | Readiness disclaimers clear | PENDING / `PASS` / `FAIL` |
| **SAMPLE CASE** | 1-Click "Explore Sample Case" loads complete multi-asset scenario | Instant preload without manual uploads | PENDING / `PASS` / `FAIL` |
| **WORKFLOW ORIENTATION** | 4-Stage persistent workflow bar shows current and completed stages | 1. Sources → 2. Reconcile → 3. Findings → 4. Receipt | PENDING / `PASS` / `FAIL` |
| **RECONCILIATION** | Click "⚡ Run Deterministic Reconciliation" executes cleanly | Deterministic output generated | PENDING / `PASS` / `FAIL` |
| **RESULT NARRATIVE** | Evaluated count, Agreed (Green), Differences (Amber), Unresolved (Orange) | Attention items highlighted | PENDING / `PASS` / `FAIL` |
| **FINDING WHY** | Open Finding Why: explains what was compared, values, rule, and provenance | Explainable without tax advice | PENDING / `PASS` / `FAIL` |
| **OUTCOME RECEIPT GENERATION** | Generate case's live signed Outcome Receipt and download/export JSON | Live receipt JSON generated and exported | PENDING / `PASS` / `FAIL` |
| **LIVE RECEIPT VERIFICATION** | Drop generated live receipt into GUI Offline Verifier | Displays `PASS — Receipt Valid` | PENDING / `VALID` / `FAIL` |
| **TAMPERED RECEIPT VERIFICATION** | Make copy of live receipt, edit 1 value, drop into GUI Offline Verifier | Displays `FAIL — Receipt Invalid or Tampered` | PENDING / `INVALID` / `FAIL` |
| **QUIT** | Terminate VaultBasis process cleanly | Process exits | PENDING / `PASS` / `FAIL` |
| **RELAUNCH** | Double-click `VaultBasis.exe` again in Explorer | Boots cleanly | PENDING / `PASS` / `FAIL` |
| **PERSISTENCE** | Confirm previously created cases and receipts persist | Data intact in local SQLite | PENDING / `PASS` / `FAIL` |
| **INTERVENTION REQUIRED** | Developer tools, Terminal, Python, or code repair | Must be `NONE` | PENDING / `NONE` |

**Recipient Explanation (Verbatim Unprompted Response):**  
> *"In your own words, what did VaultBasis just do, and what would you investigate next?"*  
> [Record verbatim response]

**Logged Findings Classification:**
- `BLOCKER`: [None]
- `COMPREHENSION FAILURE`: [None]
- `OBSERVATION`: [None]

**Windows x64 Result:** `PENDING`  
**Stopped At:** `N/A`

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

