# MMP11-EXEC-009A Physical Recipient Qualification Record

> **Governance State:** `READY_FOR_PHYSICAL_RECIPIENT_QUALIFICATION`  
> **Rule:** No distribution to Associate-001 or CPA until physical recipient tests pass without developer intervention.

---

## 1. Candidate Identity Freeze
- **Source SHA:** [To be populated from exact frozen git commit]
- **CI Run ID:** [To be populated from exact GitHub Actions run]
- **Mac arm64 Inner-ZIP SHA-256:** [To be populated from inspection report]
- **Windows x64 Inner-ZIP SHA-256:** [To be populated from inspection report]

---

## 2. Windows x64 Physical Recipient Qualification

- **Target Machine:** Physical Windows x64 Machine
- **OS / Version:** Windows 11 / Windows 10 x64
- **Architecture:** x64
- **Tester Role:** Independent Recipient (No developer assistance)

| Check | Gate Description | Expected | Actual Result |
|---|---|---|---|
| **NORMAL EXTRACTION** | Extract ZIP via Windows Explorer standard Extract All | Clean folder layout, `VaultBasis.exe` beside `_internal/` | PENDING / `PASS` / `FAIL` |
| **NORMAL GUI LAUNCH** | Double-click `VaultBasis.exe` in Explorer (handle SmartScreen "Run anyway") | No console crash, no `formatter 'default'` exception | PENDING / `PASS` / `FAIL` |
| **WORKSPACE OPEN** | Local workspace appears or reachable at `http://127.0.0.1:8000` | Edge UI displays active dashboard | PENDING / `PASS` / `FAIL` |
| **CASE MEANING UNDERSTOOD** | Practitioner understands what a Case represents | Bounded reconciliation activity for a tax year | PENDING / `PASS` / `FAIL` |
| **CLIENT / TAX-YEAR CONTEXT CLEAR** | Client reference (e.g. Redwood Consulting) & 2025 clearly visible | Context visible at top of case | PENDING / `PASS` / `FAIL` |
| **TWO EVIDENCE ROLES UNDERSTOOD** | Clear distinction between Source A (Broker) and Source B (Tax Ledger) | Roles and extracted fields explicit | PENDING / `PASS` / `FAIL` |
| **EVIDENCE READINESS UNDERSTOOD** | Readiness state understood as structural suitability, not factual truth | Readiness disclaimers clear | PENDING / `PASS` / `FAIL` |
| **SAMPLE CASE** | 1-Click "Explore Sample Case" loads complete multi-asset scenario | Instant preload without manual uploads | PENDING / `PASS` / `FAIL` |
| **WORKFLOW ORIENTATION** | 4-Stage persistent workflow bar shows current and completed stages | 1. Sources → 2. Reconcile → 3. Findings → 4. Receipt | PENDING / `PASS` / `FAIL` |
| **RECONCILIATION** | Click "⚡ Run Deterministic Reconciliation" executes cleanly | Deterministic output generated | PENDING / `PASS` / `FAIL` |
| **RESULT NARRATIVE** | Evaluated count, Agreed (Green), Differences (Amber), Unresolved (Orange) | Attention items highlighted | PENDING / `PASS` / `FAIL` |
| **FINDING WHY** | Open Finding Why: explains what was compared, values, rule, and provenance | Explainable without tax advice | PENDING / `PASS` / `FAIL` |
| **OUTCOME RECEIPT** | Open Outcome Receipt screen; understand integrity vs. Tax Correctness = NOT DETERMINED | Receipt metadata & boundaries clear | PENDING / `PASS` / `FAIL` |
| **ORIGINAL RECEIPT** | Drop `receipt-v0.1.json` into GUI Offline Verifier | Displays `PASS — Receipt Valid` | PENDING / `VALID` / `FAIL` |
| **TAMPERED RECEIPT** | Drop `golden_receipt_tampered.json` into GUI Offline Verifier | Displays `FAIL — Receipt Invalid or Tampered` | PENDING / `INVALID` / `FAIL` |
| **QUIT** | Terminate VaultBasis process cleanly | Process exits | PENDING / `PASS` / `FAIL` |
| **RELAUNCH** | Double-click `VaultBasis.exe` again in Explorer | Boots cleanly | PENDING / `PASS` / `FAIL` |
| **PERSISTENCE** | Confirm previously created cases and receipts persist | Data intact in local SQLite | PENDING / `PASS` / `FAIL` |
| **INTERVENTION REQUIRED** | Developer tools, Terminal, Python, or code repair | Must be `NONE` | PENDING / `NONE` |

**Recipient Explanation (In their own words):**  
> *"What did VaultBasis just do, and what would you investigate next?"*  
> [Record verbatim response]

**Windows x64 Result:** `PENDING`  
**Stopped At:** `N/A`

---

## 3. macOS arm64 Physical Recipient Qualification

- **Target Machine:** Apple Silicon Mac (M1/M2/M3/M4)
- **OS / Version:** macOS 14 Sonoma / macOS 15 Sequoia / macOS 13 Ventura
- **Architecture:** arm64
- **Tester Role:** Founder / Independent Recipient

| Check | Gate Description | Expected | Actual Result |
|---|---|---|---|
| **NORMAL EXTRACTION** | Extract ZIP via Archive Utility in Finder | `VaultBasis.app` intact | PENDING / `PASS` / `FAIL` |
| **NORMAL GUI LAUNCH** | Open `VaultBasis.app` (handle Gatekeeper via System Settings → Open Anyway) | App starts cleanly | PENDING / `PASS` / `FAIL` |
| **WORKSPACE OPEN** | Browser automatically opens workspace (`MMP11-DIST-MAC-002`) | Default browser loads workspace | PENDING / `PASS` / `FAIL` |
| **CASE MEANING UNDERSTOOD** | Practitioner understands what a Case represents | Bounded reconciliation activity | PENDING / `PASS` / `FAIL` |
| **CLIENT / TAX-YEAR CONTEXT CLEAR** | Client reference & 2025 tax year clear | Context visible | PENDING / `PASS` / `FAIL` |
| **TWO EVIDENCE ROLES UNDERSTOOD** | Source A (Broker) vs Source B (Tax Ledger) | Roles and extracted fields explicit | PENDING / `PASS` / `FAIL` |
| **EVIDENCE READINESS UNDERSTOOD** | Readiness state understood as structural suitability, not factual truth | Readiness disclaimers clear | PENDING / `PASS` / `FAIL` |
| **SAMPLE CASE** | 1-Click "Explore Sample Case" loads complete multi-asset scenario | Instant preload | PENDING / `PASS` / `FAIL` |
| **WORKFLOW ORIENTATION** | 4-Stage persistent workflow bar shows progress | 1. Sources → 2. Reconcile → 3. Findings → 4. Receipt | PENDING / `PASS` / `FAIL` |
| **RECONCILIATION** | Click "⚡ Run Deterministic Reconciliation" executes cleanly | Deterministic output generated | PENDING / `PASS` / `FAIL` |
| **RESULT NARRATIVE** | Evaluated count, Agreed (Green), Differences (Amber), Unresolved (Orange) | Attention items highlighted | PENDING / `PASS` / `FAIL` |
| **FINDING WHY** | Open Finding Why: explains what was compared, values, rule, provenance | Explainable without tax advice | PENDING / `PASS` / `FAIL` |
| **OUTCOME RECEIPT** | Open Outcome Receipt screen; understand integrity vs. Tax Correctness = NOT DETERMINED | Receipt metadata & boundaries clear | PENDING / `PASS` / `FAIL` |
| **ORIGINAL RECEIPT** | Drop `receipt-v0.1.json` into GUI Offline Verifier | Displays `PASS — Receipt Valid` | PENDING / `VALID` / `FAIL` |
| **TAMPERED RECEIPT** | Drop `golden_receipt_tampered.json` into GUI Offline Verifier | Displays `FAIL — Receipt Invalid or Tampered` | PENDING / `INVALID` / `FAIL` |
| **QUIT** | Terminate VaultBasis process cleanly | Process exits | PENDING / `PASS` / `FAIL` |
| **RELAUNCH** | Double-click `VaultBasis.app` again in Finder | Boots cleanly | PENDING / `PASS` / `FAIL` |
| **PERSISTENCE** | Confirm previously created cases and receipts persist | Data intact in local SQLite | PENDING / `PASS` / `FAIL` |
| **INTERVENTION REQUIRED** | Terminal, xattr, chmod, Python, or developer repair | Must be `NONE` | PENDING / `NONE` |

**Recipient Explanation (In their own words):**  
> *"What did VaultBasis just do, and what would you investigate next?"*  
> [Record verbatim response]

**macOS arm64 Result:** `PENDING`  
**Stopped At:** `N/A`

---

## 4. State Transition Rule
- If physical qualification passes on both platforms without intervention:  
  `READY_FOR_PHYSICAL_RECIPIENT_QUALIFICATION` ➔ `DISTRIBUTION_QUALIFIED`
- If Mac passes and is the designated Associate-001 environment while Windows is pending/blocked:  
  Mac can proceed to `Associate-001` (with Windows explicitly marked unqualified/blocked).
