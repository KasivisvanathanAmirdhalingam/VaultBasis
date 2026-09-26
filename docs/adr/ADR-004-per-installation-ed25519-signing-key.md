# ADR-004: Per-Installation Ed25519 Signing Keypair Model

* **Status**: ACCEPTED / FROZEN  
* **Date**: 2026-09-23  
* **Deciders**: VaultBasis Architecture Group  
* **PRD Reference**: §6.4(B) (Receipt Signing Key Decision), §13.5 (Signing Key Model), §44.3 (Signatures)  

---

## Context and Problem Statement

Outcome Receipts issued by VaultBasis must be tamper-evident and cryptographically signed. Two alternative paradigms exist:
1. **Centralized Cloud Signing Authority (CA)**: The Edge transmits the receipt digest to a central VaultBasis cloud service that signs with a company master key.
2. **Public Blockchain Anchoring**: The Edge submits transactions to Ethereum / Solana / Polygon and pays gas fees to record Merkle roots on-chain.
3. **Per-Installation Local Keypair**: The Edge generates a local cryptographic keypair on first run; the private key never leaves the customer host.

## Decision Drivers

* No cloud signing service dependency (maintains zero egress and offline operation).
* No blockchain, gas fees, or third-party consensus dependencies (PRD §2.7).
* Verifiers must be able to verify that the receipt payload has not been modified since it was emitted by the local installation.

## Decision Outcome

1. **Per-Installation Ed25519 Keypair**:
   - On initial boot, Edge generates a fresh Ed25519 keypair using the host's cryptographically secure random number generator (`os.urandom`).
   - The private key is persisted with atomic `0600` POSIX file permissions in local state.
   - The receipt declares `signer_type: "INSTALLATION_KEY"`, `signer_key_id` (SHA-256 fingerprint of public key), and `signer_public_key` (hex representation).
2. **Signature Semantics**:
   - Signature is computed over the 32-byte SHA-256 digest of canonical UTF-8 bytes (RFC 8785) of the receipt excluding `signature`.
   - The verifier proves that the receipt was signed by that specific installation key and has suffered zero byte tampering.
   - Per PRD §13.5 and §44.6, the signature proves byte integrity and key possession; it does not claim to certify legal or tax accuracy.

### Positive Consequences
* Completely autonomous, offline signing with zero network dependencies.
* No gas fees or crypto token requirements.
* Fast signing (<1ms) and instant verification.

### Negative Consequences
* Downstream verifiers establish integrity under that installation key, but cannot verify whether the software running on that host was untampered without future remote attestation (deferred to MMP-2 enterprise PKI).
