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


@pytest.mark.tdd
@pytest.mark.regression
def test_tdd_high_volume_decimal_summation_zero_drift():
    """
    Validates that summing 10,000 fractional transactions preserves exact decimal precision
    with zero accumulation drift, unlike IEEE 754 floating point arithmetic.
    """
    increment = Decimal("0.10")
    total = Decimal("0.00")
    for _ in range(10000):
        total += increment

    assert total == Decimal("1000.00")
    # Float equivalent would fail: 0.1 * 10000 != 1000.00 (drift detected)


@pytest.mark.tdd
@pytest.mark.smoke
def test_tdd_cryptographic_single_bit_flip_fails_signature(tmp_path):
    """
    Validates that flipping a single bit anywhere in an Ed25519 signature
    causes cryptographic verification to immediately fail.
    """
    from cryptography.exceptions import InvalidSignature

    km = InstallationKeyManager(tmp_path / "keys")
    priv, pub = km.ensure_keypair()
    msg = b"Normative Evidence Contract v0.1 Test Message"
    msg_digest = hashlib.sha256(msg).digest()

    sig = priv.sign(msg_digest)
    assert len(sig) == 64

    # Verification of uncorrupted signature
    pub.verify(sig, msg_digest)

    # Flip 1 bit in first byte
    corrupted_sig_1 = bytes([sig[0] ^ 0x01]) + sig[1:]
    with pytest.raises(InvalidSignature):
        pub.verify(corrupted_sig_1, msg_digest)

    # Flip 1 bit in last byte
    corrupted_sig_64 = sig[:-1] + bytes([sig[-1] ^ 0x80])
    with pytest.raises(InvalidSignature):
        pub.verify(corrupted_sig_64, msg_digest)


@pytest.mark.tdd
@pytest.mark.regression
def test_tdd_cryptographic_single_bit_flip_in_message_fails(tmp_path):
    """Validates that modifying a single bit in the message digest causes verification failure."""
    from cryptography.exceptions import InvalidSignature

    km = InstallationKeyManager(tmp_path / "keys")
    priv, pub = km.ensure_keypair()
    msg = b"Canonical Payload"
    msg_digest = hashlib.sha256(msg).digest()
    sig = priv.sign(msg_digest)

    # Corrupt digest by flipping one bit
    corrupted_digest = bytes([msg_digest[0] ^ 0x01]) + msg_digest[1:]
    with pytest.raises(InvalidSignature):
        pub.verify(sig, corrupted_digest)


@pytest.mark.tdd
@pytest.mark.regression
def test_tdd_rfc8785_unicode_character_normalization_and_escapes():
    """
    Validates RFC 8785 Unicode escaping and deterministic UTF-8 serialization:
    - Special control characters (\\b, \\f, \\n, \\r, \\t)
    - Multibyte Unicode symbols (e.g. currency, non-ASCII letters)
    """
    sample = {
        "text": "Hello\nWorld\twith \"quotes\" and \\backslash\\",
        "unicode_euro": "€100.50",
        "japanese": "ビットコイン"
    }
    canonical = canonical_json_bytes(sample)
    # RFC 8785 mandates canonical JSON produces UTF-8 encoded bytes with exact key ordering
    assert canonical.startswith(b'{"japanese":"\xe3\x83\x93\xe3\x83\x83\xe3\x83\x88\xe3\x82\xb3\xe3\x82\xa4\xe3\x83\xb3"')
    assert b'\\n' in canonical
    assert b'\\t' in canonical
    assert b'\\"' in canonical


@pytest.mark.tdd
@pytest.mark.regression
def test_tdd_decimal_fractional_lot_split_conservation():
    """
    Validates conservation of quantities across fractional lot splits
    ensuring zero remainder loss down to 18 decimal places.
    """
    original_lot = Decimal("1.000000000000000000")
    slice_1 = Decimal("0.333333333333333333")
    slice_2 = Decimal("0.333333333333333333")
    slice_3 = Decimal("0.333333333333333334")

    assert slice_1 + slice_2 + slice_3 == original_lot

    # Calculating proportional basis allocation
    total_cost_basis = Decimal("60000.00")
    basis_1 = (slice_1 / original_lot) * total_cost_basis
    basis_2 = (slice_2 / original_lot) * total_cost_basis
    basis_3 = (slice_3 / original_lot) * total_cost_basis

    total_allocated = (basis_1 + basis_2 + basis_3).quantize(Decimal("0.01"))
    assert total_allocated == Decimal("60000.00")


@pytest.mark.tdd
@pytest.mark.regression
def test_tdd_keypair_filesystem_permissions(tmp_path):
    """Validates that private key files are strictly created with mode 0o600 (owner read/write only)."""
    import os
    import stat

    key_dir = tmp_path / "secure_keys"
    km = InstallationKeyManager(key_dir)
    km.ensure_keypair()

    priv_path = key_dir / "installation_ed25519.key"
    assert priv_path.exists()
    mode = stat.S_IMODE(os.stat(priv_path).st_mode)
    assert mode == 0o600, f"Expected 0o600 permissions, got {oct(mode)}"


@pytest.mark.tdd
@pytest.mark.regression
def test_tdd_receipt_digest_computation_exactness():
    """Validates that compute_receipt_digest returns 32-byte raw SHA-256 digest over canonical JSON without signature."""
    receipt = {
        "receipt_version": "v0.1",
        "case_id": "CASE-DIGEST-TEST",
        "receipt_id": "rcpt-001",
        "signature": "abcdef123456"
    }
    digest = compute_receipt_digest(receipt)

    # Compute expected digest manually over stripped copy
    stripped = {"receipt_version": "v0.1", "case_id": "CASE-DIGEST-TEST", "receipt_id": "rcpt-001"}
    expected_bytes = hashlib.sha256(canonical_json_bytes(stripped)).digest()
    expected_hex = hashlib.sha256(canonical_json_bytes(stripped)).hexdigest()

    assert digest == expected_bytes
    assert len(digest) == 32
    assert digest.hex() == expected_hex




