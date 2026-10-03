# VaultBasis Evidence Readiness Model

## 1. Readiness vs. Factual Validity
VaultBasis enforces a strict semantic boundary: **Evidence Readiness is not Factual Truth**.

- **What Readiness establishes:**
  1. The file was received and read successfully without file-system corruption.
  2. The file format matches a supported source profile (e.g. Form 1099-DA or Koinly CSV).
  3. Required structural fields (Property/Asset, Dates, Proceeds, Basis) are present and parseable.
  4. The file integrity has been cryptographically fingerprinted using SHA-256.
  5. The evidence is suitable for execution by the deterministic reconciliation engine.

- **What Readiness does NOT establish:**
  1. That the taxpayer's underlying transactions are complete.
  2. That broker records are factually error-free.
  3. That tax treatments or holding periods are legally accurate.

---

## 2. Bounded Readiness States
- `READY`: All preflight checks passed; document fingerprinted and parsed; ready for reconciliation.
- `PENDING`: Waiting for document upload/ingestion.
- `UNSUPPORTED / PARSE_ERROR`: File format unparseable or missing required column schema.
