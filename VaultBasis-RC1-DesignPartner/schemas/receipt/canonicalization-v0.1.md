# Evidence Contract v0.1 — Normative Canonicalization Specification

> **Artifact ID**: `schemas/receipt/canonicalization-v0.1.md`  
> **Status**: NORMATIVE / FROZEN  
> **Scope**: Evidence Contract v0.1 (MMP-1)  
> **Standards Reference**: RFC 8785 (JSON Canonicalization Scheme - JCS), UTF-8, ISO 8601 UTC  

---

## 1. Purpose

In VaultBasis, receipts must be portable and independently verifiable across machines, languages, and runtime environments. To guarantee that a cryptographic signature over receipt contents is deterministic and reproducible without ambiguity, this document specifies the normative byte-for-byte serialization algorithm.

**"Hash the JSON" is strictly prohibited.** All signing and verification operations must execute this canonicalization algorithm prior to computing the SHA-256 digest.

---

## 2. Canonicalization Rules

### 2.1 Character Encoding
- The canonical representation must be encoded exclusively in **UTF-8**.
- Byte Order Mark (BOM) is strictly prohibited.
- Unicode characters must be normalized using Unicode Normalization Form C (**NFC**).

### 2.2 Whitespace
- No indentation.
- No newlines or carriage returns (`\n`, `\r`) outside quoted string values.
- Key-value separator must be `:` (ASCII 0x3A) with no preceding or trailing whitespace.
- Item separator in objects and arrays must be `,` (ASCII 0x2C) with no preceding or trailing whitespace.

### 2.3 Object Key Ordering
- All object keys must be sorted lexicographically by their UTF-16 code units (as specified in RFC 8785 §3.2.3).
- For ASCII keys (which all receipt keys are), this corresponds to standard ASCII scalar value ascending sort (`a` < `b` < `c` ...).
- Key sorting applies recursively to all nested objects.

### 2.4 Array Serialization
- Array elements preserve their semantic order as defined by the assurance engine.
- Elements within an array are serialized recursively according to these canonical rules.

### 2.5 Numbers and Precision
- In accordance with PRD §15.1, financial numbers must not use IEEE 754 binary floating point.
- All monetary amounts, costs, proceeds, variances, and fractional quantities must be represented as **exact decimal strings** (e.g., `"18400.00"`, `"0.00450000"`), never raw JSON floats (`18400.0` is invalid).
- Integer counters (if any) are encoded without leading zeros.

### 2.6 Timestamps
- All timestamps must be represented as strings in ISO 8601 extended format in UTC with explicit `Z` suffix.
- Format: `YYYY-MM-DDTHH:MM:SSZ` (or `YYYY-MM-DDTHH:MM:SS.sssZ` when millisecond precision is present).
- Local time offsets (e.g. `+02:00`, `-05:00`) are prohibited in the canonical receipt; timestamps must be converted to UTC prior to serialization.

### 2.7 Null Values and Missing Fields
- Required fields must always be present.
- If a nullable field has no value, it must be explicitly represented as `null`. Empty strings `""` or omitted keys are prohibited where `null` is expected.

---

## 3. Signing Digest Exclusion Rule

When computing the digest for signing or verifying an Outcome Receipt:
1. The `signature` field is **excluded** from the payload.
2. The remaining 24 fields of the receipt object are canonicalized into UTF-8 bytes.
3. The cryptographic digest is computed as:
   $$\text{Digest} = \text{SHA-256}(\text{CanonicalUTF8Bytes})$$
4. The Ed25519 signature is computed over this 32-byte binary digest.
5. The signature is hex-encoded (128 lowercase hex characters representing the 64-byte Ed25519 signature) and placed into the receipt's `"signature"` property.
