# UAT-WIN-001: Windows Clean-Machine Download Test Record

**Date:** 2026-09-28
**Tester:** Founder / Design Partner
**Machine:** Windows desktop (exact version + x64/ARM64 to be filled)
**Status:** BLOCKED — 2 release blockers. No further testing of this artifact;
diminishing value. Screenshot of downloaded package contents on file with tester.
**Do NOT modify RC2. Open defects against it.**

---

## Observed (downloaded via the live design-partner endpoint)

| Check | Result |
|---|---|
| Extracted executable | `VaultBasis-Edge-v0.1.0-preview-macOS` (~52.3 MB, Mach-O arm64) — **macOS binary on Windows; cannot execute** |
| Extracted guide | `VaultBasis_Quick_Start_Guide.html` — **superseded RC1-era document** |
| Windows-native installer | **Absent** |
| Current practitioner Quick Start / Troubleshooting | **Absent from package** |

## Defects

| ID | Severity | Class | Summary |
|---|---|---|---|
| VB-RC2-UAT-009 | RELEASE BLOCKER | DISTRIBUTION / PLATFORM ROUTING | Windows client served macOS Edge executable as default download. Expected: qualified Windows artifact, explicit platform selector, or "platform not currently available" — never a wrong-platform binary. First negative vector: Windows → macOS artifact = FAIL. |
| VB-RC2-UAT-010 | RELEASE BLOCKER | RELEASE ASSEMBLY / CONTENT | Distributed package contains superseded Quick Start (RC1 labeling, "local Edge Daemon", Gatekeeper/SmartScreen bypass as normal path, terminal/localhost workflow, "Simulate Audits", "verify standard compliance", receipt-proves-local-execution, "VaultBasis Inc."). Expected: package assembled from frozen release documentation source with version binding (binary RC == guide RC == manifest RC); stale guide fails the pipeline. |

## Root-cause direction (not a tester workaround)
Repository fixes alone cannot resolve this: the endpoint serves a preassembled stale
ZIP, not an artifact constructed from the release commit. RC3 requires a deterministic
release-assembly pipeline (frozen commit → per-platform build → sign → platform tests →
equivalence → package assembly with correct binary + current guides + metadata →
hashes/manifest → qualification → publication) plus post-publication verification
(download as a practitioner, hash, inspect, compare to manifest).

## Next
Preserve this download + screenshot as evidence. Next Windows clean-machine round only
against the frozen RC3-WIN artifact served by its qualified endpoint.
