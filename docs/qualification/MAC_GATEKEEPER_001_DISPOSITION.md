# MAC-GATEKEEPER-001 — Pre-Sign Trust-Boundary Finding & Governance Disposition

**Record ID:** `MAC-GATEKEEPER-001`  
**Related Record:** `ARTIFACT-TRANSPORT-001`  
**Date:** 2026-10-10  
**Target Candidate:** Candidate 13 (macOS arm64, commit `6cb896f1be2386aca99d3c107ad052f3edfc66e1`)  
**Trigger Event:** Candidate 13 macOS artifact downloaded from GitHub Actions Run 38056111224 via Google Chrome and launched in Finder.  
**Symptom:** macOS Gatekeeper modal dialog:  
> *“VaultBasis” is damaged and can’t be opened. You should move it to the Trash. Chrome downloaded this file today at 18:05.*  
**Classification:** `EXPECTED PRE-SIGN TRUST REJECTION` (Expected macOS Gatekeeper policy behavior for unsigned/ad-hoc web downloads, combined with engineering artifact transport layout divergence; NOT binary corruption or application runtime defect).  
**Product Change Authorization:** `NONE` (Zero product code modifications; Candidate 14 NOT authorized).  

---

## 1. Prior CI Verification & Baseline Evidence

Prior to distribution through an external web download channel, Candidate 13 demonstrated 100% automated integrity on macOS-14 runner in GitHub Actions:
1. **Pre-ZIP Application Launch Gate:** `PASS` (`POST /api/sample-case/load`, `GET /` 200 OK with "VaultBasis Edge").
2. **Post-DMG Extracted Launch Gate:** `PASS` (mounted DMG, extracted to clean temp dir, verified health endpoint).
3. **Disconnected Finder-Style Launch Gate:** `PASS` (spawned with `DEVNULL` stdio, verified HTTP health within deadline).
4. **Ad-Hoc Bundle Integrity:** `PASS` (`codesign --force --deep --sign -`).
5. **Candidate Provenance:** Explicitly stamped in `RELEASE.txt`: `Signing: UNSIGNED (no Developer ID in build env)`.

---

## 2. Founder Diagnostic Evidence

Diagnostic commands executed directly against downloaded bundle:
`/Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis-Validation/MAC/vaultbasis-rc3-candidate-macos-arm64/VaultBasis-RC3-macOS-arm64/VaultBasis.app`

### 2.1 Extended Attributes (`xattr -l`)
```text
com.apple.provenance: 
com.apple.quarantine: 0281;6aca6236;Chrome;48E7E567-75EF-4F99-BD11-11CD249429A7
```
**Finding:** Quarantine attribute `com.apple.quarantine` was applied by Chrome upon web download.

### 2.2 Signature Inspection (`codesign -dv --verbose=4`)
```text
Executable=.../VaultBasis.app/Contents/MacOS/VaultBasis
Identifier=com.vaultbasis.edge
Format=app bundle with Mach-O thin (arm64)
CodeDirectory v=20400 size=29132 flags=0x2(adhoc) hashes=904+3 location=embedded
Signature=adhoc
TeamIdentifier=not set
Sealed Resources version=2 rules=13 files=208
Internal requirements count=0 size=12
```
**Finding:** Candidate 13 is signed strictly with an ad-hoc signature (`flags=0x2(adhoc)`), with no Apple Developer ID or Team Identifier.

### 2.3 Gatekeeper Assessment (`spctl --assess --type execute --verbose=4`)
```text
Exit code: 1
.../VaultBasis.app: bundle format unrecognized, invalid, or unsuitable
```
**Finding:** Gatekeeper rejected execution because the bundle lacks Developer ID notarization and the downloaded loose-folder structure contains dereferenced framework symlinks.

### 2.4 Deep Code Signature Inspection (`codesign --verify --deep --strict --verbose=4`)
```text
--validated: libcrypto.1.1.dylib
--validated: pydantic_core.cpython-310-darwin.so
--validated: cryptography/hazmat/bindings/_rust.abi3.so
...
In subcomponent: .../Python.framework
bundle format unrecognized, invalid, or unsuitable
```
**Finding:** All binary shared objects validated. Framework subcomponent structure reflects expected GitHub Actions artifact container extraction behavior where POSIX symlinks (`Versions/Current`) are dereferenced into directories during loose folder upload.

---

## 3. Governance Disposition & Invariant Protection

1. **Dual Causality & Bounded Evaluation:**
   - The observed launch rejection is consistent with the candidate’s pre-sign trust state and browser quarantine. The tested GitHub Actions expanded folder also exhibited a framework-layout/signature-verification issue and is not the canonical customer-distribution artifact. Final causality for the customer DMG must be evaluated on the exact signed/notarized DMG.
2. **`ARTIFACT-TRANSPORT-001` — Engineering Transport vs Customer Distribution:**
   - **Definition:** GitHub Actions expanded folder artifacts are engineering transport only and are not qualified substitutes for DMG/installer customer artifacts.
   - Do not repair or alter the customer product to accommodate damage or layout flattening introduced by an engineering artifact transport layer. The canonical customer artifact is `VaultBasis-RC3-macOS-arm64.dmg`.
3. **Strict Operational Invariant:**
   - **Do NOT remove quarantine (`xattr -d`) or disable Gatekeeper as the customer solution.**
   - Customer Quick Start must preserve the zero-terminal, zero-developer journey:
     $$\text{Download DMG} \longrightarrow \text{Drag to Applications} \longrightarrow \text{Double-Click to Launch}$$

---

## 4. Revised Qualification Sequencing & Barrier Alignment

To resolve the contradiction of requiring an unassisted external Mac practitioner to test an unsigned download without terminal bypasses, the pre-sign barrier count is formally corrected from 6 to 5:

### PRE-SIGN BARRIERS: 0 / 5 CLOSED
1. **`PLAT-WIN-01B`**: Physical Windows execution on `WIN-CANDIDATE-04` (19-point UX checklist).
2. **Installed Windows SHA Binding**: Compute and record SHA-256 of installed `VaultBasis.exe`.
3. **`UAT-30` Fact Parity**: Verify Windows/macOS reconciliation fact parity.
4. **`SEC-01` Raw PCAP**: Continuous packet capture under `sudo tcpdump` on Candidate 13.
5. **`UAT-22` Review Lifecycle**: Human review lifecycle workflow on Candidate 13.

### POST-SIGN HUMAN ACCEPTANCE (On `MAC-SIGNED-RC1` & `WIN-SIGNED-RC1`):
1. **`UAT-29` Zero-Intervention Clean-Download Acceptance**: External CPA/EA conducts first unassisted zero-terminal session on exact signed/notarized bytes.
2. **Practitioner Validation Cohort**: 5–8 CPAs/EAs execute against production signed packages.

---

## 5. Four Canonical Claims Wording Corrections

The following four plain-English explanations are permanently corrected to maintain bounded, non-absolute claims across all documentation and roadmaps:

| Surface / Subject | Superseded Absolute Claim | Approved Canonical Bounded Claim |
| :--- | :--- | :--- |
| **PCAP (`SEC-01`)** | *“Proves VaultBasis Edge never leaks tax records to the internet.”* | **“Provides bounded evidence that no unexpected VaultBasis-process-owned non-loopback network traffic was observed during the qualified capture interval.”** |
| **SBOM (`LEGAL-007`)** | *“guaranteeing zero GPL license violations or known security bugs.”* | **“Provides an inventory of distributed software components used for license and vulnerability review; it does not guarantee zero licensing issues or zero vulnerabilities.”** |
| **Apple Notarization** | *“Apple scans… confirms no malicious payloads exist.”* | **“Apple performs automated notarization checks and issues a notarization ticket when accepted; notarization is not a guarantee that software is malware-free.”** |
| **Merchant of Record (Paddle)** | *“insulating VaultBasis from multi-state tax audits.”* | **“Paddle, as Merchant of Record, handles specified payment processing and indirect-tax obligations for transactions it processes; this does not create blanket immunity from tax or regulatory obligations.”** |

---

## 6. Track C Restructuring (Legal Review Bifurcation)

To maximize cost-efficiency and leverage the existing corporate relationship with LegalPlace (which formed and domiciles VaultBasis EURL), Track C is split:

### TRACK C1 — LegalPlace / French-Side Launch Cleanup
- **Scope:** EURL company details and corporate registry verification; Legal notices (*mentions légales*); French-side Terms / Privacy structure; French EURL $\rightarrow$ foreign B2B contracting requirements; Founder / EURL IP assignment documentation; Identification of questions outside LegalPlace's French jurisdiction.
- **Effort & Timeline:** Founder preparation: 2–4 hours; LegalPlace waiting: 1–5 business days.

### TRACK C2 — Narrow Specialist Counsel (Contingent on Unresolved US Flags)
- **Scope:** Activated only if LegalPlace review leaves specific US federal/state regulatory questions open: IRC § 7216 applicability; GLBA / FTC Safeguards Rule scope; US export controls / EAR sanctions classification; US-specific tax-professional positioning.
- **Effort & Timeline:** Founder preparation: 1–2 hours; Specialist counsel review: 1–3 focused hours; Waiting / response: 2–10 business days.
