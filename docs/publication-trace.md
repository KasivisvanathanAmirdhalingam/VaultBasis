# Production Publication Trace (frozen procedure, v0.1)

Fill exactly once per clean-machine download test. Repository state and green CI
are NOT evidence of deployment — only this trace, completed against the live
endpoint, can move an artifact to PUBLICATION VERIFIED. Preserve stale artifacts
(hashes + package identity) as UAT evidence; never overwrite or silently relabel.

## Trace

- Date / tester / client machine (OS exact version, arch):
- Vercel deployment commit SHA:
- Download API revision (code + config):
- Entitlement channel shown to this tester (e.g. RC1 Preview vs design-partner channel):
- Detected platform for this request:
- Resolved release:
- Resolved artifact identifier/path:
- Expected SHA-256 (from qualified release manifest):
- Downloaded ZIP SHA-256 (actual):
- Package contents (exact filenames):
- Guide revision found inside (RC1 dark guide vs RC3 practitioner guide):
- Match qualified manifest? YES / NO:

## Result

**PASS / FAIL.** FAIL preserves the download + screenshots under UAT-MAC-003 /
UAT-WIN-001 and opens (or confirms) distribution defects. A fresh publication that
serves unqualified CI binaries to make a test pass is itself a FAIL — production
may correctly read "preview currently unavailable" until RC3-MAC / RC3-WIN qualify.

## Known serving-chain facts (repo evidence, 2026-09-28)

- `apps/web-marketing/api/download.js` hard-codes artifact path and filename
  `VaultBasis-RC1-DesignPartner.zip` — redeploying the site without changing the
  artifact store re-serves the same stale ZIP.
- `apps/web-marketing/api/request-access.js` entitlement copy reads "RC1 Preview";
  `marketing/public/entitlement.html` references Release RC1 and the RC1 ZIP.
- Remediation belongs to RC3 distribution implementation (manifest-driven
  resolution + platform/arch allowlist), not to ad-hoc edits here.
