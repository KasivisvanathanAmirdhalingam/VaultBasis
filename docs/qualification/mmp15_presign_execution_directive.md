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
| FROZEN CANDIDATE IDENTIFIERS (BY RELEASE POLICY)                                                                  |
+-------------------------------------------------------------------------------------------------------------------+
| MACINTOSH CANDIDATE 11 (Product Source: 2b3b014dadc6dd8a51035ad31e120a17e5be7010)                                 |
|   - Customer DMG (VaultBasis-RC3-macOS-arm64.dmg) : 4fb4997111402eae3c8caf655ece50207aa7dd53d9cfdd3ff31f1d0c31b4f0a9 |
|   - Customer Package ZIP                          : efa1426187ba99b934aab1e73787b10cf3637052f2bbd27996f82ff572f459ad |
|   - Standalone Executable (MacOS/VaultBasis)      : 9cd9b511cdcc760e8d86152d6b2e04ce970b8b1c045c32ab4534121eb811d7d0 |
|   - Candidate Manifest                            : c0513603f74757104afe535c385e83b5a8254133eb251f6481633259cccf0ffa |
|   - Status                                        : FROZEN / ACCEPTED                                             |
|                                                                                                                   |
| WINDOWS CANDIDATE 02 (Product Source: 2b3b014d..., Packaging Tooling: 76a284a...)                                 |
|   - Customer Package (VaultBasis-RC3-Windows-x64.zip)      : 25adeb008ffdcc7f9e6ef83915f2e9684751574c853df8e34bc588d78d6aba39 |
|   - Customer Installer (VaultBasis-Setup-1.5.0-rc3.exe)    : 61c16bffa24219a58eaafd7d38f8e1d0e09ec0be26e7c38016503946af58153b |
|   - Pipeline Candidate ZIP                                 : 1aadacdc66f2a02d6281ae80903a7116d40f5cff95048c178a317eab79f4c3c9 |
|   - Pipeline Verified Identities                           : dbe8205b80ae65dfa099a4e494dbad4ac04cae9662947005e775a793ebe3e503 |
|   - Installed Executable (%LOCALAPPDATA%\...\VaultBasis.exe): PENDING OPERATOR PHYSICAL EXTRACTION CAPTURE         |
|   - Status                                                 : FROZEN BY RELEASE POLICY                             |
+-------------------------------------------------------------------------------------------------------------------+
```

---

## 3. Four-Way Provenance Invariants

1. **PRODUCT SOURCE SHA:** `2b3b014dadc6dd8a51035ad31e120a17e5be7010` (Locked runtime logic).
2. **PACKAGING TOOLING SHA:** `76a284aedd47a3e37359a4aafd898ad0601e097f` (Emits canonical `VaultBasis-Setup-1.5.0-rc3.exe`).
3. **CANDIDATE QUALIFICATION HARNESS:** `adef2c6d69127217b081799db5d414ce6a8efa96` (Evaluated Candidate 02 in CI Run #194).
4. **CURRENT GOVERNANCE LEDGER HEAD:** `53e59cc39f534757cf193fee69b3f52ddc305687` (Governance docs & runbooks).

---

## 4. Operational Ingestion & Closure Handlers

### A. Windows Physical Session (`PLAT-WIN-01B`) & Installed Executable SHA
When operator completes physical execution, record:
- Installed `VaultBasis.exe` SHA-256 via `Get-FileHash "$env:LOCALAPPDATA\Programs\VaultBasis\VaultBasis.exe" -Algorithm SHA256`.
- 19-point physical UX checklist results.
- **Runtime Equivalence Disposition:**
  - If equal to Candidate 01 runtime digest $\rightarrow$ `CONFIRMED — BYTE IDENTICAL`, `UAT-30 applicability CONFIRMED`.
  - If unequal due to non-semantic build metadata $\rightarrow$ `CONFIRMED — SEMANTICALLY EQUIVALENT`, `UAT-30 applicability CONFIRMED`.
  - If runtime logic changed $\rightarrow$ Rerun `UAT-30`.
- **Closure:** If all pass $\rightarrow$ `WIN-CANDIDATE-02 = ACTIVE PRE-SIGN WINDOWS BASELINE`, `PLAT-WIN-01 = PRE-SIGN PASS`.

### B. Raw Egress Packet Capture (`SEC-01`)
- Founder executes `sudo tcpdump` on macOS covering Candidate 11.
- Ingest `sec01_candidate11_capture.pcap`, metadata JSON, and analysis JSON.
- Bound claim: *No unexpected VaultBasis-process-owned non-loopback outbound traffic was observed during the qualified Candidate 11 capture interval.*
- Close `SEC-01 = PASS`.

### C. Unassisted Practitioner Validation (`UAT-29`)
- External CPA/EA runs unassisted session using standard customer guides only.
- Ingest participant environment, timestamps, and zero-intervention record $\rightarrow$ Close `UAT-29 = PASS`.

### D. Human Review Lifecycle Validation (`UAT-22`)
- Execute practitioner review workflow (review state transitions, findings dispositions, immutable deterministic truth).
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
[ ] PLAT-WIN-01B PASS (Physical Windows session complete)
[ ] Installed Windows VaultBasis.exe SHA-256 captured & bound
[ ] WIN-CANDIDATE-02 UAT-30 applicability confirmed via runtime equivalence
[ ] SEC-01 raw continuous packet capture PASS (sudo tcpdump pcap on macOS)
[ ] UAT-29 first qualified unassisted practitioner PASS
[ ] UAT-22 human review lifecycle PASS

===> CONVENE FORMAL MMP1.5 PRE-SIGN AUTHORIZATION REVIEW
===> Authorize Production Signing:
     - Candidate 11     -> MAC-SIGNED-RC1 (Apple Developer ID + Notarization + Stapling)
     - WIN-CANDIDATE-02 -> WIN-SIGNED-RC1 (Microsoft Trusted Signing + RFC 3161 Timestamp)
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
