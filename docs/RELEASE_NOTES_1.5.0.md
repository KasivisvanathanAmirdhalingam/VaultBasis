# VaultBasis Release Notes — Version 1.5.0-rc3
**Release Version:** 1.5.0-rc3  
**Classification:** CUSTOMER-FACING  
**Release Date:** 2026-10-08  
**Target Environments:** macOS (Apple Silicon arm64), Windows 10/11 (x64)  

---

## 1. Overview & Highlights

VaultBasis Edge 1.5.0-rc3 is the **pre-signing qualification candidate** for the standalone, air-gapped Form 1099-DA cryptographic reconciliation engine. This release establishes strict Base-10 Decimal precision, zero-network-egress execution, unassisted multi-format intake, Ed25519 cryptographic receipt signing, and complete installation data preservation across upgrades.

> **Production Signing Status Notice:** The current candidate binaries (`VaultBasis-RC3-macOS-arm64.dmg` and `VaultBasis-Setup-1.5.0-rc3.exe`) represent unsigned pre-sign engineering candidates. Microsoft Azure Authenticode signing and Apple Developer ID signing / notarization / stapling are scheduled upon completion of platform identity enrollment prior to general distribution.

---

## 2. Changes by Category

### Added
* **Multi-Format Form 1099-DA & Ledger Intake:** Added unassisted intake for broker 1099-DA reports (CSV, PDF layout) and client crypto tax ledger exports (Coinbase, Kraken, Koinly, standard CSV) with automatic column mapping and SHA-256 source file provenance.
* **Exact Base-10 Decimal Reconciliation Engine:** Implemented exact `decimal.Decimal` financial calculation pipeline preserving sub-cent precision with zero IEEE 754 floating-point drift.
* **Normative RFC 8785 Ed25519 Cryptographic Receipts:** Generates deterministic, verifiable JSON receipts (`receipt-v0.1.json`) cryptographically signed by the local installation key.
* **Zero-Dependency Standalone Offline Verifier:** Packaged standalone verification tool ([`apps/verifier/verify_receipt.py`](file:///Users/kasivisvanathanamirdhalingam/Downloads/VaultBasis/apps/verifier/verify_receipt.py)) enabling external auditors and IRS reviewers to verify receipt integrity in fully air-gapped environments without installing VaultBasis Edge.
* **Graceful Safe Quit & WAL Checkpoint:** Integrated explicit shutdown handler ensuring complete SQLite WAL checkpointing and socket cleanup upon exit.

### Changed
* **Micro-Variance UI Annotation:** Sub-cent non-zero variances ($< \$0.01$) are now explicitly annotated in the dashboard as *"Micro-variance — review if relevant"* to distinguish sub-cent precision from material discrepancies.
* **Canonical Number Normalization:** In canonical receipt records, numeric representations normalize away redundant trailing zeros (e.g. `1.00` $\to$ `"1"`), ensuring unique RFC 8785 cryptographic serialization.
* **Uninstall/Reinstall Identity Preservation:** Routine uninstall and reinstall operations explicitly preserve local database and key storage (`%LOCALAPPDATA%\VaultBasis` on Windows, `~/Library/Application Support/VaultBasis` on macOS).

### Security & Hardening
* **Localhost Loopback Isolation:** Sockets bind strictly to `127.0.0.1` / `::1`; non-loopback Host headers are rejected with `400 Bad Request` to prevent DNS rebinding attacks.
* **`Origin: null` Neutralization & Capability Authorization:** State-mutating HTTP requests (`POST`, `PUT`, `DELETE`, `PATCH`) with `Origin: null` are rejected with `403 Forbidden` unless presenting a valid, unguessable transient session capability header (`X-VaultBasis-Capability`).
* **Zero Capability Leakage:** Automated tests guarantee `LOCAL_SESSION_CAPABILITY` is never serialized into HTML source, API payloads, SQLite storage, receipts, or diagnostic bundles.
* **Strict Path Sanitization & ZIP Slip Defense:** Upload and extraction routines reject relative directory traversal (`../`) and absolute path escapes.
* **Anti-Rollback & Monotonic Sequence Enforcement:** Commercial license tokens and database schema revisions enforce strict sequence counters against downgrade or replay attacks.

### Fixed
* **Box 2 NO vs $0.00 Cost Basis Disambiguation:** Fixed reconciliation matching logic to clearly separate transactions where cost basis is explicitly $0.00 from transactions where Box 2 indicates cost basis was not reported to the IRS.
* **Evaluation Quota Race Condition:** Eliminated concurrency edge cases in the 3-case evaluation limit enforcement.

---

## 3. Known Limitations & Scope Boundaries

* **Tax Years:** Release 1.5.0 is calibrated specifically for Tax Year 2025 Form 1099-DA rulesets (`VB_US_1099DA_2025_R1`).
* **Runtime Deployment:** Single-seat desktop installation; cloud multi-tenancy and remote multi-seat sync are intentionally out of scope for air-gapped privacy.
* **Export Scope:** Generates Form 8949 audit worksheets and cryptographic evidence receipts; does not file directly with IRS Modernized e-File (MeF).

---

## 4. Migration & Compatibility Notice

* **Database Version:** Schema version 6. Upgrades from earlier developer previews automatically migrate SQLite schemas with pre-migration backups created in the local data directory.
* **Receipt Verifier Compatibility:** All receipts generated by 1.5.0-rc3 are fully compatible with standalone verifier v0.1.
