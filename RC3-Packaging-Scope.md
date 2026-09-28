# RC3 — Multi-Platform Desktop Packaging Baseline (no feature changes)

**Status:** PROPOSED — RC2 remains sealed and immutable. CI green is a build signal, not a release.
**Objective:** Package the qualified VaultBasis assurance kernel as independently installable
desktop applications for declared macOS and Windows environments, requiring no developer
tools, shell commands, Python installation, or Docker. Each platform artifact is
appropriately code-signed and subjected to applicable platform security qualification.
Packaging MUST preserve deterministic assurance semantics across platforms. Release builds
MUST apply proportionate defense-in-depth against tampering and practical reverse
engineering, while security MUST NOT depend upon the executable being impossible to
inspect or decompile.

## Release pipeline (CI green ≠ release)

GitHub Actions GREEN → build artifacts exist → NOT YET A QUALIFIED RELEASE →
RC3 packaging → sign (+ notarize macOS) → kernel-equivalence regression →
clean-machine qualification per platform → freeze/tag/hash → publish immutable
artifact → website download endpoint serves that exact hash → distributed UAT.

No artifact is "supported" until it passes its own distribution gate. A CI-generated
Windows ZIP is not automatically a supported Windows release. Vercel deployments and
CI artifacts must never be mistaken for qualified releases.

## Non-goals (explicitly out of RC3)
- No changes to reconciliation logic, semantics, Evidence Contract / receipt schema, assurance levels, or parsers.
- No Linux commercial support (engineering/container use only unless practitioner demand proves otherwise).
- No iPad/iOS/Android — separate application architectures, not RC3 builds.
- No new features, no UI redesign beyond lifecycle/startup-error handling required for installability.

## Target journey (both platforms)
Download qualified installer → Install → Open VaultBasis → workspace opens automatically →
Start Sample Case → findings → Outcome Receipt → verification. Having trouble → Troubleshooting.
No Docker Desktop, Python, Terminal, PowerShell, localhost address, chmod, xattr, or
developer commands in the normal practitioner journey. Docker/OCI stays in
CI/reproducibility/engineering/possible-enterprise-deployment — never CPA installation.

## Tracks

                 RC3 PACKAGING
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        RC3-MAC              RC3-WIN
   arm64 package          x64 installer
   Developer ID signing   trusted code signing
   Hardened Runtime       Smart App Control clean
   Apple notarization     per-component signing
   clean machines         clean machines
             │                   │
             └─────────┬─────────┘
                       ▼
             COMPUTATIONAL
              EQUIVALENCE
                       │
                       ▼
                 RC3 RELEASE

### RC3-MAC (required)
- Proper `.app` (Info.plist, bundle ID, version) or signed distribution `.pkg`; decide one.
- Developer ID signing + Hardened Runtime + Apple notarization (normal notarization path
  requires appropriate signing + Hardened Runtime; notarization lets Gatekeeper establish
  Apple checked the submission).
- Explicit arch: Apple Silicon arm64 required. Intel x86-64 only if explicitly built/tested,
  otherwise declared unsupported.

### RC3-WIN (required, own distribution gate — not "later")
- Real installer (not a loose `.exe` in a ZIP) + signed uninstaller.
- Trusted code-signing certificate; sign installer, EXEs, DLLs, and scripts per Microsoft
  Smart App Control guidance; test against Smart App Control before distribution.
- x86-64 required. Windows ARM64 later unless actual demand.

### Target matrix
| Platform | Artifact | Arch | RC3 objective |
|---|---|---|---|
| macOS 14+ | .app / signed distribution package | arm64 | Required |
| macOS 14+ | .app | Intel x86-64 | Only if built/tested; else unsupported |
| Windows 11 | installer + application | x86-64 | Required |
| Windows 11 | native/compatible build | ARM64 | Later unless demand |
| Linux | package/container | x86-64 | Engineering only |
| iPad/iOS | — | ARM | Not a desktop build; separate architecture |

## Security model: assume the binary is eventually understood

```
ATTACKER MAY EVENTUALLY UNDERSTAND BINARY
                 │
                 ▼
       Does VaultBasis remain safe?
```

"Impossible to decompile" is unachievable and MUST NOT be a requirement — any delivered
executable can be inspected, dumped, instrumented, or patched with sufficient effort.
Deterministic assurance semantics must stay public and reproducible
(same evidence + same declared semantics → reproducible outcome); secrecy there would
conflict with the product's evidence credibility. The secret is the per-installation
Ed25519 private key and infrastructure/entitlement credentials — never embedded in
the binary — plus customer evidence, which never leaves the machine in the tested boundary.

Reverse engineering must NOT yield: another installation's private key, infrastructure
or entitlement-service credentials, customer evidence, ability to forge an issued
receipt, or ability to alter a receipt without verification failing.

Proportionate hardening for release builds (no malware-like anti-analysis tricks that
cause AV false positives, signing breakage, or undebuggable crashes):
compiled/native components where justified; toolchain-appropriate obfuscation; symbol
stripping; debug-metadata removal; release-only builds; package integrity checks;
secrets externalization; secure local key storage; dependency minimization (+SBOM/
scanning); reproducible release manifests; OS-native signing above all.

Current baseline (honest): plain PyInstaller onefile, unsigned, unnotarized
(`scripts/build_desktop_executable.py` comment claims "stripped, encrypted" — no `--key`
or strip step exists; do not repeat that claim). PyArmor/Cython appear in task-ledger
planning only, not in the build.

Protect aggressively: proprietary implementation details; signing-key handling;
entitlement/licensing implementation; security-sensitive config; internal diagnostics
that reveal attack surfaces; future proprietary heuristics. Never embed credentials/
secrets in the binary at all.

## Computational equivalence (cross-platform)

Same canonical input → Mac result vs Windows result → byte/semantic comparison.
Precision required: byte-identical for canonical payloads, digests, difference records,
and outcome states; semantically equivalent (not byte-identical) where platform-local
material differs by design — installation signatures/fingerprints (per-install keys),
timestamps, installation-specific paths. Equivalence failures fail RC3 regardless of
install/launch success.

## Packaging invariance (binding discipline)
Packaging must not become a new computational build. Every RC3 commit traceable to
VB-RC2-UAT-001/-007/-008 and related packaging findings only. Branches
`rc3/macos-packaging` and `rc3/windows-packaging` from the qualified MMP-1 line.
`release/mmp-1.1` and `lab/mmp-2-ai` progress independently and must not feed back
into RC3.

## RC3 exit condition (all must pass, per platform unless noted)
RC3 PASS iff: (1) artifact integrity — signed (macOS: +notarized) package with published
SHA-256 matching the served download; (2) installation — clean-machine install with no
Terminal/PowerShell/bypass in the normal path, ordinary non-developer account;
(3) launch/lifecycle — auto-opens workspace, clean shutdown, user-facing startup errors,
quit/relaunch, uninstall/reinstall; (4) usability — sample-case → findings → Outcome
Receipt → hosted AND offline verification with Quick Start only, no founder assistance,
plus tampered-receipt negative test; (5) computational equivalence — Golden Corpus
outputs equivalent per the precision rule above, identical install-independent outcomes
across Mac and Windows.

## Qualification checklists
Mac: Apple Silicon A/macOS 14, Apple Silicon B/macOS 15, fresh download, non-developer
account, install → launch → sample → receipt → hosted/offline verify → quit/relaunch →
uninstall/reinstall → tampered negative.
Windows: 11 x64 machine A, machine B, one with meaningful security enforcement
(Smart App Control), non-developer account, same journey, no PowerShell/CMD.

## Evidence preserved
RC2 → automated PASS → clean-machine FAIL (UAT-MAC-003) → root cause → packaging
requirements → RC3 (mac + win tracks) → per-platform qualification. Retain UAT-MAC-003
permanently. Mac 3 retest is the first clean-machine check once the macOS artifact is
frozen — against the immutable hash, not CI output.
