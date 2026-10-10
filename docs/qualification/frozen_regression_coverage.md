# VaultBasis MMP-1.5 Frozen Regression Coverage Matrix

**Document ID:** `VB-FRZ-COV-001`  
**Governing Standard:** `REGRESSION-COVERAGE-001` under `VB-FRZ-REG-001`  
**Date:** 2026-10-10  
**Current Release Candidates:** Candidate 13 (macOS arm64) & WIN-CANDIDATE-04 (Windows x64)  
**Governance Invariant:** A blank cell indicates a **KNOWN COVERAGE GAP**, not an implicit PASS. Blank physical cells remain scheduled until clean-machine qualification is executed.

---

## 1. Master Invariant Coverage Matrix

| Invariant ID | Behavioral Scope | Source Tests (Layer A) | macOS Packaged Tests (Layer B) | Windows Packaged Tests (Layer B) | Signed-Artifact Tests (Layer B/C) | Physical / Human Tests (Layer C) | Current Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`FRZ-MAC-001`** | macOS onedir bundle build | `PASS` | `PASS` | N/A | `PENDING SIGN` | `PENDING CLEAN MAC` | **AUTOMATED PASS** |
| **`FRZ-MAC-002`** | DMG volume creation & format | `PASS` | `PASS` | N/A | `PENDING SIGN` | `PENDING CLEAN MAC` | **AUTOMATED PASS** |
| **`FRZ-MAC-003`** | `VaultBasis.app` inside DMG root | `PASS` | `PASS` | N/A | `PENDING SIGN` | `PENDING CLEAN MAC` | **AUTOMATED PASS** |
| **`FRZ-MAC-004`** | `/Applications` shortcut in DMG | `PASS` | `PASS` | N/A | `PENDING SIGN` | `PENDING CLEAN MAC` | **AUTOMATED PASS** |
| **`FRZ-MAC-005`** | DMG copy preserves symlinks | `PASS` | `PASS` | N/A | `PENDING SIGN` | `PENDING CLEAN MAC` | **AUTOMATED PASS** |
| **`FRZ-MAC-006`** | Copied app launches from temp dir | `PASS` | `PASS` | N/A | `PENDING SIGN` | `PENDING CLEAN MAC` | **AUTOMATED PASS** |
| **`FRZ-MAC-007`** | Disconnected stdio (Finder mode) | `PASS` | `PASS` | N/A | `PENDING SIGN` | `PENDING CLEAN MAC` | **AUTOMATED PASS** |
| **`FRZ-MAC-008`** | Zero repository dependency | `PASS` | `PASS` | N/A | `PENDING SIGN` | `PENDING CLEAN MAC` | **AUTOMATED PASS** |
| **`FRZ-WIN-001`** | Windows setup installer build | `PASS` | N/A | `PASS` | `PENDING SIGN` | `PENDING CLEAN WIN` | **AUTOMATED PASS** |
| **`FRZ-WIN-002`** | Installer execution & extraction | `PASS` | N/A | `PASS` | `PENDING SIGN` | `PENDING CLEAN WIN` | **AUTOMATED PASS** |
| **`FRZ-WIN-003`** | Install under `%LOCALAPPDATA%` | `PASS` | N/A | `PASS` | `PENDING SIGN` | `PENDING CLEAN WIN` | **AUTOMATED PASS** |
| **`FRZ-WIN-004`** | Desktop & Start menu shortcuts | `PASS` | N/A | `PASS` | `PENDING SIGN` | `PENDING CLEAN WIN` | **AUTOMATED PASS** |
| **`FRZ-WIN-005`** | Installed EXE launches clean | `PASS` | N/A | `PASS` | `PENDING SIGN` | `PENDING CLEAN WIN` | **AUTOMATED PASS** |
| **`FRZ-WIN-006`** | Uninstall registry entry | `PASS` | N/A | `PASS` | `PENDING SIGN` | `PENDING CLEAN WIN` | **AUTOMATED PASS** |
| **`FRZ-CROSS-001`**| `/api/health` HTTP 200 HEALTHY | `PASS` | `PASS` | `PASS` | `PENDING SIGN` | `SCHEDULED` | **AUTOMATED PASS** |
| **`FRZ-CROSS-002`**| Dashboard loads "VaultBasis Edge" | `PASS` | `PASS` | `PASS` | `PENDING SIGN` | `SCHEDULED` | **AUTOMATED PASS** |
| **`FRZ-CROSS-003`**| Sample case loads cleanly | `PASS` | `PASS` | `PASS` | `PENDING SIGN` | `SCHEDULED` | **AUTOMATED PASS** |
| **`FRZ-CROSS-004`**| Production case creation & limit | `PASS` | `PASS` | `PASS` | `PENDING SIGN` | `SCHEDULED` | **AUTOMATED PASS** |
| **`FRZ-CROSS-005`**| 1099-DA & ledger intake parsing | `PASS` | `PASS` | `PASS` | `PENDING SIGN` | `SCHEDULED` | **AUTOMATED PASS** |
| **`FRZ-CROSS-006`**| Source confirmation & hashes | `PASS` | `PASS` | `PASS` | `PENDING SIGN` | `SCHEDULED` | **AUTOMATED PASS** |
| **`FRZ-CROSS-007`**| Deterministic reconciliation | `PASS` | `PASS` | `PASS` | `PENDING SIGN` | `SCHEDULED` | **AUTOMATED PASS** |
| **`FRZ-CROSS-008`**| Practitioner review workflow | `PASS` | `PASS` | `PASS` | `PENDING SIGN` | `SCHEDULED (UAT-22)` | **AUTOMATED PASS** |
| **`FRZ-CROSS-009`**| Signed Evidence Receipt export | `PASS` | `PASS` | `PASS` | `PENDING SIGN` | `SCHEDULED` | **AUTOMATED PASS** |
| **`FRZ-CROSS-010`**| Standalone offline verification | `PASS` | `PASS` | `PASS` | `PENDING SIGN` | `SCHEDULED` | **AUTOMATED PASS** |
| **`FRZ-CROSS-011`**| SQLite restart / WAL persistence | `PASS` | `PASS` | `PASS` | `PENDING SIGN` | `SCHEDULED` | **AUTOMATED PASS** |
| **`FRZ-CROSS-012`**| Zero dev-environment dependency | `PASS` | `PASS` | `PASS` | `PENDING SIGN` | `SCHEDULED` | **AUTOMATED PASS** |
| **`FRZ-TRUST-MAC-01`**| Unsigned Mac Gatekeeper reject | N/A | N/A | N/A | N/A | `PASS (DIAGNOSTIC)`| **PASS — EXPECTED PRE-SIGN** |
| **`FRZ-TRUST-MAC-02`**| Signed Mac Gatekeeper accept | `CONTRACT: PASS` | N/A | N/A | `PENDING SIGN` | `NOT RUN (PHYSICAL PENDING)` | **CONTRACT: PASS / PHYSICAL: NOT RUN** |
| **`FRZ-TRUST-WIN-01`**| Unsigned Windows SmartScreen | N/A | N/A | N/A | N/A | `SCHEDULED (PLAT-WIN-01B)`| **SCHEDULED PRE-SIGN** |
| **`FRZ-TRUST-WIN-02`**| Signed Windows Trusted Launch | `CONTRACT: PASS` | N/A | N/A | `PENDING SIGN` | `NOT RUN (PHYSICAL PENDING)` | **CONTRACT: PASS / PHYSICAL: NOT RUN** |

---

## 2. Layer Analysis & Gap Disclosure

### Layer A (Source Tests)
- **Coverage:** 100% of functional, deterministic, parsing, schema, and commercial invariants.
- **Suite Count:** 359 tests across 11 automated pre-commit gates.
- **Status:** **PASS / FROZEN**.

### Layer B (Packaged Artifact Tests)
- **macOS:** DMG creation, mounting, extraction, symlink integrity, detached daemon launch, health, dashboard, sample load, reconcile, and bundle export execute on macOS-14 GitHub runner.
- **Windows:** Setup installer compilation, embedded payload integrity, extracted binary launch, health, dashboard, sample load, reconcile, and evidence export execute on windows-2022 runner.
- **Status:** **PASS / FROZEN**.

### Layer C (Physical & Customer Environment Tests)
- **Pre-Sign Barriers (5 Remaining):**
  1. `PLAT-WIN-01B`: Physical Windows workstation execution (19-point UX checklist).
  2. `Installed Windows SHA`: Physical capture via PowerShell `Get-FileHash`.
  3. `UAT-30`: Windows/macOS reconciliation fact parity.
  4. `SEC-01`: macOS packet capture under `sudo tcpdump`.
  5. `UAT-22`: Human review lifecycle session.
- **Post-Sign Gates:**
  1. `UAT-29`: Unassisted zero-intervention clean-download on `MAC-SIGNED-RC1`.
  2. Final 5–8 practitioner validation cohort.
