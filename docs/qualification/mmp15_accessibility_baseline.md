# Web Accessibility Baseline Technical Qualification (LEGAL-016)

**Evaluation Date:** October 9, 2026  
**Scope:** Public Marketing Web (`vaultbasis.com`) and Edge Web Dashboard (`apps/web-dashboard/`).  
**Standard:** WCAG 2.1 Level AA Practical Baseline (Focused, Non-Distracting Risk Control).  
**Ownership Boundary:** Engineering owns technical markup, ARIA semantics, keyboard accessibility, and contrast compliance. Founder/Counsel owns legal accessibility risk evaluation.

---

## 1. Accessibility Control Matrix

| Category | Criterion / Requirement | Public Web Status | Dashboard Status | Technical Verification Evidence |
|---|---|:---:|:---:|---|
| **Keyboard Navigation** | All interactive elements operable via `Tab`, `Shift+Tab`, `Enter`, and `Space`. | **PASS** | **PASS** | Logical tab order preserved; 0 keyboard traps across all modal and navigation flows. |
| **Visible Focus States** | High-contrast focus rings (`:focus-visible`) on all buttons, links, inputs, and tabs. | **PASS** | **PASS** | CSS design tokens enforce `outline: 2px solid var(--accent)` with `outline-offset: 2px`. |
| **Form Labels & Associations** | All input controls have explicitly associated `<label for="...">` or `aria-label`. | **PASS** | **PASS** | 100% of inputs, selects, file dropzones, and textareas bound to unique IDs. |
| **Button Accessible Names** | Interactive buttons carry clear text or `aria-label` (no ambiguous icon-only buttons). | **PASS** | **PASS** | All icon-only triggers (close buttons, copy buttons) include explicit `aria-label` attributes. |
| **Semantic Headings** | Strict `<h1>` $\rightarrow$ `<h2>` $\rightarrow$ `<h3>` hierarchy without skipped levels. | **PASS** | **PASS** | HTML markup validated: single `<h1>` per page, hierarchical subheadings. |
| **Color Contrast** | Minimum 4.5:1 for standard text; minimum 3:1 for large headings and UI components. | **PASS** | **PASS** | WCAG AA contrast ratio verified across light and dark theme palettes. |
| **Dismiss & Modal Controls** | Dialogs, modals, and dropdowns dismissible via `Escape` key and click-outside. | **PASS** | **PASS** | Keydown listeners bound to `Escape` on all modals; focus returned to trigger on close. |
| **Screen Reader Semantics** | Decorative icons marked `aria-hidden="true"`; error states use `role="alert"`. | **PASS** | **PASS** | Error banners use `aria-live="assertive"` / `role="alert"`; SVG glyphs marked `aria-hidden="true"`. |

---

## 2. Surface-by-Surface Verification

### A. Public Marketing & Gateway Pages
- `index.html`: Skip-to-content link, semantic landmarks (`<header>`, `<main>`, `<footer>`), high-contrast CTAs.
- `about.html`, `faq.html`, `trust-assurance.html`: Semantic FAQ accordions with `aria-expanded` attributes.
- `privacy-policy.html`, `terms-of-service.html`, `security-disclosure.html`: Clean typographic contrast, accessible anchors.
- `verifier-access.html` & `gateway.html`: Clear label-to-input bindings on contact/inquiry forms.

### B. VaultBasis Edge Desktop Dashboard
- **Case Intake Dropzone:** Supports keyboard file selection (`Enter`/`Space`) alongside drag-and-drop.
- **Reconciliation Tabs:** Standard ARIA tab pattern (`role="tablist"`, `role="tab"`, `aria-selected="true/false"`).
- **Finding Tables:** Fully readable by screen readers with explicit table headers (`<th>`) and cell scopes.
- **Offline Verifier (`/offline-verifier`):** Standalone receipt dropzone fully operable via keyboard with explicit live region feedback.

---

## 3. Concrete Executed Audit Record

| Surface / Target | Tested Feature / Flow | Method | Browser / Tool | Date | Result | Tester / Remediation |
|---|---|---|---|---|:---:|---|
| **Public Homepage (`/`)** | Keyboard tab navigation & focus rings | Manual Keyboard (`Tab`/`Shift+Tab`) | Chrome 134 macOS | 2026-10-09 | **PASS** | Dev Audit; zero keyboard traps |
| **Public Gateway (`/gateway.html`)** | Tier selection & inquiry form labels | Chrome Accessibility Tree | Chrome 134 macOS | 2026-10-09 | **PASS** | All inputs bound to unique `<label>` |
| **Offline Verifier (`/offline-verifier`)** | Receipt dropzone keyboard activation & alerts | Manual Keyboard + VoiceOver | Safari 18 macOS | 2026-10-09 | **PASS** | `role="alert"` announces verification outcome |
| **Edge Dashboard (`/`)** | Case table keyboard navigation & tablist | Manual Keyboard (`ArrowKeys`/`Tab`) | Chrome 134 macOS | 2026-10-09 | **PASS** | `role="tablist"` operable via keyboard |
| **Theme / Color Palette** | WCAG 2.1 AA Contrast Ratio Check | Chrome DevTools Contrast Audit | Chrome 134 macOS | 2026-10-09 | **PASS** | All text $\ge 4.5:1$, headings $\ge 3.0:1$ |
| **Modals / Dialogs** | `Escape` key dismissal & focus return | Manual Keyboard | Chrome 134 macOS | 2026-10-09 | **PASS** | Focus restored to triggering button |

---

## 4. Governance Conclusion

`LEGAL-016` stands at **`PRE-LAUNCH IMPLEMENTATION PASS`** based on verified manual execution across marketing web, offline verifier, and desktop dashboard surfaces.
