# VaultBasis Master Tasks Ledger

| Task Description | Status | Layer | Commit ID | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **L1.1 / L1.2 Canonicalization & Hashing** | VERIFIED | L1 | (Previous) | Implemented deterministic UTF-8 bytes and SHA-256 digests. 12 Normative vectors locked. |
| **Verify payload integrity decoupled from external truth** | VERIFIED | L1 | (Previous) | Verifier modified to declare "PAYLOAD & SIGNATURE VERIFIED" rather than asserting external truth. |
| **L2.1 Preflight Implementation** | VERIFIED | L2 | `3b5ef2e5` | Deterministic PreflightReport (profile detection, row/condition stats, readiness state) in `IntakeDispatcher`. No inferring/coercion. |
| **L2.2 Finding Why Explanations** | VERIFIED | L2 | `3b5ef2e5` | Standardized `render_explanation` engine. 6-question boundary rules applied. Golden tests implemented for semantic snapshot. |
| **Legal Entity Check (TecTixBase EURL)** | VERIFIED | L2 | `3b5ef2e5` | Replaced "VaultBasis Inc." with TecTixBase EURL across public assets. Sealed RC1 distribution restored. |
| **L2.3 Provenance Mapping** | VERIFIED | L2 | (Previous) | Traces material findings to source rows/hashes without violating privacy boundaries. |
| **MMP11-DIST-WIN-002: Windows Runtime Startup Fix** | READY_FOR_PHYSICAL_RECIPIENT_QUALIFICATION | L2/Dist | Current | Fixed uvicorn `dictConfig` crash in frozen windowed binaries (`log_config=None` + safe stdio guards + hiddenimports). Automated gates green. |
| **MMP11-DIST-MAC-002: Mac Launch & Auto-Open** | READY_FOR_PHYSICAL_RECIPIENT_QUALIFICATION | L2/Dist | Current | Enhanced launcher to invoke system `open` for reliable browser auto-launch. Automated gates green. |
| **MMP11-UX-STORY-001: Practitioner Case & Source Comprehension** | READY_FOR_PHYSICAL_RECIPIENT_QUALIFICATION | UX | Current | Implemented Client Context, Source A (Broker) vs Source B (Tax Ledger) roles, readiness checks, 4-stage workflow, and sensitized result narrative. Automated gates green. |
| **MMP11-SAMPLE-001: Zero-Knowledge Sample Case Onboarding** | READY_FOR_PHYSICAL_RECIPIENT_QUALIFICATION | UX/API | Current | Added 1-click `POST /api/sample-case/load` pre-populating multi-asset broker & ledger scenario for instant exploration. Automated gates green. |
| **MMP11-VERIFY-UX-001: Offline Verifier Practitioner Journey** | READY_FOR_PHYSICAL_RECIPIENT_QUALIFICATION | Verifier | Current | Decoupled verification UI from developer tooling; restructured bundle with clear technical verification separation. Automated gates green. |
| **VB-DOC-INV-001: Canonical Documentation Architecture** | VERIFIED | Docs | Current | Added case_model, domain_model, practitioner_journey, evidence_readiness, visual_semantics, MMP15-COMM-001, and MMP15-PRACTICE-001. |
| **MMP11-EXEC-009A Physical Recipient Qualification (Mac & Windows)** | IN_PROGRESS | Qual | Current | Physical execution on Mac arm64 & Windows x64 machines tracking against MMP11_EXEC_009A_physical_qualification_record.md. |
