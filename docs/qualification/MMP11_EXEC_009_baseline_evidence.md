# MMP11-EXEC-009 Baseline Evidence & Physical Qualification Failure Record

## 1. Candidate Baseline Identity
- **Source Commit:** `5cfb116715697f788c6cf4b44605ae119278f87a`
- **Candidate Label:** Release Candidate 3 (RC3)
- **CI Pipeline Execution:** CI Run #67 (Industrial Validation Pipeline)
- **Mac Inner-ZIP Artifact:** `VaultBasis-RC3-macOS-arm64.zip`
- **Windows Inner-ZIP Artifact:** `VaultBasis-RC3-Windows-x64.zip`
- **Baseline Qualification Status:** **FAILED QUALIFICATION BASELINE (DO NOT DISTRIBUTE)**

---

## 2. Physical Recipient Test Observations

### A. Windows x64 (Physical Execution)
- **Classification:** `RECIPIENT_PATH = FAIL`, `APPLICATION_STARTUP = FAIL`, `PRACTITIONER_JOURNEY = NOT TESTABLE`
- **Observed Traceback / Exception:**
  ```text
  Failed to execute script 'main' due to unhandled exception
  ValueError: Unable to configure formatter 'default'
  Traceback (most recent call last):
    File "main.py", line 32, in <module>
    File "uvicorn\main.py", line 587, in run
    File "uvicorn\config.py", line 380, in configure_logging
    File "logging\config.py", line 811, in dictConfig
    ValueError: Unable to configure formatter 'default'
  ```
- **Root Cause Analysis (RCA):**
  1. In PyInstaller windowed mode (`--windowed` / `console=False`), standard file descriptors (`sys.stdout` and `sys.stderr`) are set to `None` on Windows when launched directly from Windows Explorer / GUI.
  2. When `uvicorn.run()` initializes default logging without custom override, `logging.config.dictConfig` attempts to bind stream handlers to `sys.stderr` and instantiate `uvicorn.logging.DefaultFormatter`. Because `sys.stderr` is `None` in the frozen GUI environment, `dictConfig` fails with `ValueError: Unable to configure formatter 'default'`.
  3. **Why CI produced a false green:** The CI `launch_gate` launched the executable via `subprocess.Popen(..., stdout=subprocess.PIPE, stderr=subprocess.STDOUT)`, which supplied valid open OS pipe handles for standard streams. The physical recipient double-clicked the executable in Windows Explorer where no pipe was attached, immediately exposing the unhandled exception.

### B. macOS arm64 (Physical Execution)
- **Classification:** `PACKAGE_EXTRACTION = PASS`, `NORMAL GATEKEEPER GUI RECOVERY = PASS`, `EDGE_RUNTIME = PASS`, `AUTO_WORKSPACE_OPEN = FAIL / INCONSISTENT`, `MANUAL LOCAL ACCESS = PASS`, `OFFLINE_VERIFIER ORIGINAL = PASS`, `PRACTITIONER_COMPREHENSION = FAIL`, `RECIPIENT_PATH = FAIL OVERALL`
- **Observations:**
  1. **Gatekeeper:** Unsigned preview encountered expected macOS security prompt; normal GUI path (System Settings → Privacy & Security → Open Anyway) succeeded without command-line intervention.
  2. **Launch & Navigation:** Local backend server booted on `127.0.0.1:8000`, but default browser failed to auto-open reliably across macOS versions, requiring manual navigation to `http://127.0.0.1:8000`.
  3. **Practitioner Comprehension Failure:** The Edge dashboard immediately presented generic "Source Document Ingestion" without contextual domain explanation. An unfamiliar practitioner could not discern:
     - Who the case was for (no client / tax year orientation).
     - What Source A and Source B represent (Broker Form 1099-DA vs. Tax-Ledger / Koinly report).
     - Why these two sources are being compared.
     - What deterministic reconciliation transformation is performed.
     - What the outcome states (Agreed vs. Difference vs. Unresolved) signify.
     - What the Outcome Receipt establishes (cryptographic integrity & schema compatibility) vs. what it does NOT establish (Tax Correctness = NOT DETERMINED).
     - The presence of raw Python files (`verify_receipt.py`) created confusion about developer dependencies.

---

## 3. Remediation Directive
All findings are bound under `MMP11-EXEC-009A`. No further candidate promotion or distribution to Associate-001 is permitted until the full remediation sequence is qualified.
