# MMP-2 Model & Tool Governance Policy

> **Specification Ref:** `MMP2-POL-001`, `MMP2-POL-002`, `MMP2-POL-003`  
> **Core Concept:** Cryptographic Model Provenance and Framework Approval Registries

---

## 1. Model Provenance Registry

Every model artifact installed or executed within VaultBasis must have an entry in the **Model Provenance Registry** tracking origin, licensing, and cryptographic integrity:

```python
class ModelDescriptor(BaseModel):
    model_id: str                          # e.g., "vb-investigator-7b-q4"
    model_family: str                      # e.g., "Mistral", "Llama3", "Qwen"
    model_version: str                     # e.g., "1.2.0"
    publisher: str                         # e.g., "TecTixBase Research"
    base_model: str                        # e.g., "Mistral-7B-Instruct-v0.3"
    fine_tune_origin: Optional[str]        # Dataset hash or training provenance
    weights_sha256: str                    # Cryptographic hash of GGUF file
    license_spdx: str                      # e.g., "Apache-2.0", "MIT"
    commercial_use_allowed: bool = True
    local_only: bool = True
    network_requirement: str = "NONE"
    telemetry_behavior: str = "ZERO_TELEMETRY"
    approved_regions: List[str]            # e.g., ["US", "EU", "CA", "UK", "IN"]
    prohibited_regions: List[str] = []
    policy_tags: List[str] = []            # e.g., ["US_FIRM_COMPLIANT", "FED_AUDIT_OK"]
```

---

## 2. Integrity Verification Gate

Upon initialization, the sidecar verifies the SHA-256 hash of all model weight files against the registry. If a binary is altered, truncated, or tampered with:
- Model loading is immediately aborted.
- An administrative audit event (`MODEL_INTEGRITY_VIOLATION`) is logged in SQLite.
- The Core Daemon continues operating in deterministic mode without failure.

---

## 3. Tool & Framework Approval Gate

To prevent supply-chain vulnerabilities, all third-party libraries (parsers, vector math, embedding models) must pass an SBOM evaluation:
- Zero telemetry dependencies allowed.
- Open-source licenses only (Apache-2.0, MIT, BSD, ISC).
- Strict version pinning in `pyproject.toml` / lockfiles.
