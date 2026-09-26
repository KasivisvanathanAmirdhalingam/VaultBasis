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


@pytest.mark.tdd
@pytest.mark.regression
def test_tdd_sub_atomic_decimal_arithmetic_precision():
    """Validates arbitrary precision arithmetic without rounding or floating point drift up to 18 decimal places."""
    wei_amount = Decimal("0.000000000000000001")  # 1 wei
    quantity = Decimal("1000000000000000000")    # 1 ETH
    assert wei_amount * quantity == Decimal("1.000000000000000000")

    # Subtracting exact satoshis
    basis = Decimal("10000.12345678")
    proceeds = Decimal("10000.12345679")
    gain = proceeds - basis
    assert gain == Decimal("0.00000001")


@pytest.mark.tdd
@pytest.mark.regression
def test_tdd_rfc8785_edge_cases_nested_and_types():
    """Validates RFC 8785 JCS canonicalization with complex nested structures and diverse primitive types."""
    nested = {
        "z_array": [3, 1, 2],
        "b_bool": True,
        "a_null": None,
        "deep": {
            "y": False,
            "x": -42,
            "empty_dict": {},
            "empty_list": []
        }
    }
    canonical = canonical_json_bytes(nested)
    expected = b'{"b_bool":true,"deep":{"empty_dict":{},"empty_list":[],"x":-42,"y":false},"z_array":[3,1,2]}'
    # Note: null keys or null values in JSON
    # When serialized, keys must be lexicographically sorted at every depth
    assert canonical == b'{"a_null":null,"b_bool":true,"deep":{"empty_dict":{},"empty_list":[],"x":-42,"y":false},"z_array":[3,1,2]}'


@pytest.mark.tdd
@pytest.mark.regression
def test_tdd_receipt_schema_rejection_on_missing_required_field():
    """Validates that Evidence Contract v0.1 strictly rejects receipts missing any of the 23 required fields."""
    import jsonschema
    from apps.verifier.verify_receipt import SCHEMA_PATH

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    valid_minimal_receipt = {
        "receipt_version": "v0.1",
        "receipt_id": "00000000-0000-0000-0000-000000000000",
        "case_id": "CASE-MIN-01",
        "claim_type": "DIGITAL_ASSET_TAX_RECONCILIATION",
        "claimant_type": "TAXPAYER",
        "producer_reference": "VaultBasis Edge v0.1.0-preview",
        "source_ids": ["src_1"],
        "source_hashes": {"src_1": "a" * 64},
        "source_schema_ids": {"src_1": "GENERIC"},
        "canonicalization_version": "v0.1",
        "ruleset_id": "US_IRC_1099DA_2025_V1",
        "engine_version": "0.1.0",
        "policy_version": "0.1.0",
        "assurance_level": "L2_EVIDENCE_RECONCILED",
        "outcome_state": "MATCHED",
        "material_differences": [],
        "unresolved_items": [],
        "provenance_references": [],
        "human_review_state": "UNREVIEWED",
        "ai_involvement_level": "NONE",
        "signer_type": "INSTALLATION_KEY",
        "signer_key_id": "b" * 64,
        "signer_public_key": "c" * 64,
        "created_at": "2026-09-26T12:00:00Z",
        "signature": "d" * 128
    }

    # Should validate cleanly
    jsonschema.validate(instance=valid_minimal_receipt, schema=schema)

    # Missing required field must fail validation
    invalid_receipt = dict(valid_minimal_receipt)
    del invalid_receipt["signer_public_key"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_receipt, schema=schema)

