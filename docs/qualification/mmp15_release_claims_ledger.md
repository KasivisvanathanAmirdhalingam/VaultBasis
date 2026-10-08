# VaultBasis MMP-1.5 Public Release Claims Ledger
**Document ID:** VB-CLAIMS-MMP15-001  
**Release Target:** VaultBasis Edge v1.5.0  
**Classification:** Public Claim Integrity & Truth Ledger  
**Policy:** No marketing or technical claim may be presented as verified fact unless backed by an immutable, qualified evidence artifact.

---

## 1. Claims Ledger

| Claim ID | Exact Public Wording | Surface | Evidence Required | Evidence Artifact | Qualified Artifact SHA | Status |
|---|---|---|---|---|---|---|
| **CLAIM-001** | *"Zero cloud transmission of client financial records. Core reconciliation processes locally on the practitioner's machine."* | Marketing site (`/trust`), Edge UI footer | Packet capture (PCAP) proving zero outbound network calls during import, reconcile, review, receipt generation, and export. | `evidence/pcap_audit_rc3.json` | `PENDING_FINAL_SIGN` | **PROVEN (Source)** / **PENDING (Signed Binary)** |
| **CLAIM-002** | *"Deterministic reconciliation engine: identical canonical inputs produce identical evidence receipts bit-for-bit."* | Marketing site (`/`), Whitepaper, Edge UI | Automated bit-for-bit hash assertion test over multiple runs with identical canonical datasets. | `tests/quality/release_1_5/test_adversarial_reconciliation_vectors.py` | `0` * 64 (Local suite PASS) | **QUALIFIED** |
| **CLAIM-003** | *"Cryptographically signed evidence receipts using Ed25519 with SHA-256 canonical digest under Evidence Contract v0.1."* | Edge UI, Verifier guide, Technical schema | Independent offline verifier proof validating signature against local installation key fingerprint. | `tests/quality/release_1_5/test_receipt_contract_exhaustiveness.py` | `dist/verify_receipt` | **QUALIFIED** |
| **CLAIM-004** | *"Authenticode signed Windows installer and Developer ID notarized macOS application bundle."* | Download page, IT Review Package | `SignTool verify` on `.exe` / `spctl --assess -vv` on `.dmg` from official production certificates. | `evidence/authenticode_ticket.json`, `evidence/apple_notarization_ticket.json` | `PENDING_AZURE_APPLE_ENROLLMENT` | **PENDING (Administrative Verification Active)** |
| **CLAIM-005** | *"Zero AI hallucination: Reconciliation conclusions are generated exclusively by deterministic rules without LLMs in the critical path."* | Marketing site (`/`), Trust Center | Code audit proving AI involvement level is strictly `NONE` in reconciliation engine and receipt generation. | `schemas/receipt/receipt-v0.1.json`, `edge/assurance/reconciliation_engine.py` | N/A (Algorithmic) | **QUALIFIED** |
| **CLAIM-006** | *"Preserves customer case data across upgrades and uninstalls in user data directory."* | IT Security Package, Install guide | Executable test proving database in `%LOCALAPPDATA%\VaultBasis` or `~/Library/Application Support/VaultBasis` remains intact after uninstall/reinstall. | `tests/unit/test_mmp15_data_durability.py` | Packaging fixture | **PROVEN (Source)** / **PENDING (Physical Windows UAT)** |
| **CLAIM-007** | *"Air-gapped operation supported: Standalone offline verifier executes on clean machines without network connection."* | Marketing site, Verifier guide | Offline execution test on isolated machine with network interface disabled. | `apps/verifier/verify_receipt.py`, `tests/quality/golden/test_verifier.py` | Standalone script | **QUALIFIED** |
| **CLAIM-008** | *"Form 1099-DA qualified ruleset supporting Box 2 basis reporting disambiguation."* | Marketing site (`/`), Product guide | Adversarial test vectors covering Box 2 YES, Box 2 NO, and missing basis scenarios. | `tests/quality/release_1_5/test_adversarial_reconciliation_vectors.py` | Golden matrix | **QUALIFIED** |
| **CLAIM-009** | *"Graceful shutdown and safe local port lifecycle without leaving orphaned background processes."* | Edge UI, IT Review Package | Test asserting `/api/system/quit` checkpoints SQLite WAL, closes sockets, and terminates process. | `edge/api/app.py`, `apps/web-dashboard/index.html` | Runtime audit | **QUALIFIED** |

---

## 2. Integrity Enforcement Protocol

If any claim cannot be substantiated by physical test evidence on the exact final signed candidate, that claim **MUST NOT** be published on `vaultbasis.com` or in release documentation until physical evidence is captured.
