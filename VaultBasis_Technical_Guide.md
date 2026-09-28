# VaultBasis Edge — Technical / Administrator Guide
**Design Partner Preview v0.1.0-preview · RC2 qualification context**
**Audience:** IT administrator, security reviewer, or developer supporting a practitioner.**
**Companion docs:** Practitioner Quick Start (non-technical path) · Troubleshooting (failure path). This document is not the practitioner path.

---

## 1. What this build actually is

| Attribute | Value (verified 2026-09-28) |
|---|---|
| Entry point | `main.py` → `uvicorn.run(app, host="127.0.0.1", port=8000)` |
| API service | `edge/api/app.py` (FastAPI `VaultBasis Edge v0.1.0-preview`) |
| Packager | PyInstaller, spec `VaultBasis-Edge-v0.1.0-preview-macOS.spec` |
| macOS output | Single-file Mach-O 64-bit executable, **arm64 only** (`target_arch=None` = build-host arch) |
| Size | ~52 MB (`dist/VaultBasis-Edge-v0.1.0-preview-macOS`); ~35 MB zipped for distribution |
| Console | `console=True` — expects a terminal window to remain open; closing it stops the server |
| Browser auto-open | **Not implemented** in `main.py`. No `webbrowser.open()` call. Dashboard must be opened manually at `http://127.0.0.1:8000`. Any guide claiming auto-open is incorrect for this build. |
| Launcher | `launch_vaultbasis.command` — `chmod +x`, conditional `xattr -d com.apple.quarantine`, then exec. Must sit in same folder as the executable. The `.command` file itself receives a quarantine flag on download. |
| Signing | `codesign_identity=None` — **unsigned** |
| Notarization | **Not notarized**. `spctl -a -v` → `rejected`. |
| App bundle | None. Raw executable, no `.app`, no `Info.plist`, no bundle ID. |
| Data dir | `<repo>/data/` (SQLite `vaultbasis.db`, `keys/installation_ed25519.*`). Created at runtime via `DATA_DIR.mkdir`. Env override: `VAULTBASIS_DB_FILE`. |
| Bundled content | `apps/`, `schemas/` via spec `datas`. Verifier CLI at `apps/verifier/verify_receipt.py`, golden fixtures at `tests/fixtures/`. |

## 2. Runtime behavior

- Binds strictly to `127.0.0.1:8000`. No `0.0.0.0` binding in this build.
- CORS is permissive for local origins (`allow_origins=["*"]`) — acceptable for localhost-only preview, must be tightened before any non-localhost exposure.
- Key management: `InstallationKeyManager(KEY_DIR).ensure_keypair()` generates a local Ed25519 installation key on first run if absent. Signer key ID is exposed at `GET /api/health`.
- Reconciliation requires ≥2 ingested sources per case (`POST /api/cases/{id}/reconcile` returns 400 otherwise).
- Evidence bundle (`GET /api/cases/{id}/export`) zips: signed `receipt-v0.1.json`, `verify_receipt.py`, `schemas/receipt-v0.1.json`, raw source files under `evidence/`, `VERIFY_INSTRUCTIONS.txt`.
- Dashboard is served at `GET /` from `apps/web-dashboard/index.html`; verifier at `GET /verifier`; marketing at `GET /about`; schemas at `GET /schemas/{filename}`; OpenAPI at `/docs` (FastAPI default).

## 3. Egress statement (bounded — do not overclaim)

Do **not** state "never transmits" or "zero data egress" as absolutes in practitioner material. The accurate bounded claim for this build is:

> During the reconciliation workflow, transaction evidence is processed locally by VaultBasis Edge bound to localhost (127.0.0.1:8000). Qualification test AC-07 covers [bounded evidence — fill exact test scope]. General web browsing, OS telemetry, or user-initiated sharing of the Evidence Bundle are outside that boundary.

Absolute zero-egress language exceeds AC-07 evidence and must not ship.

## 4. Signature semantics (do not overclaim)

Correct: the Ed25519 signature over the canonicalized receipt payload proves **integrity and key attribution** under the scheme in `schemas/receipt/signing-v0.1.md` + `canonicalization-v0.1.md`, verifiable offline via `verify_receipt.py` or the web verifier.

Incorrect and must not ship:
- "proves you ran the software locally" — signature does not independently attest execution location.
- "verify standard compliance" / "simulate audits" — VaultBasis does not determine legal/tax compliance. It reports MATCHED / differences / unresolved items. The reviewer determines compliance.

## 5. Platform matrix (declared — qualification determines truth)

| Platform | Preview status |
|---|---|
| macOS 14+ / 15, Apple Silicon arm64 | Primary preview target. UAT-MAC-003 BLOCKED on Gatekeeper path; terminal workaround passes. |
| macOS Intel x86-64 | **Not built, not tested. Not supported.** arm64 binary will not execute. |
| Windows 11 x64 | **Qualification in progress.** Do not distribute Windows instructions until a Windows RC2 artifact is built and qualified. The macOS binary does not run on Windows. |
| Windows ARM, Linux desktop, iPadOS/iOS, Android, ChromeOS | **Not supported in MMP-1.** iPad is not an installer variation — localhost desktop executable architecture does not transfer. |

## 6. macOS Gatekeeper detail (why the Quick Start failed)

1. Downloaded files carry `com.apple.quarantine`. Unsigned + unnotarized + raw-executable form guarantees a Gatekeeper block on double-click.
2. On the tested Mac 3 / macOS 15 environment, "Open Anyway" in Privacy & Security did not appear for this quarantined standalone executable, so the documented "Open Anyway → instantly launch" recovery path was unavailable in that test. No universal claim about all Sequoia configurations is made.
3. Working workarounds in order: (a) `launch_vaultbasis.command` right-click → Open; (b) `xattr -d com.apple.quarantine <path>`; (c) `chmod +x` if execute bit was stripped.
4. Commercial direction (MMP-1.1): proper `.app` or `.pkg` packaging with Developer ID signing + notarization so no bypass is the normal path. "More Info → Run Anyway" / quarantine-stripping must remain preview friction, never the designed commercial UX.

## 7. Verification for administrators

```bash
# Architecture (expect: Mach-O 64-bit executable arm64)
file ./VaultBasis-Edge-v0.1.0-preview-macOS

# Signing (expect: rejected — unsigned preview)
spctl -a -v ./VaultBasis-Edge-v0.1.0-preview-macOS

# Quarantine flag (expect: com.apple.quarantine if freshly downloaded)
xattr ./VaultBasis-Edge-v0.1.0-preview-macOS ./launch_vaultbasis.command

# SHA-256 of distributed ZIP (compare against release record)
shasum -a 256 ./VaultBasis-Edge-*.zip
# UAT-MAC-003 reference: 2d08564d63a8c06f8c71e0f96d079cd6c68bee76a395db60ad321025194cc617

# Health check (after launch, terminal must stay open)
curl -s http://127.0.0.1:8000/api/health
```

## 8. Known preview defects (against immutable RC2 — do not patch RC2)

| ID | Severity | Summary |
|---|---|---|
| VB-RC2-UAT-001 | BLOCKER | macOS documented double-click / Open-Anyway path fails (Sequoia); terminal workaround required |
| VB-RC2-UAT-002 | HIGH | Guide version provenance: RC1 label on RC2 artifact |
| VB-RC2-UAT-003 | BLOCKER | Regulatory overclaim: "verify standard compliance" / "simulate audits" |
| VB-RC2-UAT-004 | HIGH | Assurance overclaim: receipt "proves local execution" |
| VB-RC2-UAT-005 | HIGH | Entity: "VaultBasis Inc." inaccurate |
| VB-RC2-UAT-006 | HIGH | Windows instructions shipped without qualified Windows artifact |
| VB-RC2-UAT-007 | HIGH | OS security bypass presented as normal install path |
| VB-RC2-UAT-008 (new) | MEDIUM | Browser auto-open claimed but not implemented in `main.py` |

If the executable, launcher, or packaging must change, cut **RC3**. Never silently repair RC2.

## 9. Product requirement for MMP-1.1 commercial packaging

1. A supported non-technical user MUST install and launch VaultBasis with no Terminal / PowerShell / shell command in the normal path.
2. OS security prompts MUST be satisfied by standard signing + notarization (macOS) / trusted signing + reputation (Windows), not by user-executed bypass steps.
3. Terminal / `xattr` / `chmod` / port / localhost material lives in Troubleshooting → Advanced and in this admin guide only — never in Quick Start.
