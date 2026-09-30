# Anonymous production observation packet

Captured 2026-09-30T20:35:53.642Z against `https://vaultbasis.com` using Playwright with Chromium 153.0.8010.12. Viewports: 1440×900 and 390×900. Twelve routes per viewport and one open access-dialog screenshot: 25 PNGs. [Raw observations](production-observations.json) list route, final URL, response status, headings, links/buttons, page overflow and console errors. The open-dialog tab sequence is recorded separately.

This is a read-only production audit: no access form submission, credentials, real email, artifact entitlement or client evidence. The hosted verifier was observed only through its anonymous access redirect. Mobile viewport simulation is not real-device qualification. Source SHA is not established: homepage metadata says `preview`. The unknown-route HTTP 200/homepage response and modal focus escape are defects, not passes.

Selected visual review: [Home/mobile](home-390.png), [Trust/desktop](_trust-assurance-1440.png), [Scope/mobile](_docs_scope_and_limitations_v0_1_html-390.png). Full-page images may be scaled in viewers; use native resolution for visual judgment. These are developer captures, not original founder screenshots or founder approval.

[capture.cjs](capture.cjs) preserves the read-only capture procedure. It requires an available Playwright installation and matching Chromium browser; neither was added to project dependencies. Run from an environment with network access and set `VB_AUDIT_OUTPUT` to a new, non-existing evidence directory. Example from repository root:

```sh
VB_AUDIT_OUTPUT=/private/tmp/vaultbasis-new-audit node docs/ux/evidence/2026-09-30/capture.cjs
```

The saved script was made portable after this capture and refuses to overwrite an existing directory; it was syntax-checked, not rerun. A new run is new evidence, not a replacement for this timestamped record. [SHA256SUMS](SHA256SUMS) covers images, raw observations and capture script. Hashes establish file integrity only, not independent attestation or completeness of the audit.
