# UAT-MAC-003: macOS Clean-Machine Test Record

**Date:** 2026-09-28  
**Tester:** Founder / Design Partner  
**Status:** BLOCKED — Release Blocker

---

## Mac Environment

| Field | Value |
|-------|-------|
| **Mac Model** | Mac (Apple Silicon M3 - "Mac 3") |
| **CPU Architecture** | Apple Silicon (arm64) |
| **macOS Version** | macOS 15 Sequoia (exact version to be filled) |

---

## Package Verification

| Check | Result |
|-------|--------|
| **Downloaded ZIP SHA-256** | `2d08564d63a8c06f8c71e0f96d079cd6c68bee76a395db60ad321025194cc617` — **MATCH / MISMATCH** (to be verified) |
| **Extracted Files** | 1. `VaultBasis_Quick_Start_Guide.html`<br>2. `VaultBasis-Edge-v0.1.0-preview-macOS` (52 MB executable)<br>3. `launch_vaultbasis.command` (launcher script) |
| **Executable Filename** | `VaultBasis-Edge-v0.1.0-preview-macOS` |
| **Executable Architecture** | Mach-O 64-bit executable **arm64** (Apple Silicon only) |
| **Code Signing** | **NOT SIGNED** (spctl: rejected) |
| **Notarization** | **NOT NOTARIZED** |
| **Quarantine Attribute** | Present (downloaded from web) |

---

## Test Execution

### Double-Click Behavior (Executable)
- **Action:** Double-clicked `VaultBasis-Edge-v0.1.0-preview-macOS` in Finder
- **macOS Message:** "Apple could not verify 'VaultBasis-Edge-v0.1.0-preview-macOS' is free of malware" / "macOS cannot verify the developer"
- **Result:** **BLOCKED** — Gatekeeper prevents execution entirely; no Terminal window appears

### Double-Click Behavior (Launcher Script)
- **Action:** Double-clicked `launch_vaultbasis.command` in Finder
- **macOS Message:** Terminal opens but script may be blocked by Gatekeeper
- **Result:** **NEEDS VERIFICATION** — .command files also receive quarantine flag

### System Settings → Privacy & Security (observed on test machine only)
- **"Open Anyway" Button:** **DID NOT APPEAR on the tested Mac 3 / macOS 15 environment** for this quarantined standalone executable
- **Result:** Documented "Open Anyway" recovery path was **unavailable/unsuccessful in this test**. No broader claim about all Sequoia systems is made — this records only what was observed here.

### Terminal Method (xattr)
- **Command Tested:** `xattr -d com.apple.quarantine ~/Downloads/VaultBasis-Edge-v0.1.0-preview-macOS`
- **Result:** Removes quarantine, executable then runs from command line
- **Browser Auto-Open:** **NO — not implemented in `main.py` (verified: no `webbrowser.open()` call). Manual open at `http://127.0.0.1:8000` required.**
- **Terminal Window:** **YES** — Must stay open while server runs
- **localhost Response:** **YES** — Dashboard loads on manual open

---

## Outcome

| Metric | Result |
|--------|--------|
| **Normal User Path (Double-Click)** | **BLOCKED** |
| **Documented "Open Anyway" Path** | **FAILS on tested Mac 3 / macOS 15 env** |
| **Terminal Workaround** | **WORKS** (but requires technical skill) |
| **Launcher Script Path** | **UNTESTED** (likely blocked same as executable) |
| **Overall** | **RELEASE BLOCKER** |

---

## Root Cause Analysis (Preliminary)

1. **No Code Signing** — PyInstaller build has `codesign_identity=None`
2. **No Notarization** — Not submitted to Apple for notarization
3. **arm64 Only** — `target_arch=None` defaults to build machine (Apple Silicon); no universal binary
4. **Raw Executable** — Not packaged as `.app` bundle; no Info.plist, no bundle ID
5. **Quarantine Handling** — Launcher script helps but is itself subject to quarantine

---

## Defects Opened

| Defect ID | Severity | Class | Summary |
|-----------|----------|-------|---------|
| VB-RC2-UAT-001 | RELEASE BLOCKER | PACKAGING/DISTRIBUTION | macOS documented installation path fails on clean-machine test |
| VB-RC2-UAT-002 | HIGH | DOCUMENTATION/PROVENANCE | Quick Start identifies package as RC1 while distributed artifact is RC2 |
| VB-RC2-UAT-003 | RELEASE BLOCKER | CLAIMS/REGULATORY | Quick Start claims "verify standard compliance" |
| VB-RC2-UAT-004 | HIGH | ASSURANCE CLAIM | Quick Start claims signed receipt proves local execution |
| VB-RC2-UAT-005 | HIGH | LEGAL/IDENTITY | Quick Start contains inaccurate "VaultBasis Inc." |
| VB-RC2-UAT-006 | HIGH | SUPPORT-BOUNDARY | Windows instructions presented without demonstrated RC2 Windows qualification |
| VB-RC2-UAT-007 | HIGH | PACKAGING/UX/SECURITY | Quick Start relies on OS security bypass as normal installation path |

---

## Next Steps

1. **Do NOT modify vaultbasis-mmp1-rc2** — Keep RC2 immutable
2. **Root-cause the packaging defects** — Determine if documentation-only or requires package change
3. **If package change required → Cut RC3** — Then test systematically across declared OS matrix
4. **Declare supported platforms explicitly** — e.g., macOS 14+ Apple Silicon only for MMP-1
5. **Rewrite Quick Start as three artifacts** — Practitioner Quick Start, Troubleshooting, Technical Guide