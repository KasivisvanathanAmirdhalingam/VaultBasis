# VaultBasis MMP-1.5 Physical Golden Journey Qualification Protocol
**Document ID:** `MMP15-QUAL-GOLDEN-001`  
**Candidate Source Commit:** `744de44`  
**Branch:** `preprod`  
**Standard:** Left-Shift Maximum / Granite-Level Release Gate (PRD §64, §71)  

---

## 1. Candidate Provenance & Identity Requirements

The physical validation harness on both **macOS arm64** and **Windows x64** must record and verify the following immutable identifiers:

| Identifier Key | Value / Resolution Source | Pass Criteria |
| :--- | :--- | :--- |
| `candidate_sha` | `744de44` | Exact match on git commit |
| `github_run_id` | GitHub Actions Workflow Run ID | Canonical release build job |
| `github_artifact_sha256` | SHA-256 of downloaded CI transport archive | Exact cryptographic digest |
| `customer_zip_sha256` | SHA-256 of unpacked customer distribution ZIP | Exact cryptographic digest |
| `api_health_service` | `GET /api/health` -> `"service": "VaultBasis Edge"` | Healthy, loopback-only |
| `runtime_source_commit` | `GET /api/system/version` -> `"build_sha"` | **Must equal `744de44`** |

---

## 2. Strict Cross-Platform Promotion Governance Rules

1. **Exact Candidate Promotion Only**: The exact source commit (`744de44`) that passes both macOS and Windows physical validation without any code change is promoted to `main`.
2. **Atomic Invalidation Rule**: Any code modification, hotfix, or script adjustment invalidates testing immediately, creates a new candidate SHA, and requires restarting the full 26-step physical qualification from Step 1 on both macOS and Windows.
3. **Preprod Isolation**: Vercel production and GitHub `main` remain locked and untouched until the complete physical evidence package is signed off.
4. **Expected vs Unexpected Errors**:
   - **0 Unexpected Error Toasts / 0 Uncaught Exceptions** (DevTools console clean).
   - Expected policy denials (e.g. `EVALUATION_CAPACITY_REACHED` on second client case attempt, or `ENTITLEMENT_REQUIRED` on unentitled case creation) must render the correct practitioner-facing explanation and guidance without crashing or throwing unhandled exceptions.

---

## 3. The 26-Step Golden Journey Execution Protocol

```
[PHASE A: INITIALIZATION & READ-ONLY VERIFICATION]
1. Start Edge from fresh packaged binary. Query GET /api/health and GET /api/system/version to record runtime provenance.
2. Verify unentitled dashboard state. Confirm zero cases count against commercial usage.
3. Open bundled sample case ("Sample Client (Acme Holdings LLC)"). Confirm reconciliation outcomes and material differences render.
4. Test offline Evidence Receipt verifier on sample receipt. Confirm verification passes with green cryptographic badge.
5. Attempt New Case creation from unentitled state. Confirm form is gated with clear "Start 3-Day Evaluation" and "Activate License Token" options. Create button is disabled.

[PHASE B: EVALUATION ACTIVATION & INTAKE WORKFLOW]
6. Click "Start 3-Day Evaluation". Confirm local evaluation activates (ACTIVE_EVALUATION, 1 client case limit, 72h temporal window).
7. Create first client case (e.g. "Redwood Tax Practice LLC", Tax Year 2025). Confirm creation succeeds (HTTP 201).
8. Inspect case table. Confirm authoritative UTC created_at / updated_at formatted as LAST ACTIVITY (e.g. "Oct 6, 2026 · 5:20 PM").
9. Ingest Source A (Broker Form 1099-DA).
10. Confirm case row updates to actionable state: "Missing tax ledger" with action button "Add client ledger →".
11. Ingest Source B (Client Tax Ledger - Koinly format).
12. Confirm case row updates to "Ready to Reconcile" with action button "Run deterministic reconciliation →".

[PHASE C: DETERMINISTIC RECONCILIATION & RECEIPT ISSUANCE]
13. Execute deterministic reconciliation.
14. Inspect findings: confirm 2 agreed records, 3 material differences (basis, scope, proceeds), and 0 unresolved items.
15. Generate VaultBasis Evidence Receipt.
16. Export signed Evidence Receipt JSON and complete client evidence bundle ZIP.
17. Run standalone offline verifier against exported receipt. Confirm cryptographic signature and schema validation pass.

[PHASE D: COMMERCIAL CAPACITY ENFORCEMENT]
18. Attempt to create a second client case.
19. Confirm deterministic rejection (HTTP 402, reason code: EVALUATION_CAPACITY_REACHED).
20. Confirm practitioner-facing upgrade guidance is clearly displayed.

[PHASE E: PERSISTENCE & EXPIRY ASSURANCE]
21. Terminate Edge application completely (kill process).
22. Relaunch Edge packaged application. Confirm Evaluation state, case record, ingested sources, reconciliation outcome, and receipt persist intact.
23. Execute synthetic time-travel test past T+72h.
24. Confirm status updates to EXPIRED_EVALUATION and new client work is blocked.
25. Confirm existing case, findings, export, and verification remain 100% accessible (Anti-Ransom historical access invariant).

[PHASE F: CROSS-PLATFORM REPETITION]
26. Repeat Steps 1–25 on the secondary operating system (Windows x64 / macOS arm64) using candidate SHA 744de44.
```

---

## 4. Physical Evidence Package Checklist (Per OS Platform)

Each platform validation run must assemble the following 10 artifacts into `docs/qualification/evidence/<OS>/`:

- [ ] **`01_provenance.json`**: Output of `GET /api/health`, `GET /api/system/version`, `github_artifact_sha256`, `customer_zip_sha256`.
- [ ] **`02_unentitled_launch.png`**: Clean dashboard showing unentitled guidance and sample case.
- [ ] **`03_active_evaluation.png`**: Dashboard banner showing active evaluation (1 case remaining).
- [ ] **`04_first_case_created.png`**: Table showing created case with authoritative `LAST ACTIVITY` timestamp.
- [ ] **`05_source_a_actionable_queue.png`**: Table showing *"Missing tax ledger"* with *"Add client ledger →"* action button.
- [ ] **`06_both_sources_ready.png`**: Case ready to reconcile with *"Run deterministic reconciliation →"*.
- [ ] **`07_reconciliation_findings.png`**: Findings breakdown showing agreed records and material differences.
- [ ] **`08_receipt_exported_and_verified.png`**: Issued cryptographic receipt and offline verifier pass.
- [ ] **`09_capacity_denial.png`**: Second case attempt showing clear capacity limit explanation.
- [ ] **`10_restart_persistence_and_expiry.png`**: Post-restart dashboard and expired evaluation read-only access.
- [ ] **`console_errors.log`**: Browser DevTools console log proving zero uncaught exceptions.
- [ ] **`runtime.log`**: Edge backend process log proving clean initialization and loopback-only processing.
