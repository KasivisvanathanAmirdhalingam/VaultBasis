# VaultBasis Edge — Local Deployment Guide (MMP-1)

> **Document Version**: v1.0.0-MMP1  
> **Target Audience**: CPAs, Enterprise Testers, Design Partners  
> **Deployment Model**: Local-First / Customer-Premises Trust Boundary  

---

## 1. System Requirements

* **Operating System**: macOS (ARM64/x86_64), Linux (Debian/Ubuntu/RHEL), or Windows (WSL2).
* **Runtime**: Python 3.9+ (or Docker / OCI container runtime).
* **Dependencies**: Python standard library + `cryptography`, `pydantic`, `fastapi`, `uvicorn`, `jsonschema`.
* **Network**: Offline / Airgapped supported. Zero internet access required.

---

## 2. Quick Start (Native Launch)

1. Clone or unpack the repository into your secure working directory:
   ```bash
   cd /path/to/VaultBasis
   ```
2. Validate the installation and security posture using the industrial validation script:
   ```bash
   ./scripts/validate_before_commit.sh
   ```
3. Start the VaultBasis Edge daemon and Web Application:
   ```bash
   ./scripts/launch.sh
   ```
4. Access the local web surfaces:
   - **Customer Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - **Public Verifier Tool**: [http://127.0.0.1:8000/verifier](http://127.0.0.1:8000/verifier)
   - **Interactive API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **Architecture & Overview**: [http://127.0.0.1:8000/about](http://127.0.0.1:8000/about)

---

## 3. End-to-End User Journey

1. **Create Case**: Open the Dashboard and click `+ New Case`. Enter a descriptive identifier (e.g. `CASE-2025-COINBASE-01`).
2. **Ingest Documents**:
   - Upload your Broker Form 1099-DA representation (CSV or JSON).
   - Upload your Koinly Capital Gains Report CSV (or VaultBasis Reconciliation fallback CSV).
   - VaultBasis computes streaming SHA-256 hashes and normalizes rows into canonical transactions on local CPU.
3. **Execute Deterministic Reconciliation**:
   - Click `⚡ Run Deterministic Reconciliation`.
   - The engine compares proceeds, cost basis, dates, and reporting scopes, mapping discrepancies into one of 13 bounded outcome states.
4. **Inspect Evidence & Provenance**:
   - Review material differences and itemized variances.
   - Inspect shallow provenance links to the exact source row references and file digests.
5. **Issue & Export Outcome Receipt**:
   - The system cryptographically signs the canonical receipt using your local Ed25519 installation key.
   - Click `📥 Download Evidence Bundle (.ZIP)` to retrieve the self-contained verification package.
