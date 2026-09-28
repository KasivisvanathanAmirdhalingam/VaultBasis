# RC3 — Packaging RC Scope (macOS only, no feature changes)

**Status:** PROPOSED — RC2 remains sealed and immutable.
**Objective (narrow):** Make the already-qualified VaultBasis assurance capability installable and launchable by an ordinary supported macOS user with no Terminal commands and no security-bypass instructions in the normal path.

## Non-goals (explicitly out of RC3)
- No changes to reconciliation logic, semantics, Evidence Contract / receipt schema, assurance levels, or parsers.
- No Windows / Linux / tablet builds. Lessons from macOS RC3 apply later.
- No new features, no UI redesign beyond lifecycle/startup-error handling required for installability.

## Target journey (RC3)
Download → Open installer/package → Install / move to Applications → Open VaultBasis → VaultBasis starts → Workspace opens automatically → Start Sample Case. Having trouble → Troubleshooting.

## Work items
1. Proper macOS `.app` (Info.plist, bundle ID, version) or signed `.pkg`; decide one.
2. Developer ID signing + notarization so Gatekeeper passes without `xattr` / Open-Anyway in normal path.
3. Explicit arch: Apple Silicon arm64 for RC3. Intel only if explicitly built/tested — otherwise declare unsupported.
4. App-owned service lifecycle: start localhost service on launch, automatic UI open (fix `main.py` missing `webbrowser.open()` or preferably app-shell launch), controlled shutdown, no orphaned terminal requirement.
5. User-facing startup errors (port in use, data dir unwritable, key init failure) — no tracebacks to practitioners.
6. Replace practitioner Quick Start normal path with 3 steps (Install / Open / Sample case). Move `127.0.0.1:8000`, `xattr`, `chmod`, ports to Troubleshooting → Advanced + Technical Guide only.
7. Publish SHA-256 for distributed ZIP + in-app version matching guide version (fix RC1/RC2 provenance defect).

## Qualification gates (permanent — three separate gates)
1. **Assurance Kernel Qualification** — deterministic engine + receipt integrity. RC2: PASS (sealed, unchanged by RC3).
2. **Distribution Qualification** — clean-machine install/launch on declared matrix. RC2 macOS: FAIL (UAT-MAC-003). RC3 must pass: clean machine A → clean machine B → different supported macOS version → nontechnical participant → repeatability.
3. **Practitioner Usability Qualification** — nontechnical user completes sample case with Quick Start only, no Terminal, no assistance.

## Sequence
RC3 macOS packaging → Apple Silicon clean A → clean B → different macOS version → nontechnical participant → repeatability → macOS distribution QUALIFIED → then apply lessons to Windows. Linux stays technical/container unless practitioner demand proves otherwise. Tablets/mobile stay outside desktop Edge matrix.

## Packaging invariance (binding discipline for RC3)
Packaging must not become a new computational build. The packaged RC3 application must produce the same deterministic outcomes as the qualified RC2 assurance kernel for the same Golden Corpus inputs. Any divergence fails RC3 regardless of install/launch success. Trace every RC3 commit to VB-RC2-UAT-001/-007/-008 and related packaging findings only — no engine, schema, or semantic changes. Branch: `rc3/macos-packaging` from the qualified MMP-1 line. `release/mmp-1.1` and `lab/mmp-2-ai` progress independently and must not feed changes back into RC3.

## RC3 exit condition (all five must pass)
RC3 PASS iff: (1) artifact integrity — signed/notarized macOS package with published SHA-256 matching the guide version; (2) installation — installs on all declared supported environments with no Terminal or security-bypass instructions in the normal path; (3) launch/lifecycle — launches, auto-opens the VaultBasis workspace, shuts down cleanly with user-facing startup errors; (4) usability — completes sample-case → findings → Outcome Receipt → verification journey with Quick Start only and no founder assistance; (5) computational equivalence — Golden Corpus outputs identical to the qualified deterministic assurance baseline.

## Evidence preserved
RC2 → automated PASS → clean-machine FAIL (UAT-MAC-003) → root cause → packaging requirements → RC3 → clean-machine qualification. Retain UAT-MAC-003 permanently as release evidence.
