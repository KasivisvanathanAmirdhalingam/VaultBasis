# MMP11-EXEC-009A Physical Recipient Qualification Record

> **Governance State:** `WINDOWS_DISTRIBUTION_QUALIFIED / MACOS_FUNCTIONAL_MANUAL_PASS`  
> **Rule:** No public distribution until physical recipient tests pass without developer intervention. Windows distribution qualified under Run 37197525586; macOS distribution pending Developer ID signing/notarization under MMP11-DIST-MAC-004.

---

## 1. Candidate Identity & Governance Freeze

### Qualified Candidate: Windows x64 Distribution (Candidate 4 / Frozen Record)
- **Source SHA:** `bd9b1e79e112443f8fdb2a2293d94d275774c269`
- **Candidate Governance State:** `DISTRIBUTION_QUALIFIED` (Task `MMP11-DIST-WIN-004` CLOSED)
- **CI Run ID:** `37197525586` (Native Windows & macOS build workflow)
- **Windows x64 Package:** `VaultBasis-RC3-Windows-x64.zip`
  - **SHA-256:** `434957f1ccc5ee1ba8b398830d88e348c3f6785d721a9b26a1d2e8c5e0c5f41b`
  - **Size:** 16,664,052 bytes
  - **Release Content Gate:** `PASS` (11 required package members at exact paths; 0 Mach-O/FAT binaries; 0 `.app` bundles; 0 stray directories)
  - **Package Member Inventory (Exact 11 Paths):**
    1. `VaultBasis.exe`
    2. `apps/sandbox-studio/dist/index.html`
    3. `apps/sandbox-studio/dist/verifier.html`
    4. `apps/sandbox-studio/dist/assets/index.js`
    5. `apps/sandbox-studio/dist/assets/index.css`
    6. `apps/sandbox-studio/dist/assets/verifier.js`
    7. `apps/sandbox-studio/dist/assets/verifier.css`
    8. `schemas/receipt-v0.1.json`
    9. `samples/sample_broker_1099da.csv`
    10. `samples/sample_tax_ledger.csv`
    11. `samples/sample_client_profile.json`
- **Exported Evidence Bundle:** `VaultBasis_Evidence_CASE-SAMPLE-2025.zip`
  - **SHA-256:** `403de48c8a59b6893b8819090cbeb4b17e278baaf57a753ae561845c53a0eea4`
  - **Size:** 5,825 bytes
  - **Evidence Allowlist Gate:** `PASS` (5 items: `receipt-v0.1.json`, `schemas/receipt-v0.1.json`, 2 evidence CSVs, `VERIFY_INSTRUCTIONS.txt`; zero `.py`/`.pyc` code leaks, zero `technical-verification/` directory)
- **Physical Smoke Execution:**
  - Double-click `VaultBasis.exe` in Explorer → Starts cleanly (`PASS`)
  - Auto browser open to `http://127.0.0.1:8000` (`PASS`)
  - 1-Click "Explore Sample Case" (`POST /api/sample-case/load`) (`PASS`)
  - Run Deterministic Reconciliation (`PASS`)
  - Download & Export Evidence Bundle (`PASS`)
  - GUI Offline Receipt Verification with exported receipt (`PASS`)

### macOS arm64 Candidate (Candidate 4 / Functional Manual Pass)
- **Source SHA:** `bd9b1e79e112443f8fdb2a2293d94d275774c269`
- **Candidate Governance State:** `FUNCTIONAL_MANUAL_PASS` (Formal signing/notarization tracked under `MMP11-DIST-MAC-004`)
- **CI Run ID:** `37197525586`
- **Mac arm64 Package:** `VaultBasis-RC3-Mac-arm64.zip`
  - **SHA-256:** `9ec370c1c875d654f15dcfcbba7339d6b5e084323e0ec346f00e9ec19d08655c`
  - **Size:** 16,423,736 bytes
  - **Manual Smoke Test:** Launch, sample case load, reconciliation, evidence export, and GUI offline verification all verified working.
  - **Distribution Status:** Pending formal Developer ID code signing, hardened runtime, notarization stapling, and Gatekeeper clean-download verification under `MMP11-DIST-MAC-004`.

### Historical Failed / Superseded Candidates (Preserved Failure Evidence)
- **Candidate 1 (Mac Launch Failure):** Source SHA `641d2b135ab0dcfa3bdf3b5edc95f4d1a3d5511d` (CI Run `37120319044`)
  - Mac arm64 Inner-ZIP SHA-256: `8e8e77290a8544c0e9fe72f5c862cb942e2dcc293ce80b9f8d93ff7565c2bb24` (FAILED: Gatekeeper / port contention)
  - Windows x64 Inner-ZIP SHA-256: `6f25843188aaf91b6688902e87bc487f68bc76999f077745876ca0b926bc52f3`
- **Candidate 2 (Windows HTTP 500 & Mac LaunchServices -47 Failures):** Source SHA `160f4d7f8cfceebbcac2b33a12d1c0e67b7d0659` (CI Run `37123027673`)
  - Mac arm64 Inner-ZIP SHA-256: `4f6c0f1cc98319e5f21e4beb2a00c7ee54260c2e2a9eeb421884a8e0e633e832` (FAILED: LaunchServices OSStatus error -47 on physical Mac recipient launch)
  - Windows x64 Inner-ZIP SHA-256: `7b9a99c6af97dbaf2ee896938e67df41181c125e2095296da57498843f8c2061` (FAILED: `GET /` returned HTTP 500 "Internal Server Error" on physical Windows machine)
- **Candidate 3 (Legacy Mac Packaging Superseded):**
  - Mac arm64 ZIP SHA-256: `b7935421297593c6be5374e2d43141cf5e5cf6dd05ec2c6104e76d9595ca5b24` (22.4 MB - Superseded by clean bounded build `9ec370c1...` 16.4 MB)

---

## 2. Windows x64 Physical Recipient Qualification (Qualified Record)

- **Target Machine:** Physical Windows x64 Machine (Windows 11)
- **Architecture:** x64
- **Tester Role:** Independent Recipient / Pair Verification
- **Package Tested:** `VaultBasis-RC3-Windows-x64.zip` (`434957f1...`)

| Check | Gate Description | Expected | Actual Result |
|---|---|---|---|
| **DOWNLOAD** | Download ZIP artifact from CI Run 37197525586 | Full archive downloaded | `PASS` |
| **NORMAL EXTRACTION** | Extract ZIP via Windows Explorer standard Extract All | Clean folder layout, `VaultBasis.exe` beside `_internal/` | `PASS` |
| **APPLICATION_RUNTIME** | Double-click `VaultBasis.exe` in Explorer | Process starts, local port becomes reachable | `PASS` |
| **AUTO_WORKSPACE_OPEN** | Default web browser automatically launches and opens workspace | Browser loads `http://127.0.0.1:8000` automatically | `PASS` |
| **WORKSPACE_RESPONSE** | Root dashboard (`GET /`) renders functional UI | HTTP 200 with VaultBasis Edge UI | `PASS` |
| **SAMPLE_CASE_LOAD** | Click "Explore Sample Case" | Sample broker + ledger case pre-populated | `PASS` |
| **RECONCILIATION** | Run Deterministic Reconciliation | Deterministic findings calculated | `PASS` |
| **EVIDENCE_EXPORT** | Download Evidence Bundle ZIP | Exported ZIP downloaded | `PASS` |
| **OFFLINE_VERIFICATION** | Verify exported receipt via Verifier UI | Displays `PASS — Receipt Valid` | `PASS` |
| **EVIDENCE_ALLOWLIST** | Audit bundle contents | 5 allowlist items only; 0 code leaks | `PASS` |
| **INTERVENTION REQUIRED** | Developer tools, Terminal, Python, or code repair | Must be `NONE` | `NONE` |

**Overall Windows Result:** `PASS` (`DISTRIBUTION_QUALIFIED`)  
**Disposition:** `MMP11-DIST-WIN-004` CLOSED and QUALIFIED.

---

## 3. macOS arm64 Physical Recipient Qualification (Functional Manual Pass)

- **Target Machine:** Apple Silicon Mac (M1/M2/M3/M4)
- **Architecture:** arm64
- **Tester Role:** Recipient Smoke Test
- **Package Tested:** `VaultBasis-RC3-Mac-arm64.zip` (`9ec370c1...`)

| Check | Gate Description | Expected | Actual Result |
|---|---|---|---|
| **NORMAL EXTRACTION** | Extract ZIP via Archive Utility in Finder | `VaultBasis.app` intact | `PASS` |
| **APPLICATION_RUNTIME** | Open `VaultBasis.app` | App starts cleanly | `PASS` |
| **AUTO_WORKSPACE_OPEN** | Browser opens workspace | Default browser opens `http://127.0.0.1:8000` | `PASS` |
| **SAMPLE CASE** | 1-Click "Explore Sample Case" loads complete multi-asset scenario | Instant preload | `PASS` |
| **RECONCILIATION** | Run Deterministic Reconciliation | Deterministic findings rendered | `PASS` |
| **OUTCOME RECEIPT** | Export Evidence Bundle ZIP | Exported ZIP generated | `PASS` |
| **OFFLINE VERIFICATION**| Offline Verifier verification | Displays `PASS — Receipt Valid` | `PASS` |
| **FORMAL DISTRIBUTION**| Developer ID Signing, Hardened Runtime, Notarization | Signed & Notarized | `PENDING` (Tracked in `MMP11-DIST-MAC-004`) |

**macOS arm64 Result:** `FUNCTIONAL_MANUAL_PASS`  
**Next Governance Step:** `MMP11-DIST-MAC-004` for formal CI-driven Developer ID signing and notarization.

---

## 4. State Transition Rule
- **Windows x64:** `DISTRIBUTION_QUALIFIED` (Run 37197525586 / SHA `434957f1...`)
- **macOS arm64:** `FUNCTIONAL_MANUAL_PASS` (Run 37197525586 / SHA `9ec370c1...`) — Awaiting `MMP11-DIST-MAC-004` for formal distribution qualification.

