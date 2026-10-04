# VaultBasis Commercial License Token Specification v1.0

> **Standard:** Normative Protocol Specification  
> **Status:** FROZEN BASELINE (MMP-1.5)  
> **Scope:** Cryptographic envelope, canonicalization, key management, temporal state machine, and entitlement evaluation rules for VaultBasis offline commercial licenses.

---

## 1. Cryptographic Primitive Hierarchy & Signing Contract

All VaultBasis commercial license tokens are cryptographically signed using Ed25519 (RFC 8032) over a 32-byte SHA-256 digest of the canonical JSON representation of the license payload.

```
Token String (Base64URL or JSON)
       │
       ▼
JSON Envelope Parse (Strict Duplicate Key Rejection)
       │
       ├──> Envelope {"payload": {...}, "signature": "<hex>", "key_id": "<id>"}
       │
       ▼
Payload Validation (Schema v1.0, UTC ISO 8601 Chronology)
       │
       ▼
RFC 8785 JSON Canonicalization (JCS) -> canonical_utf8_bytes
       │
       ▼
SHA-256 Digest (32 bytes) -> sha256(canonical_utf8_bytes)
       │
       ▼
Ed25519 Verify (Signature, Digest, Keyring[key_id]) -> Boolean
```

### 1.1 Formal Mathematical Construction
$$\text{Digest} = \text{SHA256}(\text{JCS}(\text{Payload}))$$
$$\text{Valid} = \text{Ed25519Verify}(\text{PublicKey}_{\text{key\_id}}, \text{Digest}, \text{Signature})$$

### 1.2 Fixed Protocol Parameters
- **Signature Algorithm:** PureEd25519 (`ed25519` / RFC 8032).
- **Hash Function:** SHA-256 (NIST FIPS 180-4, 32 bytes).
- **Canonicalization Scheme:** JSON Canonicalization Scheme (RFC 8785 / JCS).
- **Signature Format:** 64-byte raw Ed25519 signature encoded as 128 lowercase hexadecimal characters.
- **Key Identifier:** UTF-8 string (e.g., `"k1"`, `"k2026_1"`) identifying the signing key version.

---

## 2. Token Data Structures & Schema

### 2.1 License Envelope Schema
```json
{
  "payload": {
    "version": "v1.0",
    "license_id": "LIC-2026-0001",
    "customer_id": "CUST-ACME-CPA",
    "issued_at": "2026-10-04T12:00:00Z",
    "not_before": "2026-10-04T12:00:00Z",
    "expires_at": "2027-10-04T12:00:00Z",
    "grace_until": "2027-11-03T12:00:00Z",
    "tier": "PRACTICE",
    "max_cases_per_installation": 250,
    "entitlements": [
      "reconciliation",
      "offline_export",
      "reviewer_workflow"
    ],
    "installation_id": null,
    "key_id": "k1"
  },
  "signature": "3b2e... (128 hex chars) ...91a4",
  "key_id": "k1"
}
```

### 2.2 Field Definitions & Rules
| Field | Type | Mandatory | Invariant / Validation Rule |
|---|---|---|---|
| `version` | string | Yes | Must be exactly `"v1.0"`. Other versions fail to `UNSUPPORTED_VERSION`. |
| `license_id` | string | Yes | Unique license identifier (e.g. `LIC-YYYY-XXXX`). |
| `customer_id` | string | Yes | Unique firm / customer reference. |
| `issued_at` | string (ISO 8601) | Yes | UTC timestamp with explicit timezone (`Z` or `+00:00`). Naive timestamps prohibited. Must satisfy `issued_at <= expires_at`. |
| `not_before` | string (ISO 8601) | Yes | UTC timestamp. Must satisfy `not_before <= expires_at`. |
| `expires_at` | string (ISO 8601) | Yes | UTC timestamp. Active tier expiration boundary. |
| `grace_until` | string (ISO 8601) | Yes | UTC timestamp. Grace period termination boundary. Must satisfy `expires_at <= grace_until`. |
| `tier` | enum | Yes | Must be one of: `TRIAL`, `ESSENTIAL`, `PRACTICE`, `ENTERPRISE`. |
| `max_cases_per_installation` | integer | Yes | Strict positive integer (`> 0`). Enforceable local installation case capacity limit. |
| `entitlements` | array[string] | Yes | Explicit capability identifiers. Unknown strings are preserved for forward compatibility but NEVER grant capabilities. |
| `installation_id` | string / null | No | If non-null, license is bound to a specific local installation ID hash. |
| `key_id` | string | Yes | Key identifier. Must match envelope `key_id` exactly. |

---

## 3. Strict Parser & Canonicalization Rules

1. **Duplicate Key Rejection:** Any JSON input with duplicate keys at any nesting level MUST be rejected as `MALFORMED` before canonicalization.
2. **RFC 8785 Serialization:**
   - Object keys sorted by UTF-16 code units (lexicographical order).
   - Compact delimiters: comma `,` and colon `:` with no surrounding whitespace.
   - Exact string preservation; no exponential notation for numbers.
3. **No Signature Field in Canonical Digest:** The signature is computed strictly over `payload`. The envelope `signature` and outer `key_id` are not part of the payload digest calculation.

---

## 4. Key Management & Keyring Resolution

1. **Keyring Mapping:** Edge runtime resolves public verification keys from an immutable local mapping: `Keyring: Map[KeyID, PublicKeyHex]`.
2. **Key Rotation Protocol:**
   - A new key (e.g., `"k2"`) is introduced into the client keyring before operational issuance.
   - The runtime supports multiple valid keys simultaneously during transition windows.
   - If `key_id` in token is not present in the keyring, evaluation fails closed to `INVALID_SIGNATURE` with diagnostic `"Unknown signing key ID"`.
3. **Zero Private Key Invariant:** Client edge distributions MUST NEVER contain or reference private signing keys.

---

## 5. State Machine & Exact Boundary Rules

Evaluation against current time $T_{\text{eval}}$ (in UTC) follows exact deterministic boundaries:

| Condition | State | `is_active` | Diagnostic / Meaning |
|---|---|---|---|
| $T_{\text{eval}} < \text{not\_before}$ | `NOT_YET_VALID` | `false` | License period has not yet begun. |
| $\text{not\_before} \le T_{\text{eval}} \le \text{expires\_at}$ | `ACTIVE` | `true` | License is within primary active commercial validity. |
| $\text{expires\_at} < T_{\text{eval}} \le \text{grace\_until}$ | `GRACE` | `true` | License has expired but is within administrative grace window. |
| $T_{\text{eval}} > \text{grace\_until}$ | `EXPIRED` | `false` | License and grace period have both terminated. |
| Signature invalid / Key unknown | `INVALID_SIGNATURE` | `false` | Cryptographic verification failed. |
| Version $\neq$ `"v1.0"` | `UNSUPPORTED_VERSION` | `false` | Incompatible schema version. |
| JSON / Chronology error | `MALFORMED` | `false` | Structural or timestamp chronology violation. |
| Bound `installation_id` mismatch | `INSTALLATION_MISMATCH` | `false` | License bound to a different machine hash. |

> **Security Rule:** All enforcement decisions MUST evaluate actual datetime comparisons ($T_{\text{eval}}$ vs ISO timestamps). Derived integer counts (`days_remaining`, `grace_days_remaining`) are presentation helpers and MUST NOT govern security boundaries.

---

## 6. Entitlement Evaluation Semantics

1. **Known Capabilities:**
   - `reconciliation`: Permission to run deterministic reconciliation on new cases.
   - `offline_export`: Permission to export encrypted/unencrypted practitioner workpaper bundles.
   - `reviewer_workflow`: Permission to transition cases to reviewer review / sign-off stage.
   - `multi_office`: Permission to configure multi-office workspace partitions.
2. **Fail-Closed Capability Grant:** An entitlement is granted if and only if `is_active == true` AND the capability identifier is explicitly present in `payload.entitlements`. Unknown entitlement strings NEVER grant capabilities.
