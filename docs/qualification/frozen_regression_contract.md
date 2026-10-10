# VaultBasis MMP-1.5 Frozen Regression Contract

**Document ID:** `VB-FRZ-REG-001`  
**Standard:** Granite-Grade / Left-Shift Maximum / Immutable Release Baseline  
**Authority:** Canonical Release Engineering Directive `REGRESSION-COVERAGE-001`  
**Current State:** `FROZEN — RELEASE INVARIANT`  
**Governing Rule:** Once a VaultBasis function has been validated and qualified, its behavior is **FROZEN**. Every relevant change must execute the complete applicable regression suite proving that validated functions remain intact. Modifying, relaxing, or bypassing a frozen behavior is strictly prohibited without an explicit **Mode 3 Authorized Change Ticket**.

---

## 1. Regression Layer Architecture

To prevent conflation between development test passes, packaged artifact checks, and real operating system trust boundaries, regression coverage is partitioned into three immutable layers:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER A — SOURCE CODE REGRESSION (Automated CI / Local)                   │
│ Unit tests, schema validators, deterministic engine, commercial policies │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER B — PACKAGED ARTIFACT REGRESSION (Clean Runner Isolation)           │
│ Real DMG mount, extraction, symlink check, Windows installer execution,   │
│ isolated daemon launch, API health, sample load, reconcile, bundle export │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER C — PHYSICAL CUSTOMER ENVIRONMENT REGRESSION (Clean Machines)       │
│ Browser download, OS quarantine metadata, Gatekeeper/SmartScreen trust,  │
│ GUI Finder/Explorer double-click, zero-terminal practitioner journey     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Frozen Behavioral Invariants

### 2.1 macOS Packaging & Extraction (`FRZ-MAC-*`)

| Invariant ID | Frozen Requirement | Technical Implementation | Layer A Test | Layer B Packaged Test | Layer C Physical Test |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`FRZ-MAC-001`** | Candidate package builds into clean onedir bundle | `PyInstaller VaultBasis-RC3-macOS.spec` | Build script invocation | `dist/VaultBasis.app` executable exists, Mach-O thin arm64 | Manual arm64 host verification |
| **`FRZ-MAC-002`** | Single-layer customer DMG mounts cleanly | `hdiutil create -format UDZO` | Spec validation | `hdiutil attach -nobrowse` returns exit code 0 | Finder volume mount |
| **`FRZ-MAC-003`** | `VaultBasis.app` bundle present inside root volume | DMG staging directory assembly | Path existence check | Volume root contains `VaultBasis.app` | Finder visual inspection |
| **`FRZ-MAC-004`** | Applications shortcut symlink present in DMG | `os.symlink('/Applications', ...)` | Link target check | `readlink(mnt/Applications) == '/Applications'` | Finder drag-and-drop target |
| **`FRZ-MAC-005`** | App copy from DMG preserves framework symlinks | `shutil.copytree(..., symlinks=True)` | Symlink traversal unit test | PyInstaller `python3.X` and dynamic dylib symlinks verified intact | Clean `/Applications` install |
| **`FRZ-MAC-006`** | Copied app launches from temporary/isolated path | Standalone daemon process spawn | Subprocess unit test | Launch copied app from temp directory without dev repo | Drag to desktop, launch |
| **`FRZ-MAC-007`** | App launches with disconnected stdio (`DEVNULL`) | Finder-style launch simulation | GUI runner tests | `Popen(..., stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)` responds healthy | Finder double-click launch |
| **`FRZ-MAC-008`** | App operates with zero repository dependency | Independent binary bundle | `edge/api/app.py` isolation | Executable runs in directory lacking `.git`, `requirements.txt`, or Python | Clean machine (no developer tools) |

---

### 2.2 Windows Packaging, Installation & Execution (`FRZ-WIN-*`)

| Invariant ID | Frozen Requirement | Technical Implementation | Layer A Test | Layer B Packaged Test | Layer C Physical Test |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`FRZ-WIN-001`** | Windows self-extracting setup installer builds | `scripts/installer_windows.py` + PyInstaller onefile | Packaging unit check | `dist/VaultBasis-Setup-1.5.0-rc3.exe` exists, PE x64 | Windows host build |
| **`FRZ-WIN-002`** | Installer executes cleanly and extracts payloads | Embedded zip payload extraction | Zipslip path checks | Installer executes and unpacks without error | Interactive double-click |
| **`FRZ-WIN-003`** | Application installs under `%LOCALAPPDATA%\VaultBasis` | Per-user non-admin destination | Path resolution test | `%LOCALAPPDATA%\VaultBasis\VaultBasis.exe` exists and has valid SHA | File Explorer verification |
| **`FRZ-WIN-004`** | Desktop and Start Menu shortcuts created | PowerShell WScript.Shell COM script | Shortcut generator test | Shortcut targets `%LOCALAPPDATA%\VaultBasis\VaultBasis.exe` | Desktop icon & Start Menu pin |
| **`FRZ-WIN-005`** | Installed `VaultBasis.exe` launches without Python or repo | PyInstaller standalone executable | Process launch test | Installed executable starts in clean environment without PATH python | Physical Windows launch |
| **`FRZ-WIN-006`** | Clean uninstall registration recorded | `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall` | Registry utility test | Uninstall registry keys exist with display name, version, and uninstall string | Settings > Installed Apps verification |

---

### 2.3 Cross-Platform Functional & Commercial Invariants (`FRZ-CROSS-*`)

| Invariant ID | Frozen Requirement | Technical Implementation | Layer A Test | Layer B Packaged Test | Layer C Physical Test |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`FRZ-CROSS-001`**| `/api/health` returns HTTP 200 `status: HEALTHY` | `edge/api/routes.py` health endpoint | `tests/unit/test_health.py` | Packaged runner polls `GET /api/health` and verifies status | Browser navigation to `/api/health` |
| **`FRZ-CROSS-002`**| Root dashboard `GET /` loads VaultBasis Edge UI | FastHTML / static assets | `tests/unit/test_dashboard.py` | Packaged runner GET `/` returns HTTP 200 with "VaultBasis Edge" | Browser visual verification |
| **`FRZ-CROSS-003`**| Bundled sample case loads via `POST /api/sample-case/load` | `edge/api/routes.py` sample loader | `test_uat28_offline_air_gapped_journey.py` | Packaged runner executes sample load and confirms `CASE-SAMPLE-2025` | Click "Load Sample Case" in UI |
| **`FRZ-CROSS-004`**| Production case creation enforces capacity limit | `edge/commercial/policy.py` case counter | `tests/unit/test_mmp15_license_engine.py` | Packaged app validates monotonic increment and limit gate | Create Case modal interaction |
| **`FRZ-CROSS-005`**| Form 1099-DA and tax ledger intake parses cleanly | `edge/intake/` broker and ledger parsers | `tests/quality/integration/test_uat*.py` | Packaged runner parses sample CSVs without data loss | Drag-and-drop CSV files in UI |
| **`FRZ-CROSS-006`**| Selected source confirmation binds cryptographic digests | Source confirmation contract | `test_reconciliation_engine_semantic_equivalence.py` | Packaged runner records SHA-256 source bindings in case store | UI source selection checklist |
| **`FRZ-CROSS-007`**| Deterministic reconciliation executes under `VB_US_1099DA_2025_R1` | `edge/assurance/reconciliation_engine.py` | Golden boundary test suite | Packaged app runs reconcile and verifies expected status | Click "Run Reconciliation" |
| **`FRZ-CROSS-008`**| Practitioner review workflow transitions operate immutably | Case review state model | `tests/quality/test_uat22_review_lifecycle.py` | Packaged app records review notes and sign-off without math drift | Practitioner review modal |
| **`FRZ-CROSS-009`**| Signed Evidence Receipt generated under Contract v0.1 | `edge/evidence/receipt.py` (Ed25519) | `test_uat24_standalone_offline_verifier.py` | Packaged app exports ZIP containing valid `receipt.json` | Download Evidence Package |
| **`FRZ-CROSS-010`**| Standalone verifier verifies receipt integrity offline | `apps/verifier/verify_receipt.py` | Verifier golden test suite | Verifier script executes against exported receipt with exit code 0 | Standalone verifier tool |
| **`FRZ-CROSS-011`**| Database restart preserves case & license state | SQLite WAL mode + atomic transactions | `test_uat27_crash_recovery_wal_durability.py` | Terminate and restart daemon; verify persisted case records | OS reboot / restart app |
| **`FRZ-CROSS-012`**| Zero runtime dependency on source tree / dev environment | Frozen dependency isolation | Harness isolation tests | App runs in clean directory without source files | Non-developer workstation |

---

### 2.4 Operating System Trust Boundary Invariants (`FRZ-TRUST-*`)

| Invariant ID | Target Stage | Operating System Policy | Expected Behavior | Verification Requirement |
| :--- | :--- | :--- | :--- | :--- |
| **`FRZ-TRUST-MAC-01`** | Pre-Sign (Candidate 13) | Web download attaches `com.apple.quarantine`; ad-hoc unsigned bundle | **`EXPECTED_REJECT_PRE_SIGN`** (Gatekeeper modal: *"is damaged and can't be opened"*) | Diagnostic confirmation only; no product changes |
| **`FRZ-TRUST-MAC-02`** | Post-Sign (`MAC-SIGNED-RC1`) | Web download attaches `com.apple.quarantine`; Developer ID signed & notarized | **`MUST_ACCEPT`** (Clean Finder double-click launch; zero warnings, zero bypass, zero terminal) | Physical clean-machine test on macOS 14/15 |
| **`FRZ-TRUST-WIN-01`** | Pre-Sign (`WIN-CANDIDATE-04`) | Web download on Windows; unsigned setup installer | **`EXPECTED_REPUTATION_PROMPT_PRE_SIGN`** (SmartScreen unknown publisher prompt) | Diagnostic confirmation only; no product changes |
| **`FRZ-TRUST-WIN-02`** | Post-Sign (`WIN-SIGNED-RC1`) | Web download on Windows; Microsoft Trusted Signing certificate | **`TRUSTED_LAUNCH`** (Publisher verified: "VaultBasis EURL"; clean install into `%LOCALAPPDATA%`) | Physical clean-machine test on Windows 11 |

---

## 3. Mandatory Change Classification System

Every modification proposed to the repository must be explicitly classified using one of the following canonical tags:

```text
+---------------------+---------------------------------------------------------------------------------+
| CLASSIFICATION TAG  | PERMITTED SCOPE & MANDATORY REGRESSION PIPELINE                                 |
+---------------------+---------------------------------------------------------------------------------+
| DOCS_ONLY           | Markdown / documentation files only. Source content gates run. No rebuilds.     |
| MARKETING_ONLY      | Static marketing web portal (`apps/web-marketing/`). Catalog tests run.          |
| QUALIFICATION_HARNESS| Test files, CI workflows, gate scripts. Full 11-gate suite runs. Zero candidate |
|                     | byte changes permitted.                                                         |
| PRODUCT_UI          | Edge dashboard (`apps/web-dashboard/`). Full Source + Mac + Win packaging runs. |
| PRODUCT_RUNTIME     | Core engine, API, database (`edge/`). Full Source + Full Packaging + Candidate  |
|                     | identity increments to new candidate.                                           |
| PACKAGING           | Build specs, packaging scripts (`scripts/build_*`). Full packaging runs.        |
| COMMERCIAL          | License engine, catalog schemas. Commercial suite + Packaging regression runs.  |
| SECURITY            | Cryptographic routines, socket bindings, evidence schemas. Full regression.     |
| MODE3_AUTHORIZED    | Explicit authorized bug fix or requirement change. Requires Mode 3 ticket.      |
+---------------------+---------------------------------------------------------------------------------+
```

### Fail-Closed Enforcement Rule
If any commit modifies files under `edge/`, `apps/web-dashboard/`, `scripts/build_*`, `scripts/installer_*`, or schemas without an explicit classification or with missing regression execution:
$$\textbf{VALIDATION GATES FAIL CLOSED} \longrightarrow \textbf{PROMOTION BLOCKED}$$

---

## 4. Mode Discipline: Mode 1 vs Mode 3

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│ MODE 1 — EVIDENCE & QUALIFICATION (Current Operating Mode)                       │
│ • Product runtime, UI, deterministic logic, schemas, and packaging are FROZEN.   │
│ • Permitted: Running tests, capturing physical evidence, qualification docs.    │
│ • FORBIDDEN: Modifying runtime code, loosening tests, patching candidate bytes.  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼ (Requires explicit defect / mandate)
┌─────────────────────────────────────────────────────────────────────────────────┐
│ MODE 3 — AUTHORIZED REMEDIATION (Strict Exception Pipeline)                     │
│ 1. Formal Ticket Opened: Defect statement + root cause analysis.                 │
│ 2. Impacted Invariants Identified: Explicit list of affected FRZ-* IDs.          │
│ 3. Minimal Targeted Fix Applied: Restricted strictly to identified components.   │
│ 4. New Candidate Minted: Candidate bytes change -> increment candidate number.  │
│ 5. Full Requalification Executed: Complete Layer A + Layer B suites rerun.       │
│ 6. Immediate Return to Mode 1.                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```
