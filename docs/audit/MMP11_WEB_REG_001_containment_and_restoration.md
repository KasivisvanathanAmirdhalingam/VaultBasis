# MMP11-WEB-REG-001 — Public Website Regression Containment & Restoration

> **Directive Reference:** `MMP11-WEB-REG-001`  
> **Status:** `MMP11-WEB-REG-001 = AUTOMATED_VALIDATION_PASS / CI_VERIFIED`  
> **Web Remediation SHA:** `dd4230c97ba98d5fbab7738efdc80c089a9e9ee7` (CI Run `37121404625`)  
> **Frozen Edge Candidate:** `641d2b135ab0dcfa3bdf3b5edc95f4d1a3d5511d` (CI Run `37120319044`) — *Preserved & Untouched*  
> **Priority:** Release Blocker  
> **Scope:** Public Marketing & Trust Website (`apps/web-marketing/`, `dist/public-web/`)  

---

## 1. Executive Summary & Root Cause Analysis

### 1.1 Observed Production Regression
1. **Duplicate / Floating In-Page Navigation:** On the public homepage (`/` / `/#how-it-works`), a secondary navigation strip (`How It Works | Evaluation Boundary | Evidence Processing | Resources`) was rendered between the global header and the page content, violating the single-navigation architecture.
2. **Access Modal Transient State Bleed:** On `/verifier-access?next=/verifier`, the Request Access success modal could unexpectedly remain visible if previously submitted or improperly closed.
3. **Verifier Availability Claim Discrepancy:** `trust-assurance.html` stated that the Web Verifier is available *"without a VaultBasis account"*, which conflicted with the controlled preview gate requiring design-partner credentials.

### 1.2 Root Cause
- **Issue 1 (Duplicate Navigation):** Commit `73a4523` (`fix(mmp11-pres-002)`) had introduced a `.page-nav-strip` element inside `apps/web-marketing/index.html` as a quick-jump bar. While intended for in-page anchors, it visually competed with the canonical global header navigation.
- **Issue 2 (Modal State Bleed):** `apps/web-marketing/partials/shell.js` did not explicitly reset the modal DOM state (switching from `request-success` back to `request-form-container` and clearing inputs) upon every `openAccessModal()` call, nor did it track and restore focus to the invoking button upon `closeAccessModal()`.
- **Issue 3 (Verifier Claim):** Legacy marketing copy in `trust-assurance.html` retained an outdated unauthenticated claim from prior iterations.

---

## 2. Invariants Introduced

### `VB-WEB-INV-002 — Single Global Navigation`
Every public VaultBasis route exposes exactly one canonical global header navigation. Page-local navigation may aid document navigation on long standalone reference docs (e.g. Table of Contents on Trust & Assurance) but must never duplicate, compete with, or render as a pseudo-global navigation bar between the header and normal page content.

### `VB-WEB-INV-003 — Route-Scoped Transient State`
Request Access modal, form inputs, and submission success state must appear only through an explicit user journey and must not leak unexpectedly across unrelated route transitions or fresh sessions. `openAccessModal()` must unconditionally reset modal state to `FORM`, and `closeAccessModal()` / `Escape` must dismiss the modal and restore focus to the triggering element.

---

## 3. Remediation Details

| File | Changes Made |
|---|---|
| `apps/web-marketing/index.html` | Removed `.page-nav-strip` CSS and `<nav class="page-nav-strip">` HTML block completely. |
| `apps/web-marketing/partials/shell.js` | Added `_lastFocusedElement` tracking, focus restoration, explicit `FORM` state reset in `openAccessModal()`, and `Escape` key event listener cleanup. |
| `apps/web-marketing/trust-assurance.html` | Reconciled verifier description: *"Outcome Receipts can be independently verified offline or via the hosted web verifier during preview. Verification operates entirely client-side without transmitting receipt contents to a server."* |
| `tests/quality/production_deployment/test_web_regression_invariants.py` | Added comprehensive automated assertions for `VB-WEB-INV-002`, `VB-WEB-INV-003`, negative control injection tests, and claim audits. |
| `tests/quality/production_deployment/test_web_navigation_and_links.py` | Updated anchor regex to support root-relative `/#...` anchors. |

---

## 4. Route Verification Matrix (Post-Remediation)

| Route | Canonical Header | Secondary Nav Strip | Modal Initial State | Status |
|---|---|---|---|---|
| `/` | `PASS (1)` | `NONE (Absent)` | `CLOSED` | `PASS` |
| `/#how-it-works` | `PASS (1)` | `NONE (Absent)` | `CLOSED` | `PASS` |
| `/#comparison` | `PASS (1)` | `NONE (Absent)` | `CLOSED` | `PASS` |
| `/#security` | `PASS (1)` | `NONE (Absent)` | `CLOSED` | `PASS` |
| `/#resources` | `PASS (1)` | `NONE (Absent)` | `CLOSED` | `PASS` |
| `/trust-assurance` | `PASS (1)` | `NONE (TOC in hero only)` | `CLOSED` | `PASS` |
| `/about` | `PASS (1)` | `NONE (Absent)` | `CLOSED` | `PASS` |
| `/verifier-access` | `PASS (1)` | `NONE (Absent)` | `CLOSED` | `PASS` |
| `/faq` | `PASS (1)` | `NONE (Absent)` | `CLOSED` | `PASS` |
| `/privacy-policy` | `PASS (1)` | `NONE (Absent)` | `CLOSED` | `PASS` |
| `/terms-of-service` | `PASS (1)` | `NONE (Absent)` | `CLOSED` | `PASS` |
| `/contact` | `PASS (1)` | `NONE (Absent)` | `CLOSED` | `PASS` |
| `/security-disclosure` | `PASS (1)` | `NONE (Absent)` | `CLOSED` | `PASS` |

---

## 5. Frozen Edge Candidate Preservation Statement

> **CRITICAL INVARIANT:**  
> The frozen Edge candidate (`641d2b135ab0dcfa3bdf3b5edc95f4d1a3d5511d`), CI Run `37120319044`, and the resulting macOS arm64 (`8e8e77...`) and Windows x64 (`6f2584...`) inner-ZIP binaries are **completely preserved and unaffected** by this public website remediation.  
>  
> Zero files within `edge/`, `schemas/`, `scripts/build_rc3_*.py`, or the offline packaged runtime were modified. Deterministic reconciliation, cryptographic signing, receipt schema, and local desktop packaging remain 100% immutable.
