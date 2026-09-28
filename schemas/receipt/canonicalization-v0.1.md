# Evidence Contract v0.1 — Normative Canonicalization Specification (`VB-CJCS-0.1`)

> **Artifact ID**: `schemas/receipt/canonicalization-v0.1.md`  
> **Status**: NORMATIVE / FROZEN  
> **Scope**: Evidence Contract v0.1 (MMP-1 / RC2 Baseline)  
> **Specification Name**: **VaultBasis Canonical JSON v0.1 (`VB-CJCS-0.1`)**  
> **Normative Test Suite**: `tests/fixtures/canonical_vectors_v0.1.json` (`TC-CANON-01` through `TC-CANON-12`)  

---

## 1. Normative Compatibility Rule

> **The Core Interoperability Standard:**  
> For every supported canonical payload, independently implemented canonicalizers **MUST** produce byte-identical UTF-8 output and identical SHA-256 digests. The normative test vector corpus (`TC-CANON-01..12`), rather than implementation-language defaults, defines compatibility.

"Hash the JSON" without canonical serialization is strictly prohibited. All signing and verification operations must execute this canonicalization algorithm prior to computing cryptographic digests.

---

## 2. Canonical Serialization Rules

### 2.1 Character Encoding
- Encoding must be strictly **UTF-8**.
- Byte Order Mark (BOM) is strictly prohibited.
- Strings are encoded as standard UTF-8 bytes without character transformation.

### 2.2 Whitespace & Delimiters
- No indentation.
- No newlines or carriage returns (`\n`, `\r`) outside quoted string literals.
- Object key-value separator must be `:` (ASCII 0x3A) with zero preceding or trailing whitespace.
- Object/array item separator must be `,` (ASCII 0x2C) with zero preceding or trailing whitespace.

### 2.3 Object Key Ordering
- All object keys must be sorted lexicographically by their Unicode scalar value code points (`a` < `b` < `c` ...).
- Key sorting applies recursively to all nested dictionaries.

### 2.4 Array Serialization
- Array elements preserve their exact semantic sequence as emitted by the evaluation engine.
- Child elements within an array are serialized recursively according to these canonical rules.

### 2.5 Numbers & Financial Quantities
- Native IEEE 754 binary floating-point numbers (`float`) are strictly prohibited in financial fields to prevent precision drift.
- All monetary amounts, costs, proceeds, variances, and fractional quantities must be represented as **canonical decimal strings** (e.g., `"1842.17"`, `"0.500000000000000000"`, `"0.00"`).
- Integers (e.g., counters, row indices) are encoded as unquoted base-10 digits without leading zeros.

### 2.6 Escaping & Special Characters
- Standard JSON string escape sequences (`\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`, `\t`) follow RFC 8259.
- Forward slash `/` does not require escaping unless necessary.

### 2.7 Null Values & Omitted Fields
- If a nullable field has no value, it must be explicitly represented as `null`.
- Empty strings `""` or omitted keys are prohibited where `null` is the semantic representation.

---

## 3. Cryptographic Signing Envelope Rule

When generating or verifying an Outcome Receipt:
1. The `signature` field is **excluded** from the envelope.
2. The remaining 24 fields of the receipt dictionary are serialized into UTF-8 bytes via `VB-CJCS-0.1`.
3. The cryptographic payload digest is computed as:
   $$\text{Digest} = \text{SHA-256}(\text{CanonicalUTF8Bytes})$$
4. The Ed25519 signature is computed over this 32-byte binary digest.
5. The signature is encoded as 128 lowercase hex characters and injected into the `"signature"` field.

---

## 4. Normative Test Vectors

All conforming implementations (Python CLI, browser WebCrypto, Node.js) are verified against:

| Vector ID | Target Semantic | Frozen SHA-256 Digest |
| :--- | :--- | :--- |
| `TC-CANON-01` | Flat object ASCII keys lexicographical ordering | `ebba85cfdc0a724b6cc327ecc545faeb38b9fe02eca603b430eb872f5cf75370` |
| `TC-CANON-02` | Nested dictionary recursive key ordering | `768e5d553e3a1e80d8507ab5804808197cc391b2cf9279d98e9216af4b1d348f` |
| `TC-CANON-03` | Array sequence preservation with child objects | `b0f905d8de82c1a6dcb5b3bb663e156c31e0a8bab107d665a34cf435cc26f8a3` |
| `TC-CANON-04` | Decimal string quantities and monetary values | `b8281863d68708af45fa356242f83384d11976bc0837ad80ae903bdff55997c3` |
| `TC-CANON-05` | Booleans, integers, zero, and null value handling | `5adf47651c2c347c851491004ae4e81b302b1adfef23c00b1ac4d97b4008b7db` |
| `TC-CANON-06` | Escaped control characters, quotes, and slashes | `1cdbfb8ab1acc30e17f99323ba6c39e571645b5f7f8b152ef829126c2d08b7ba` |
| `TC-CANON-07` | Empty objects, empty arrays, and empty strings | `2a8781af9ac37e30b45f58e83894528acb1472c33bdf4c2ef0d6b6d86e4f190f` |
| `TC-CANON-08` | Unicode accented characters in keys and values | `d2365099518d86c5812430f2248c083692ed17b07e5829efff9acc5bc1c8ca71` |
| `TC-CANON-09` | Supplementary Plane Unicode (Emojis & Symbols) | `264db028d37fcda954b89bde497e41c0df1582d2de6f0baf8042e2ad18e23ab4` |
| `TC-CANON-10` | ISO 8601 UTC timestamp format | `3afabd2f24276654f0a1a946173f3905b00f4a619cfd644f276465d6cde799d3` |
| `TC-CANON-11` | Null values in array items versus omitted keys | `885bdd923293742c865bb6394320693a7c141dbe5889d7f0681c9699d88211ad` |
| `TC-CANON-12` | Full 24-Field Evidence Contract v0.1 Payload | `3911af4efacaf9adf1c4098dfc6899bde75a8fb1055f055fbdbbd4f54ad49fed` |
