"""
VaultBasis Edge — Normative Canonicalization Test Suite (RC2-L1.1 / RC2-L1.2)
Verifies VB-CJCS-0.1 against the 12 frozen normative test vectors (TC-CANON-01..12).
"""

import hashlib
import json
from pathlib import Path
import pytest

from edge.receipts.canonicalizer import canonical_json_bytes, compute_sha256_hex


def load_normative_vectors():
    fixture_path = Path(__file__).parent.parent / "fixtures" / "canonical_vectors_v0.1.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["vectors"]


@pytest.mark.parametrize("vector", load_normative_vectors(), ids=lambda v: v["id"])
def test_canonical_json_bytes_normative_vectors(vector):
    """
    RC2-L1.1 / RC2-L1.2:
    Ensures canonical_json_bytes produces byte-identical UTF-8 serialization
    and exact SHA-256 digests matching frozen normative test vectors.
    """
    input_obj = vector["input"]
    expected_json_str = vector["expected_canonical_json"]
    expected_bytes = expected_json_str.encode("utf-8")
    expected_sha256 = vector["expected_sha256"]

    # 1. Byte-identical UTF-8 test
    actual_bytes = canonical_json_bytes(input_obj)
    assert actual_bytes == expected_bytes, (
        f"Vector {vector['id']} ({vector['description']}) failed byte equality.\n"
        f"Expected: {expected_json_str}\n"
        f"Actual:   {actual_bytes.decode('utf-8')}"
    )

    # 2. SHA-256 digest match test
    actual_sha256 = compute_sha256_hex(actual_bytes)
    assert actual_sha256.lower() == expected_sha256.lower(), (
        f"Vector {vector['id']} SHA-256 mismatch.\n"
        f"Expected: {expected_sha256}\n"
        f"Actual:   {actual_sha256}"
    )
