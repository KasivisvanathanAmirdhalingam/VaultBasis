# VaultBasis Master Tasks Ledger

| Task Description | Status | Layer | Commit ID | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **L1.1 / L1.2 Canonicalization & Hashing** | VERIFIED | L1 | (Previous) | Implemented deterministic UTF-8 bytes and SHA-256 digests. 12 Normative vectors locked. |
| **Verify payload integrity decoupled from external truth** | VERIFIED | L1 | (Previous) | Verifier modified to declare "PAYLOAD & SIGNATURE VERIFIED" rather than asserting external truth. |
| **L2.1 Preflight Implementation** | VERIFIED | L2 | `3b5ef2e5` | Deterministic PreflightReport (profile detection, row/condition stats, readiness state) in `IntakeDispatcher`. No inferring/coercion. |
| **L2.2 Finding Why Explanations** | VERIFIED | L2 | `3b5ef2e5` | Standardized `render_explanation` engine. 6-question boundary rules applied. Golden tests implemented for semantic snapshot. |
| **Legal Entity Check (TecTixBase EURL)** | VERIFIED | L2 | `3b5ef2e5` | Replaced "VaultBasis Inc." with TecTixBase EURL across public assets. Sealed RC1 distribution restored. |
| **L2.3 Provenance Mapping** | VERIFIED | L2 | (Previous) | Traces material findings to source rows/hashes without violating privacy boundaries. |
| **MMP11-DIST-WIN-002: Windows Runtime Startup Fix** | DISTRIBUTION_QUALIFIED | L2/Dist | `55eb501` | Fixed uvicorn `dictConfig` crash in frozen windowed binaries (`log_config=None` + safe stdio guards + hiddenimports). Automated gates & physical smoke PASS. |
| **MMP11-DIST-WIN-003: Windows Evidence Export UTF-8 Encoding Fix** | DISTRIBUTION_QUALIFIED | L2/Dist | `55eb501` | Enforced explicit `encoding="utf-8"` on all evidence export file writes under `cp1252` locale. Verified in CI Run 37190867994. |
| **MMP11-DIST-WIN-004: Windows Package Hygiene & Evidence Allowlist Contract** | CLOSED / QUALIFIED | L2/Dist | `bd9b1e7` | Qualified on native CI Run 37197525586 (Candidate SHA `434957f1...`, export SHA `403de48c...`). 0 leaks, physical smoke PASS. |
| **MMP11-DIST-MAC-004: macOS Distribution Qualification (Developer ID / Notarization)** | PENDING | L2/Dist | — | Functional manual pass verified (`9ec370c1...`); formal Developer ID code signing, hardened runtime, notarization stapling pending. |
| **MMP11-DIST-MAC-002: Mac Launch & Auto-Open** | READY_FOR_PHYSICAL_RECIPIENT_QUALIFICATION | L2/Dist | Current | Enhanced launcher to invoke system `open` for reliable browser auto-launch. Automated gates green. |
| **MMP11-UX-STORY-001: Practitioner Case & Source Comprehension** | READY_FOR_PHYSICAL_RECIPIENT_QUALIFICATION | UX | Current | Implemented Client Context, Source A (Broker) vs Source B (Tax Ledger) roles, readiness checks, 4-stage workflow, and sensitized result narrative. Automated gates green. |
| **MMP11-SAMPLE-001: Zero-Knowledge Sample Case Onboarding** | DISTRIBUTION_QUALIFIED | UX/API | Current | Added 1-click `POST /api/sample-case/load` pre-populating multi-asset broker & ledger scenario for instant exploration. Verified on Windows & Mac. |
| **MMP11-VERIFY-UX-001: Offline Verifier Practitioner Journey** | DISTRIBUTION_QUALIFIED | Verifier | Current | Decoupled verification UI from developer tooling; restructured bundle with clear technical verification separation. Verified on Windows & Mac. |
| **VB-DOC-INV-001: Canonical Documentation Architecture** | VERIFIED | Docs | Current | Added case_model, domain_model, practitioner_journey, evidence_readiness, visual_semantics, MMP15-COMM-001, and MMP15-PRACTICE-001. |
| **MMP11-QUAL-PHYS-001: Physical Recipient Qualification (Mac & Windows)** | IN_PROGRESS | Qual | `bd9b1e7` | Windows x64 DISTRIBUTION_QUALIFIED; macOS arm64 functional manual pass confirmed, awaiting MMP11-DIST-MAC-004. |

