# Evidence Contract v0.1 — Normative Signing Specification

> **Artifact ID**: `schemas/receipt/signing-v0.1.md`  
> **Status**: NORMATIVE / FROZEN  
> **Scope**: Evidence Contract v0.1 (MMP-1)  
> **Cryptography Standards**: RFC 8032 (Ed25519 / PureEdDSA), FIPS 180-4 (SHA-256)  

---

## 1. Key Lifecycle Architecture (MMP-1)

Under MMP-1, VaultBasis operates under a **per-installation signing model**:
1. At initial startup, VaultBasis Edge inspects its local state directory (`/var/lib/vaultbasis/keys/` or equivalent local path).
2. If no signing key exists, Edge generates a fresh, cryptographically secure **Ed25519 keypair** using the operating system's CSPRNG (`os.urandom` or platform equivalent).
3. The private key remains exclusively on local customer storage with POSIX permissions `0600` (readable and writable only by the process owner).
4. The private key is **never transmitted over any network**, never included in diagnostics, and never stored in cloud infrastructure.

```
+--------------------------------------------------------------+
|                     Edge Trust Boundary                      |
|                                                              |
|   [ CSPRNG Keygen ]                                          |
|          │                                                   |
|          ├─► Private Key (0600 local disk) ──┐               |
|          │                                   │               |
|          └─► Public Key (32 bytes)           │               |
|                    │                         │               |
|                    ├─► signer_public_key     │               |
|                    └─► SHA-256 Fingerprint   │               |
|                              │               │               |
|                              ▼               │               |
|                        signer_key_id         ▼               |
|   Canonical Receipt Bytes ─► SHA-256 Digest ─► Ed25519 Sign  |
|                                                      │       |
|                                                      ▼       |
|                                                  signature   |
+--------------------------------------------------------------+
```

---

## 2. Key Identifiers

### 2.1 Public Key
- 32-byte Ed25519 public key.
- Represented in the receipt as a 64-character lowercase hexadecimal string in `signer_public_key`.

### 2.2 Signer Key ID (Key Fingerprint)
- Computed as the SHA-256 hash of the 32 raw binary bytes of the public key:
  $$\text{signer\_key\_id} = \text{Hex}(\text{SHA-256}(\text{RawPublicKeyBytes}))$$
- Represented as a 64-character lowercase hexadecimal string in `signer_key_id`.

### 2.3 Signer Type
- In MMP-1, `signer_type` must be strictly set to `"INSTALLATION_KEY"`.
- This ensures downstream verifiers know the signature guarantees provenance from a specific installation rather than a central VaultBasis CA.

---

## 3. Signing Procedure

Given an unsigned receipt object $R$ conforming to `receipt-v0.1.json` with all fields populated except `signature`:

1. **Verify Invariants**: Ensure all 24 fields are present, valid according to schema rules, and formatted per `canonicalization-v0.1.md`.
2. **Canonicalize**: Serialize $R$ (excluding `signature`) into UTF-8 bytes using RFC 8785 canonical rules:
   $$B = \text{Canonicalize}(R \setminus \{\text{signature}\})$$
3. **Compute Digest**: Calculate 32-byte SHA-256 digest:
   $$D = \text{SHA-256}(B)$$
4. **Sign Digest**: Sign the 32-byte digest $D$ with the installation's Ed25519 private key:
   $$S = \text{Ed25519\_Sign}(\text{PrivateKey}, D)$$
5. **Format Final Receipt**: Convert the 64-byte binary signature $S$ to a 128-character lowercase hex string:
   $$\text{Receipt}.\text{signature} = \text{Hex}(S)$$
6. The resulting object is the finalized, portable Outcome Receipt.

---

## 4. Cryptographic Proof vs. Legal Authority Notice

Per PRD §13.5 and §44.6:
> **A valid signature proves possession of the corresponding installation private key and integrity of the signed bytes under the declared cryptographic scheme. It does NOT prove legal correctness, tax correctness, source authenticity, source completeness, or IRS endorsement.**
