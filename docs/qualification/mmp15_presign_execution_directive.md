# MMP1.5 Pre-Sign Execution Directive & Operator Handoff

**Authority:** Canonical Pre-Sign Master Ledger  
**Current State:** `ENGINEERING FREEZE — EFFECTIVE`  
**Product Change Authorization:** `NONE`  

---

## 1. Governance & Execution Rule

All MMP1.5 product code, packaging configurations, claims statements, qualification test harnesses, and pre-sign evidence are **frozen by release policy**.

No developer is authorized to modify runtime code, UI, packaging, installer behavior, rulesets, schemas, licensing semantics, commercial semantics, legal copy, qualification harnesses, or frozen candidate bytes unless:
1. A qualified physical/human execution exposes a release-blocking defect; or
2. Counsel or provider formal requirements mandate a concrete technical modification.

In either case, informal patching is strictly prohibited. The team will:
$$\text{Open Defect Ticket} \longrightarrow \text{Identify Affected Artifact} \longrightarrow \text{Apply Minimal Targeted Fix} \longrightarrow \text{Mint New Candidate Identity} \longrightarrow \text{Execute Requalification}$$

---

## 2. Authoritative Candidate Identities

```
+-------------------------------------------------------------------------------------------------------------------+
| ACTIVE PRE-SIGN CANDIDATE IDENTIFIERS (POST MODE-3 REMEDIATION OF CASE-CAP-001 & CASE-SOURCE-001)                 |
+-------------------------------------------------------------------------------------------------------------------+
| MACINTOSH CANDIDATE 12 (Provisional Baseline)                                                                     |
|   - Customer DMG (VaultBasis-RC3-macOS-arm64.dmg) : 55fd18199c81e8b922cb5613342b957a8d9706c5df353bdc876bf9bb1b8fb726 |
|   - Customer Package ZIP                          : e033d525db3e310c96217b0b638c764276471ecd809b361815713dd62bb76cb4 |
|   - Standalone Executable (MacOS/VaultBasis)      : 1a1bd6814209997b8269a243edacbca7b373f67eec985fdd30618c4199540dad |
|   - Candidate Manifest                            : 8f24123e0d537e56c437ed9350bef29d6a23a38782258e10dd0ada2448761504 |
|   - Status                                        : BUILT / PROVISIONALLY FROZEN                                  |
|                                                     (Pending source-commit + clean-worktree runtime binding)      |
|                                                                                                                   |
| WINDOWS CANDIDATE 03 (Staged Baseline — Pending Windows CI Execution)                                             |
|   - Target Spec                                   : Python 3.13 + PyInstaller 6.22 + canonical setup installer    |
|                                                     (scripts/installer_windows.py -> VaultBasis-Setup-1.5.0-rc3.exe)|
|   - Packaging Lineage                             : PLAT-WIN-PKG-DRIFT CHECK -> OPTION A PASS                     |
|                                                     (Documentation error corrected; frozen PyInstaller installer |
|                                                      pipeline remains intact; zero Inno/NSIS toolchain change)    |
|   - Cross-Platform Parity Contract                : UAT-30 100% FACT PARITY PASS (Candidate 12 core logic)        |
|   - Status                                        : STAGED FOR WINDOWS CI RUNNER EXECUTION                        |
+-------------------------------------------------------------------------------------------------------------------+
| SUPERSEDED HISTORICAL CANDIDATES (ARCHIVED AUDIT RECORD)                                                          |
+-------------------------------------------------------------------------------------------------------------------+
| MACINTOSH CANDIDATE 11 (Superseded by Candidate 12 — pre-CASE-CAP-001 / pre-CASE-SOURCE-001 remediation)         |
|   - Customer DMG: 4fb4997111402eae3c8caf655ece50207aa7dd53d9cfdd3ff31f1d0c31b4f0a9                              |
|   - Status: SUPERSEDED                                                                                            |
|                                                                                                                   |
| WINDOWS CANDIDATE 02 (Superseded by WIN-CANDIDATE-03 — pre-CASE-CAP-001 / pre-CASE-SOURCE-001 remediation)       |
|   - Customer Installer: 61c16bffa24219a58eaafd7d38f8e1d0e09ec0be26e7c38016503946af58153b                        |
|   - Status: SUPERSEDED                                                                                            |
+-------------------------------------------------------------------------------------------------------------------+
```

---

## 3. Four-Way Provenance Invariants & Qualification Harness Corrections

```text
+-------------------------------------------------------------------------------------------------------------------+
| PROVENANCE BOUNDARY SEPARATION                                                                                    |
+-------------------------------------------------------------------------------------------------------------------+
| PRODUCT SOURCE COMMIT        : cdbc94fba0fa005d7acc6778e53a892484a634e9                                           |
|                                (Authoritative runtime code for Candidate 12 & WIN-CANDIDATE-03)                   |
| QUALIFICATION HARNESS HEAD   : 5f6df64469b384c16bf47804090757fbb61bfb9f                                           |
|                                (Harness diagnostic reporting & fuzz test fail-closed invariant)                   |
| PACKAGING TOOLING SHA        : 76a284aedd47a3e37359a4aafd898ad0601e097f                                           |
|                                (scripts/installer_windows.py)                                                     |
| OPERATING STATE              : ENGINEERING FREEZE EFFECTIVE | PRODUCT CHANGE AUTH: NONE                           |
| 11 PRE-COMMIT GATES          : 11 / 11 GREEN (357-359 automated tests passed across all suites)                   |
| PRE-SIGN BARRIERS            : 0 / 6 CLOSED (PLAT-WIN-01B, WIN SHA, UAT-30, SEC-01 PCAP, UAT-29, UAT-22)        |
+-------------------------------------------------------------------------------------------------------------------+
```

### Governance Record: `QUAL-HARNESS-001`
- **Issue:** Validation gate `GATE-07` masked failing test identity due to summary column truncation, and license token fuzz invariant excluded a legitimate fail-closed terminal state (`UNSUPPORTED_VERSION`).
- **Scope:** Qualification harness + unit test suite only (`scripts/run_validation_gates.py`, `tests/unit/test_mmp15_license_engine.py`).
- **Product Runtime Changed:** **NO** (Zero changes to packaged runtime, UI, schemas, policies, or database engine).
- **Candidate Bytes Changed:** **NO** (Candidate 12 and WIN-CANDIDATE-03 binaries remain unaltered).
- **Disposition:** **HARNESS CORRECTION ACCEPTED**.
- **Rebuild Candidate 12:** **NOT REQUIRED** (Candidate 12 remains frozen at product source `cdbc94fba0fa005d7acc6778e53a892484a634e9`).
- **Re-run Affected Qualification:** **REQUIRED — COMPLETED** (All 11 pre-commit gates 100% green on CI and local).

### Governance Record: `CASE-CAP-UX-001` (Commercial UX Completion of CASE-CAP-001 — Final Adjudication)
- **Authorization:** Authorized narrow commercial-comprehension amendment prior to UAT-29 unassisted validation.
- **Scope:** Edge web dashboard (`apps/web-dashboard/index.html`), marketing portal (`apps/web-marketing/`), and catalog schemas. Zero engine, SQLite database, or pricing logic drift.
- **Adjudicated Scope Decisions:**
  1. **Always-visible case meter in top nav:** Plan tier, monotonic usage (`billable_cases_count / max_cases_per_installation`), accessible `role="progressbar" aria-valuemin="0" aria-valuemax="10" aria-valuenow="6"` attributes, compact label (`6 / 10 cases used`), and tooltip (`1 case = 1 client + 1 tax year · X new cases remain this annual term`).
  2. **4-state New Case modal:** Capacity Available (with after-creation preview), Final Slot Warning (`⚡ Final Case Allowance`), Limit Reached Explanatory Card (with zero-egress `<a href="https://vaultbasis.com/pricing" target="_blank">` navigation and `[Back to Cases]`), and Expired/Unlicensed Gate.
  3. **Friendly error translation:** `CASE_CAPACITY_REACHED` translated to: *"Your annual client-case allowance has been used. Existing cases remain available to review, reconcile, and export."*
  4. **Delete Case Action Scope Discipline:** Newly introduced Delete Case buttons and modals removed to avoid workflow expansion. Canonical rule preserved in copy: *"Deleting an existing case does not restore its annual case allowance."*
  5. **Marketing standardization:** Standardized to *"Up to 10/50 new client tax-year cases per annual term"* and canonical definition *"1 case = 1 client + 1 tax year"*.
- **Candidate Lineage Transition:**
  - `Candidate 12`: Historical frozen regression baseline (superseded for pre-sign release use once Candidate 13 is fully packaged and qualified).
  - `Candidate 13` (macOS) & `WIN-CANDIDATE-04` (Windows): Release candidate targets incorporating `CASE-CAP-UX-001`.
  - Physical and human pre-sign gates (`UAT-29`, `PLAT-WIN-01B`, `SEC-01`, `UAT-22`) target Candidate 13 / WIN-CANDIDATE-04.

---

## 4. Operational Ingestion & Closure Handlers

### A. Windows Physical Session (`PLAT-WIN-01B`) & Installed Executable SHA
When operator completes physical execution on WIN-CANDIDATE-04, record:
- Installed `VaultBasis.exe` SHA-256 via `Get-FileHash "$env:LOCALAPPDATA\VaultBasis\VaultBasis.exe" -Algorithm SHA256`.
- 19-point physical UX checklist results.
- **Runtime Equivalence Disposition:**
  - Verify UAT-30 cross-platform fact parity against Candidate 13.
- **Closure:** If all pass $\rightarrow$ `WIN-CANDIDATE-04 = ACTIVE PRE-SIGN WINDOWS BASELINE`, `PLAT-WIN-01 = PRE-SIGN PASS`.

### B. Raw Egress Packet Capture (`SEC-01`)
- Founder executes `sudo tcpdump` on macOS covering Candidate 13.
- Ingest `sec01_candidate13_capture.pcap`, metadata JSON, and analysis JSON.
- Bound claim: *No unexpected VaultBasis-process-owned non-loopback outbound traffic was observed during the qualified Candidate 13 capture interval.*
- Close `SEC-01 = PASS`.

### C. Unassisted Practitioner Validation (`UAT-29`)
- External CPA/EA runs unassisted session on Candidate 13 using standard customer guides only.
- Ingest participant environment, timestamps, and zero-intervention record $\rightarrow$ Close `UAT-29 = PASS`.

### D. Human Review Lifecycle Validation (`UAT-22`)
- Execute practitioner review workflow on Candidate 13 (review state transitions, findings dispositions, immutable deterministic truth).
- Ingest review session evidence $\rightarrow$ Close `UAT-22 = PASS`.

### E. Counsel Determinations (`LEGAL-001..003, 008, 009, 011..013, 015`)
- Map counsel advice into legal ledger records.
- If technical modification required $\rightarrow$ open `LEGAL-###-REMEDIATION-###`.
- If accepted $\rightarrow$ close counsel dependencies without over-claiming.

### F. Commercial & External Providers
- **Microsoft Trusted Signing:** Await organizational identity validation; bind certificate profile to signing pipeline.
- **Paddle Production:** Verify live credentials, webhook HMAC validation, replay protection, and zero-tax-data transmission $\rightarrow$ Close `LEGAL-004` & `LEGAL-012` live milestones.
- **Mailer DNS:** Verify SPF, DKIM, DMARC, and zero-tax-data in emails $\rightarrow$ Close `PROD-GATE-12`.
- **LEGAL-014:** Founder confirms corporate formation, IP assignments, and contributor agreements $\rightarrow$ Close `LEGAL-014 = PASS`.

---

## 5. Formal Pre-Sign Authorization Gate

Signing is authorized **only** when all six prerequisites are satisfied:

```text
[ ] PLAT-WIN-01B PASS (Physical Windows session complete on WIN-CANDIDATE-04)
[ ] Installed Windows VaultBasis.exe SHA-256 captured & bound
[ ] WIN-CANDIDATE-04 UAT-30 applicability confirmed via runtime equivalence
[ ] SEC-01 raw continuous packet capture PASS (sudo tcpdump pcap on macOS on Candidate 13)
[ ] UAT-29 first qualified unassisted practitioner PASS (on Candidate 13)
[ ] UAT-22 human review lifecycle PASS (on Candidate 13)

===> CONVENE FORMAL MMP1.5 PRE-SIGN AUTHORIZATION REVIEW
===> Authorize Production Signing:
     - Candidate 13     -> MAC-SIGNED-RC1 (Apple Developer ID + Notarization + Stapling)
     - WIN-CANDIDATE-04 -> WIN-SIGNED-RC1 (Microsoft Trusted Signing + RFC 3161 Timestamp)
```
```

---

## 6. Post-Sign Qualification Mandate

Signed artifacts receive new immutable cryptographic identities and undergo mandatory post-sign qualification:
- Clean-machine install & launch
- Final SBOM & license notice reconciliation
- 5–8 unassisted practitioner validation campaign
- Live checkout & web gateway verification
- Final closure of `PROD-GATE-01..17`
- Formal `PROD-GATE-18` Final Launch Authorization $\rightarrow$ `DISTRIBUTION_ACTIVE`.
