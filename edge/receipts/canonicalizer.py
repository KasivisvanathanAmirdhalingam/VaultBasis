"""
VaultBasis Edge — Deterministic Canonicalization Engine
Conforms to Evidence Contract v0.1 (schemas/receipt/canonicalization-v0.1.md)
Based on RFC 8785 (JSON Canonicalization Scheme - JCS)
"""

import hashlib
import json
from decimal import Decimal
from typing import Any, Dict


def canonical_json_bytes(obj: Any) -> bytes:
    """
    Serializes a Python object into canonical UTF-8 bytes according to RFC 8785.
    
    Rules:
    - UTF-8 encoding without BOM
    - Object keys sorted by UTF-16 code unit values (Unicode code point order for ASCII)
    - Separators: comma ',' and colon ':' with no surrounding whitespace
    - Floats are prohibited in financial accounting; Decimal or integer strings must be used
    - No newlines or indentation
    """
    def _normalize(val: Any) -> Any:
        if isinstance(val, dict):
            # Recursively sort keys and normalize values
            return {k: _normalize(val[k]) for k in sorted(val.keys())}
        elif isinstance(val, (list, tuple)):
            return [_normalize(item) for item in val]
        elif isinstance(val, Decimal):
            # Format decimal without exponential notation
            return str(val)
        else:
            return val

    normalized = _normalize(obj)
    # Using sort_keys=True, separators=(',', ':'), ensure_ascii=False
    json_str = json.dumps(
        normalized,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False
    )
    return json_str.encode('utf-8')


def compute_sha256_digest(data: bytes) -> bytes:
    """Computes binary SHA-256 digest of input bytes."""
    return hashlib.sha256(data).digest()


def compute_sha256_hex(data: bytes) -> str:
    """Computes lowercase hexadecimal SHA-256 digest of input bytes."""
    return hashlib.sha256(data).hexdigest()


def compute_receipt_digest(receipt_dict: Dict[str, Any]) -> bytes:
    """
    Computes the 32-byte SHA-256 digest of the receipt for signing or verification.
    Per schemas/receipt/canonicalization-v0.1.md, the 'signature' field is excluded.
    """
    payload = {k: v for k, v in receipt_dict.items() if k != "signature"}
    raw_canonical_bytes = canonical_json_bytes(payload)
    return compute_sha256_digest(raw_canonical_bytes)
