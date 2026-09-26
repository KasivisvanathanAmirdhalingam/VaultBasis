# Evidence Contract v0.1 — Normative Verification Specification

> **Artifact ID**: `schemas/receipt/verification-v0.1.md`  
> **Status**: NORMATIVE / FROZEN  
> **Scope**: Evidence Contract v0.1 (MMP-1)  
> **Environment**: Offline, Zero-Cloud, Standalone Clean Machine  

---

## 1. Verification Philosophy

Per PRD §13.8, independent verification must be possible:
- Completely offline without internet access.
- Without an account, license key, or API token.
- Without any VaultBasis cloud service or central coordinator.
- Without an LLM or probabilistic reasoning.
- Without disclosing customer transactions to any third party.

---

## 2. Normative Verification Algorithm

An independent verifier processing a receipt file $F$ (and optional evidence bundle containing source files) must execute the following sequential checks:

```
           [ Input Receipt File ]
                     │
                     ▼
           [ 1. JSON Schema Check ] ──────────► (FAIL: Malformed / Incompatible)
                     │
                     ▼
           [ 2. Version Check ] ──────────────► (FAIL: Unsupported Version)
                     │
                     ▼
           [ 3. Key Fingerprint Check ] ──────► (FAIL: Key ID != SHA256(PubKey))
                     │
                     ▼
           [ 4. Canonicalization & Digest ]
                     │
                     ▼
           [ 5. Ed25519 Signature Verify ] ───► (FAIL: Signature Invalid / Tampered)
                     │
                     ▼
       (Optional: Source Files Present?)
            │                     │
           Yes                    No
            │                     │
            ▼                     │
    [ 6. Source Hash Match ]      │
            │                     │
            └──────────┬──────────┘
                       │
                       ▼
           [ Emit Structured Report ]
           - Signature: PASS
           - Canonicalization: PASS
           - Schema: PASS
           - Outcome State: <state>
           - Assurance Level: <level>
           - Limitations Notice
```

### Detailed Verification Steps

#### Step 1: Schema Conformance Check
- Validate the input document against `schemas/receipt/receipt-v0.1.json`.
- If schema validation fails, halt immediately with status `REJECTED_SCHEMA_INVALID`.

#### Step 2: Version Compatibility Check
- Verify that `receipt_version == "v0.1"`.
- If the receipt indicates an unknown or higher minor/major version without backward compatibility rules, halt with status `UNSUPPORTED_VERSION`. Silent guessing of semantics is forbidden (PRD §44.7).

#### Step 3: Signer Key Fingerprint Validation
- Parse `signer_public_key` (32 bytes from 64-char hex string).
- Compute `SHA-256(RawPublicKeyBytes)`.
- Compare hex digest against `signer_key_id`.
- If mismatch, halt with `FAIL_KEY_FINGERPRINT_MISMATCH`.

#### Step 4: Canonicalization & Digest Computation
- Extract and remove the `signature` property from the receipt object.
- Canonicalize the remaining 24 properties into UTF-8 bytes using RFC 8785 rules as specified in `canonicalization-v0.1.md`.
- Compute 32-byte digest $D = \text{SHA-256}(\text{CanonicalUTF8Bytes})$.

#### Step 5: Cryptographic Signature Verification
- Decode the 128-char hex string in `signature` into 64 raw bytes.
- Using the Ed25519 public key, verify the signature over digest $D$.
- If verification fails, return `FAIL_SIGNATURE_TAMPERED`.
- If verification succeeds, record `SIGNATURE: PASS`.

#### Step 6: Source Integrity Verification (When Evidence Bundle is Provided)
- For each source file provided in the evidence package:
  - Compute `SHA-256(SourceFileBytes)`.
  - Check that the digest matches the corresponding entry in `source_hashes[source_id]`.
- If any source file does not match its declared hash, record `SOURCE_HASH: FAIL` for that source.
- If no source files are provided, record `SOURCE_INTEGRITY: UNVERIFIED_NO_EVIDENCE_ATTACHED`.

---

## 3. Mandatory Limitations Notice

Every verifier output (CLI, API, or Web) must append the normative limitations notice specified in PRD §27 and §44.6:

> **LIMITATION STATEMENT**:
> Verification of this receipt confirms cryptographic integrity and origin from the declared installation key under Evidence Contract v0.1.
> Verification does NOT constitute:
> 1. Legal advice or tax advice.
> 2. An assertion that source systems, brokers, or tax filers acted fraudulently or correctly.
> 3. Official endorsement or certification by the Internal Revenue Service (IRS) or any government taxing authority.
