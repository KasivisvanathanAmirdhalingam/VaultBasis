# VaultBasis MMP-1.5 Practitioner UAT Observation Protocol & Scoring Instrument (MMP15-PROD-UAT-001)

> **Standard:** Zero-Developer-Intervention Production Readiness Protocol  
> **Evaluation Phase:** MMP-1.5 End-to-End Practitioner Validation  
> **Rule of Engagement:** The observer MUST NOT explain where to click, guide navigation, provide terminal commands, or explain underlying architecture. Any developer/founder assistance fails zero-intervention qualification for that stage.

---

## 1. Platform Coverage Quota

To ensure comprehensive cross-platform qualification and prevent platform bias, the UAT cohort of 5–8 unassisted CPAs/EAs MUST satisfy the following minimum platform distribution:

| Environment Profile | Minimum Quota | Actual Tested | Disposition |
|---|---|---|---|
| **Clean Windows x64 (Non-Dev Machine)** | $\ge 2$ sessions | `[ ] / [ ]` | Pending |
| **Clean Apple Silicon macOS (arm64)** | $\ge 2$ sessions | `[ ] / [ ]` | Pending |
| **Enterprise / Managed Endpoint (MDM/EDR)** | $\ge 1$ session | `[ ] / [ ]` | Pending |
| **Additional Cross-Platform Sessions** | Balance to $\ge 5-8$ | `[ ] / [ ]` | Pending |

---

## 2. Participant & Session Metadata

* **Participant ID / Code:** `CPA-UAT-____`
* **Professional Profile:** `[ ] Solo CPA  [ ] Tax Firm Partner  [ ] Enrolled Agent (EA)  [ ] Corporate Tax Manager`
* **Device / Operating System:** `[ ] Windows 11 x64  [ ] macOS Tahoe/Sequoia (arm64)  [ ] Managed Windows (Intune/Defender)`
* **Observer:** `__________________________`
* **Session Start Time:** `____:____ UTC` | **Session End Time:** `____:____ UTC`
* **Source Release Commit SHA:** `78f49a0` (Frozen in `release-manifest.json`)
* **Downloaded ZIP SHA-256 Digest:** `________________________________________________________________`

---

## 3. 13-Stage Scoring Rubric

Each stage must be evaluated against the strict five-state scoring taxonomy:
- `PASS`: Completed smoothly without friction or external guidance.
- `PASS_WITH_HESITATION`: Completed independently, but participant exhibited visible hesitation or expressed confusion.
- `FAIL_ZERO_INTERVENTION`: Required observer/developer explanation, hint, or intervention to proceed.
- `BLOCKED_BY_PRODUCT`: Blocked by an application bug, crash, or unexpected software state.
- `BLOCKED_BY_ENVIRONMENT`: Blocked by external infrastructure, local OS policy, or network failure outside product control.

| # | Journey Stage | Target Action / Verification Objective | Duration (min) | Score | Hesitations / Observations |
|---|---|---|---|---|---|
| **1** | **`DISCOVERY`** | Understands product purpose & Form 1099-DA value proposition in < 15s from `vaultbasis.com`. | `[  ]` | `[ ] PASS<br>[ ] PASS_HESIT<br>[ ] FAIL_ZERO<br>[ ] BLOCKED_PROD<br>[ ] BLOCKED_ENV` | |
| **2** | **`TRUST`** | Inspects Trust Center / "Why It's Safe" panel; confirms local-only boundary without IT panic. | `[  ]` | `[ ] PASS<br>[ ] PASS_HESIT<br>[ ] FAIL_ZERO<br>[ ] BLOCKED_PROD<br>[ ] BLOCKED_ENV` | |
| **3** | **`DOWNLOAD`** | Requests evaluation release, receives transactional email, clicks expiring link, downloads ZIP. | `[  ]` | `[ ] PASS<br>[ ] PASS_HESIT<br>[ ] FAIL_ZERO<br>[ ] BLOCKED_PROD<br>[ ] BLOCKED_ENV` | |
| **4** | **`INSTALL`** | Extracts ZIP and opens binary; OS accepts Authenticode / Developer ID without bypass prompts. | `[  ]` | `[ ] PASS<br>[ ] PASS_HESIT<br>[ ] FAIL_ZERO<br>[ ] BLOCKED_PROD<br>[ ] BLOCKED_ENV` | |
| **5** | **`FIRST_LAUNCH`** | App opens cleanly; confirms localhost `127.0.0.1` binding, privacy model, and version info. | `[  ]` | `[ ] PASS<br>[ ] PASS_HESIT<br>[ ] FAIL_ZERO<br>[ ] BLOCKED_PROD<br>[ ] BLOCKED_ENV` | |
| **6** | **`SAMPLE`** | Ingests bundled `CASE-SAMPLE-2025`; reconciles differences unmetered without license key. | `[  ]` | `[ ] PASS<br>[ ] PASS_HESIT<br>[ ] FAIL_ZERO<br>[ ] BLOCKED_PROD<br>[ ] BLOCKED_ENV` | |
| **7** | **`LICENSE`** | Enters/pastes valid Ed25519 commercial license token in UI; activates tier and case capacity. | `[  ]` | `[ ] PASS<br>[ ] PASS_HESIT<br>[ ] FAIL_ZERO<br>[ ] BLOCKED_PROD<br>[ ] BLOCKED_ENV` | |
| **8** | **`PRODUCTION_CASE`**| Creates new production case; verifies case is marked `PRODUCTION` and consumes capacity. | `[  ]` | `[ ] PASS<br>[ ] PASS_HESIT<br>[ ] FAIL_ZERO<br>[ ] BLOCKED_PROD<br>[ ] BLOCKED_ENV` | |
| **9** | **`RECONCILIATION`** | Ingests Form 1099-DA & tax ledger CSV; executes deterministic reconciliation. | `[  ]` | `[ ] PASS<br>[ ] PASS_HESIT<br>[ ] FAIL_ZERO<br>[ ] BLOCKED_PROD<br>[ ] BLOCKED_ENV` | |
| **10**| **`EXPORT`** | Exports signed Outcome Receipt bundle (`receipt.json` + verifier CLI/Web). | `[  ]` | `[ ] PASS<br>[ ] PASS_HESIT<br>[ ] FAIL_ZERO<br>[ ] BLOCKED_PROD<br>[ ] BLOCKED_ENV` | |
| **11**| **`VERIFICATION`** | Runs standalone offline verifier (`verify.py` or `verifier.html`) on export; verifies signature & digest. | `[  ]` | `[ ] PASS<br>[ ] PASS_HESIT<br>[ ] FAIL_ZERO<br>[ ] BLOCKED_PROD<br>[ ] BLOCKED_ENV` | |
| **12**| **`PERSISTENCE`** | Closes application completely, relaunches; confirms 100% of cases and audit events persist. | `[  ]` | `[ ] PASS<br>[ ] PASS_HESIT<br>[ ] FAIL_ZERO<br>[ ] BLOCKED_PROD<br>[ ] BLOCKED_ENV` | |
| **13**| **`SUPPORT`** | Generates sanitized diagnostic bundle (`diagnostic.zip`); confirms support email `support@vaultbasis.com`. | `[  ]` | `[ ] PASS<br>[ ] PASS_HESIT<br>[ ] FAIL_ZERO<br>[ ] BLOCKED_PROD<br>[ ] BLOCKED_ENV` | |

---

## 4. Frozen 11 Customer-Visible Failure Taxonomy

During UAT and production operations, non-happy path conditions must map deterministically to one of the 11 frozen failure states with actionable recovery instructions in the UI:

| # | Failure Identifier | User-Visible Cause | Expected Recovery Guidance in UI |
|---|---|---|---|
| **1** | `DOWNLOAD_LINK_EXPIRED` | Expiring HMAC link timestamp exceeded | One-click "Send fresh link to my email" prompt. |
| **2** | `WRONG_PLATFORM` | User downloaded Windows ZIP on Mac or vice versa | Platform detection with direct link to alternative OS artifact. |
| **3** | `DOWNLOAD_INTERRUPTED` | Network drop during binary download | Resumable download guidance with SHA-256 verification instructions. |
| **4** | `SIGNATURE_INVALID` | Binary bytes tampered or corrupted in transit | Immediate integrity warning directing user to re-download official build. |
| **5** | `LICENSE_INVALID` | Malformed token or invalid signature | Clear distinction between syntax error and cryptographic invalidity. |
| **6** | `LICENSE_EXPIRED` | License expiration timestamp exceeded | Renewal link with guarantee that historical cases remain fully readable. |
| **7** | `LICENSE_CAPACITY_REACHED`| Installation case limit exhausted | In-app capacity upgrade CTA without loss of current case data. |
| **8** | `FIRST_RUN_INIT_FAILED` | Storage directory creation / permissions error | Actionable remediation for local user directory permissions. |
| **9** | `EXISTING_DATA_DETECTED`| Previous installation database found | Automatic schema migration prompt with zero data loss. |
| **10**| `RESTORE_FAILED` | Backup file corrupted or invalid format | Safe rollback to pre-restore snapshot with diagnostic export. |
| **11**| `ENDPOINT_SECURITY_BLOCKED`| Corporate IT / EDR blocks execution | Link to Enterprise IT Deployment Profile (`vaultbasis.com/trust#enterprise`). |

---

## 5. Post-Session Qualitative Assessment

* **Trust Level Before Download (1–5):** `[   ]`
* **Trust Level After Running Sample (1–5):** `[   ]`
* **Value Comprehension:** `[ ] Fully Clear  [ ] Partially Clear  [ ] Confused`
* **Willingness to Purchase:** `[ ] Definitely Yes  [ ] Probably Yes  [ ] Unsure  [ ] No`
* **Price Sensitivity Feedback:** `_________________________________________________________`
* **Primary Hesitation / Blocker:** `_______________________________________________________`

---

## 6. Qualification & Release Promotion Rule

$$\texttt{MMP15-PROD-UAT-001 PASS} \implies \texttt{MMP-1.5 PRODUCTION-QUALIFIED}$$
$$\implies \texttt{Stabilization / Defect Triage Window} \implies \texttt{Commercial Launch} \implies \texttt{MMP-2 Unlock}$$

- **Zero-Intervention Threshold:** If any stage receives `FAIL_ZERO_INTERVENTION` or `BLOCKED_BY_PRODUCT`, it generates an immediate P0/P1 remediation ticket.
- **Production Qualification:** Requires 100% stage pass rate across the full platform quota ($\ge 2$ Win, $\ge 2$ Mac, $\ge 1$ Enterprise).
