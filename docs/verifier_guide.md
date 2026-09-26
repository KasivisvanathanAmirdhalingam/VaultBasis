# VaultBasis — Independent Verifier Guide

> **Document Version**: v1.0.0-MMP1  
> **Audience**: Independent Reviewers, Auditors, Tax Filers, Third-Party Verifiers  
> **Protocol**: Evidence Contract v0.1  

---

## 1. Verification Philosophy

VaultBasis Outcome Receipts are designed for **unassisted third-party verification**. 

You do **not** need a VaultBasis account, an active license, or network connectivity to verify a receipt. The verification logic relies exclusively on public cryptographic standards:
- **Encoding**: UTF-8 NFC
- **Canonicalization**: RFC 8785 (JSON Canonicalization Scheme)
- **Digest Algorithm**: SHA-256 (FIPS 180-4)
- **Signature Algorithm**: Ed25519 (RFC 8032 PureEdDSA)

---

## 2. Option A: Command-Line Verification (Zero-Cloud)

The standalone verifier CLI (`apps/verifier/verify_receipt.py`) has zero proprietary dependencies and requires only standard Python 3.8+ with the `cryptography` library.

### Verify Receipt Signature and Schema:
```bash
python3 apps/verifier/verify_receipt.py path/to/receipt-v0.1.json
```

### Verify with Evidence Bundle (Checking Source Hashes):
```bash
python3 apps/verifier/verify_receipt.py path/to/receipt-v0.1.json --evidence-dir path/to/evidence/
```

### JSON Machine-Readable Output:
```bash
python3 apps/verifier/verify_receipt.py path/to/receipt-v0.1.json --json
```

---

## 3. Option B: Web Drag-and-Drop Verification

1. Start or open the VaultBasis Verifier tool at:
   [http://127.0.0.1:8000/verifier](http://127.0.0.1:8000/verifier)
2. Drag and drop any `receipt-v0.1.json` into the dropzone.
3. The browser runs cryptographic validation and displays the status of all five checks:
   - `[1] JSON Schema Conformance`
   - `[2] Evidence Contract Version`
   - `[3] Key Fingerprint Integrity`
   - `[4] Ed25519 Cryptographic Signature`
   - `[5] Source Hashes Match`

---

## 4. Understanding Outcome States

| State | Interpretation |
| :--- | :--- |
| `MATCHED` | All proceeds, cost basis, and dates match within tolerance ($0.01). |
| `BASIS_DIFFERENCE` | Proceeds match, but cost basis diverges between broker and ledger. |
| `PROCEEDS_DIFFERENCE` | Gross proceeds diverge between broker and ledger. |
| `REPORTING_SCOPE_DIFFERENCE` | Form 1099-DA Box 2 indicates non-covered asset under 2025 transition rules. |
| `UNRESOLVED_DATA` | Required fact was missing from sources; unknown was preserved without guessing. |

---

## 5. Mandatory Limitations Notice

> Verification of this receipt confirms cryptographic origin from the declared installation key and byte integrity under Evidence Contract v0.1. Verification does NOT constitute tax or legal advice, nor does it represent endorsement by the Internal Revenue Service (IRS).
