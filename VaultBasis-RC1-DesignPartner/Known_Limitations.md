# Known Limitations (MMP-1 Design Partner Preview)

This RC1 build is strictly for preview and validation. It is not approved for live client tax filings or regulatory submission.

## Scope Limitations
- **File Formats**: Currently only supports the provided `Form 1099-DA` CSV profile v0.1 and `Koinly` default CSV export formats.
- **Reporting Scope**: This software does NOT determine tax compliance, basis conservation validity, or safe-harbor eligibility. It is a deterministic difference engine.
- **Unresolved Data**: Missing fields in source data are intentionally flagged as `UNRESOLVED_DATA` rather than coerced to $0.00.
- **Networking**: The application binds strictly to `127.0.0.1`. It does not transmit payload data to the internet (Zero Egress boundary tested in AC-07).

## Legal Notice
VaultBasis does not hold itself out as providing tax or legal advice. Whether VaultBasis, its activities, or particular service arrangements implicate tax-return-preparer or related obligations is reserved for counsel determination.
