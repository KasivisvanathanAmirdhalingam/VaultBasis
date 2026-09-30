# Visual acceptance matrix — MMP11-VISUAL-001

Initial population under VB-GOV-001; qualification task remains open. Source: [25 dated screenshots](evidence/2026-09-30/README.md). Captured ≠ reviewed ≠ qualified. Developer visual observations are not founder approval. Desktop 1440×900 and mobile viewport 390×900; no real-device qualification implied.

| Surface | Desktop evidence | Mobile evidence | Functional | Accessibility | UX review | Action / task |
|---|---|---|---|---|---|---|
| Home | Captured | Captured; structural review | Page load only | Full review pending | Duplicate section nav/resource-heavy narrative observed | MMP11-UX-PAGES-001 |
| Trust | Captured; structural review | Captured | Page load only | Full review pending | Card-heavy reference observed | MMP11-UX-PAGES-001 |
| About | Captured | Captured | Page load only | Pending | Pending detailed review | MMP11-UX-PAGES-001 |
| Contact | Captured | Captured | Mail delivery not exercised | Pending | Pending | MMP11-UX-PAGES-001 |
| Access dialog | Open-state capture | Missing open-state capture | Submission not exercised | Observed focus FAIL | Full state review pending | MMP11-A11Y-001 / MMP11-ACCESS-001 |
| Verifier access | Captured | Captured | Anonymous landing observed | Pending | Credential journey pending | MMP11-ACCESS-001 |
| Hosted verifier | Gate captured only | Gate captured only | Pending authenticated access | Pending | Not inspected behind gate | MMP11-JOURNEY-001 |
| Privacy | Captured | Captured | Page load only | Pending | Pending | MMP11-UX-PAGES-001 |
| Terms | Captured | Captured | Page load only | Pending | Pending | MMP11-UX-PAGES-001 |
| Security | Captured | Captured | Mail delivery not exercised | Pending | Pending | MMP11-UX-PAGES-001 |
| Scope | Captured | Captured; structural review | Page load only | Pending | Separate document shell observed | MMP11-UX-PAGES-001 |
| FAQ | Captured | Captured | Page load only | Pending | Pending | MMP11-UX-PAGES-001 |
| Unknown route / 404 | Wrong Home response captured | Wrong Home response captured | FAIL: Home/200 | Intended error page not reached | Misleading destination | MMP11-NAV-404-001 |
| Edge surfaces | No exact-package capture | Not applicable unless declared supported | Recipient qualification pending | Pending native review | Source/historical only | MMP11-EDGE-AUDIT-001 |

Before founder review replace pending observations with exact protected-candidate evidence for every relevant loading/empty/success/error state, and separately link qualified Edge captures. Do not adopt these current screenshots as approved visual-regression baselines.
