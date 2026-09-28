# VaultBasis MMP-1 Release Manifest

**Release Status**: `vaultbasis-mmp1-rc1` (Release Candidate 1)  
**Build Timestamp**: 2026-09-27T12:00:00Z  
**Release Timestamp**: TBD — Approved for controlled Design-Partner Preview packaging  

---

## 1. Versions & Provenance

| Component | Version / Identifier |
| :--- | :--- |
| **VaultBasis Edge Version** | `v26.1-mmp1-rc1` |
| **Git Tag** | `vaultbasis-mmp1-rc1` |
| **Commit SHA** | `d99e447b8f76ac6bbcdef08067910e36efe8057e` |
| **Evidence Contract Version** | `v0.1` |
| **Semantic Specification** | `v26.1 Baseline (SEM-ING, SEM-TIME, SEM-MATCH)` |
| **Golden Corpus Version** | `Layer A-D (G001-G045, V001-V012)` |

### AC-06 Offline Clean-Machine Ceremony
* **Artifact**: `docs/AC06_Offline_Ceremony_Evidence.md`
* **Result**: PASS
* **Verifier SHA-256**: `ab2c137ce7f348f3318e66ec588d8cb0fe5556c91f528d0a8aa0fe0605262b17`
* **Ceremony Environment**: Ubuntu 24.04 VM, Firefox 125.0.1
* **Network State**: OFFLINE

---

## 2. Cryptographic Integrity

| Artifact | SHA-256 Hash |
| :--- | :--- |
| `independent_verifier.html` | `ab2c137ce7f348f3318e66ec588d8cb0fe5556c91f528d0a8aa0fe0605262b17` |
| **macOS Native Binary (Edge)** | `f834d8cc39401fbaea0d41e7eb68bb274e1d1b54a23ab7f4575ec65c924bc01c` |
| **Container Digest (Docker/OCI)** | *NOT DISTRIBUTED IN THIS PREVIEW* |

### Signing & Public-Key Information
* **Signing Algorithm**: Ed25519
* **Signer Type**: Locally generated persistent installation key (Generated per Edge Installation)
* **OS Signing**: Apple Developer ID Signed (macOS Native Package)

---

## 3. Supported Environment & Bounds

### Distribution Profiles
* **macOS 14+**: Native package (clean-installed and validated)
* **Docker/OCI**: Validated container runtime

### Supported Input Adapters
1. **Form 1099-DA** (Coinbase standard CSV export)
2. **Koinly Capital Gains Report** (CSV)
3. **VaultBasis Canonical Format** (CSV)

### Declared Resource Limits
* **Maximum File Size**: 50 MB
* **Maximum Row Count**: 100,000 rows per source
* **Maximum Row Length**: 1 MB
* *Exceeding limits safely fails with bounded errors (`RESOURCE_EXHAUSTED` / `FILE_TOO_LARGE`).*

---

## 4. Known Limitations & Deferred Scope

### Deferred Semantics
1. **Quantity Differences (GAP-001)**: G004 is explicitly omitted from MMP-1 execution. Quantity discrepancy reconciliation is deferred to future releases.
2. **Rounding / Tolerances (SEM-ROUND-002)**: G017 is BLOCKED. VaultBasis does not automatically invent tolerances for micro-rounding. Differences in rounding deterministically yield a `BASIS_DIFFERENCE` or `PROCEEDS_DIFFERENCE`.
3. **Multi-Lot HIFO Optimization**: Deferred; relies on provided input matching rather than solving complex inventory allocations.

### Known Limitations
* **Receipt Signatures**: Receipts are signed by a local installation key; public key distribution for global verification is out-of-scope for the MMP-1 Preview.
* **Network Egress (AC-07)**: Egress boundaries have been verified by disabling Python socket interactions; physical firewall egress monitoring is recommended.

---

## 5. Next Steps

1. **Checksums & Provenance**: Finalize container digests and executable hashes.
2. **OS Signing**: Apply Apple Notarization / Developer ID signing where practical.
3. **Verification Guide**: Finalize CPA guides for Edge usage and `independent_verifier.html` execution.
4. **Partner Acquisition**: Commence design-partner onboarding in parallel.
