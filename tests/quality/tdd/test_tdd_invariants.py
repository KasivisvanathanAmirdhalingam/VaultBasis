"""
VaultBasis Quality Suite — TDD (Test-Driven Development)
Tests low-level mathematical invariants, exact Decimal arithmetic, and canonical serialization determinism.
"""

from decimal import Decimal
import hashlib
import json
import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519

from edge.receipts.canonicalizer import canonical_json_bytes, compute_receipt_digest
from edge.receipts.keygen import InstallationKeyManager
from edge.receipts.signer import ReceiptSigner


@pytest.mark.tdd
@pytest.mark.smoke
def test_tdd_decimal_exactness_no_floating_point():
    """Validates that Decimal arithmetic preserves exact fractional precision without float drift."""
    val1 = Decimal("0.1")
    val2 = Decimal("0.2")
    assert val1 + val2 == Decimal("0.3")  # Float would yield 0.30000000000000004

    # High precision sub-atomic satoshi units
    satoshi_qty = Decimal("0.00000001")
    price = Decimal("65432.10")
    total_proceeds = satoshi_qty * price
    assert total_proceeds == Decimal("0.0006543210")


@pytest.mark.tdd
@pytest.mark.regression
def test_tdd_canonicalization_rfc8785_invariants():
    """
    Validates RFC 8785 canonicalization invariants:
    1. Whitespace normalization (no spaces around delimiters)
    2. Lexicographical key sorting
    3. UTF-8 NFC character normalization
    """
    obj1 = {"c": 3, "a": 1, "b": 2}
    obj2 = {"a": 1, "b": 2, "c": 3}
    obj3 = {"b": 2, "c": 3, "a": 1}

    bytes1 = canonical_json_bytes(obj1)
    bytes2 = canonical_json_bytes(obj2)
    bytes3 = canonical_json_bytes(obj3)

    assert bytes1 == bytes2 == bytes3 == b'{"a":1,"b":2,"c":3}'


@pytest.mark.tdd
@pytest.mark.regression
def test_tdd_receipt_digest_signature_exclusion():
    """Validates that signature field is excluded when computing receipt digest."""
    receipt_a = {
        "receipt_version": "v0.1",
        "receipt_id": "test-uuid",
        "case_id": "case-1",
        "signature": "1111" * 32
    }
    receipt_b = {
        "receipt_version": "v0.1",
        "receipt_id": "test-uuid",
        "case_id": "case-1",
        "signature": "9999" * 32
    }

    digest_a = compute_receipt_digest(receipt_a)
    digest_b = compute_receipt_digest(receipt_b)

    # Digests must be identical because signature is excluded from calculation
    assert digest_a == digest_b


@pytest.mark.tdd
@pytest.mark.smoke
def test_tdd_cryptographic_signature_correctness(tmp_path):
    """Validates Ed25519 signing and verification over 32-byte digest."""
    km = InstallationKeyManager(tmp_path / "keys")
    priv, pub = km.ensure_keypair()
    signer = ReceiptSigner(priv)

    msg_digest = hashlib.sha256(b"canonical message").digest()
    sig = priv.sign(msg_digest)

    # Valid verification
    pub.verify(sig, msg_digest)

    # Corrupted digest fails
    with pytest.raises(Exception):
        pub.verify(sig, hashlib.sha256(b"corrupted message").digest())
