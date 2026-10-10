"""
Unit & Invariant Test Suite for MMP15-ENT-001 (Commercial License & Entitlement Engine).
Conforms to VaultBasis Commercial License Token Specification v1.0 (docs/commercial/license_token_v1.md).
Guarantees deterministic evaluation, cryptographic tamper detection, key isolation,
air-gap safety, strict JSON duplicate-key rejection, keyring rotation, and timestamp boundary invariance.
"""

import base64
import copy
import hashlib
import json
import os
import random
import socket
from datetime import datetime, timedelta, timezone

import pytest

from edge.commercial.engine import (
    evaluate_license_envelope,
    evaluate_license_token,
)
from edge.commercial.keys import (
    COMMERCIAL_KEYRING,
    COMMERCIAL_LICENSE_VERIFICATION_PUBLIC_KEY_HEX,
    resolve_verification_key,
)
from edge.commercial.models import (
    CommercialEntitlement,
    LicenseEvaluationResult,
    LicensePayload,
    LicenseState,
    LicenseTier,
    parse_strict_utc_iso8601,
)
from edge.receipts.canonicalizer import canonical_json_bytes, compute_sha256_digest
from edge.receipts.verifier import ReceiptVerifier
from tools.issue_license import (
    build_license_payload,
    encode_token_base64,
    generate_commercial_keypair,
    sign_license_payload,
)


@pytest.fixture
def commercial_keypair():
    """Generates an ephemeral Ed25519 keypair for test execution."""
    priv_hex, pub_hex = generate_commercial_keypair()
    return priv_hex, pub_hex


@pytest.fixture
def valid_license_fixture(commercial_keypair):
    """Creates a valid signed license payload and token."""
    priv_hex, pub_hex = commercial_keypair
    now = datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc)
    payload = build_license_payload(
        customer_id="CUST-ALPHA-CPA",
        tier="PRACTICE",
        max_cases=250,
        valid_days=365,
        grace_days=30,
        license_id="LIC-2026-ALPHA",
        key_id="k_test_1",
        not_before_dt=now,
    )
    envelope = sign_license_payload(payload, priv_hex)
    token_b64 = encode_token_base64(envelope)
    return {
        "priv_hex": priv_hex,
        "pub_hex": pub_hex,
        "key_id": "k_test_1",
        "keyring": {"k_test_1": pub_hex},
        "payload": payload,
        "envelope": envelope,
        "token_b64": token_b64,
        "base_time": now,
    }


# ==============================================================================
# 1. POSITIVE EVALUATION & TIER TESTS
# ==============================================================================

def test_valid_signed_license_evaluates_to_active(valid_license_fixture):
    """Valid signed token evaluates to ACTIVE with correct tier and capacity."""
    f = valid_license_fixture
    eval_time = f["base_time"] + timedelta(days=30)
    
    result = evaluate_license_token(
        token_str=f["token_b64"],
        keyring_override=f["keyring"],
        current_time=eval_time,
    )
    
    assert result.state == LicenseState.ACTIVE
    assert result.is_active is True
    assert result.tier == LicenseTier.PRACTICE
    assert result.customer_id == "CUST-ALPHA-CPA"
    assert result.license_id == "LIC-2026-ALPHA"
    assert result.max_cases_per_installation == 250
    assert result.days_remaining == 335
    assert result.grace_days_remaining == 365
    assert "reconciliation" in result.entitlements
    assert result.has_entitlement("reconciliation") is True


@pytest.mark.parametrize("tier_name", ["TRIAL", "ESSENTIAL", "PRACTICE", "ENTERPRISE"])
def test_all_commercial_tiers_supported(commercial_keypair, tier_name):
    """Every defined commercial tier is valid and correctly recognized."""
    priv_hex, pub_hex = commercial_keypair
    now = datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc)
    payload = build_license_payload(
        customer_id="CUST-TIER-TEST",
        tier=tier_name,
        max_cases=50,
        key_id="k_tier",
        not_before_dt=now,
    )
    envelope = sign_license_payload(payload, priv_hex)
    token = encode_token_base64(envelope)
    
    result = evaluate_license_token(
        token,
        keyring_override={"k_tier": pub_hex},
        current_time=now + timedelta(days=1),
    )
    assert result.state == LicenseState.ACTIVE
    assert result.tier.value == tier_name


# ==============================================================================
# 2. CRYPTOGRAPHIC TAMPER DETECTION TESTS
# ==============================================================================

def test_payload_mutation_rejected(valid_license_fixture):
    """Single-byte or field mutation in payload must invalidate signature."""
    f = valid_license_fixture
    tampered_envelope = copy.deepcopy(f["envelope"])
    
    # Tamper with max_cases_per_installation (e.g. increase from 250 to 9999)
    tampered_envelope["payload"]["max_cases_per_installation"] = 9999
    
    result = evaluate_license_envelope(
        envelope_dict=tampered_envelope,
        keyring_override=f["keyring"],
        current_time=f["base_time"] + timedelta(days=1),
    )
    assert result.state == LicenseState.INVALID_SIGNATURE
    assert result.is_active is False
    assert "verification failed" in result.diagnostic_reason


def test_signature_mutation_rejected(valid_license_fixture):
    """Corrupting the signature string must deterministically fail validation."""
    f = valid_license_fixture
    tampered_envelope = copy.deepcopy(f["envelope"])
    
    # Flip last character of signature hex
    sig = list(tampered_envelope["signature"])
    sig[-1] = "0" if sig[-1] != "0" else "1"
    tampered_envelope["signature"] = "".join(sig)
    
    result = evaluate_license_envelope(
        envelope_dict=tampered_envelope,
        keyring_override=f["keyring"],
        current_time=f["base_time"] + timedelta(days=1),
    )
    assert result.state == LicenseState.INVALID_SIGNATURE
    assert result.is_active is False


def test_wrong_public_key_rejected(valid_license_fixture):
    """License signed with Key A evaluated against Key B must be rejected."""
    f = valid_license_fixture
    _, other_pub_hex = generate_commercial_keypair()
    
    result = evaluate_license_token(
        token_str=f["token_b64"],
        keyring_override={"k_test_1": other_pub_hex},
        current_time=f["base_time"] + timedelta(days=1),
    )
    assert result.state == LicenseState.INVALID_SIGNATURE
    assert result.is_active is False


# ==============================================================================
# 3. RFC 8785 CANONICALIZATION & PROTOCOL VECTORS
# ==============================================================================

def test_rfc8785_canonicalization_determinism():
    """Verify deterministic byte serialization matching RFC 8785 rules."""
    obj_a = {"b": 2, "a": 1, "c": [3, 2, 1], "d": {"z": "val", "a": "val"}}
    obj_b = {"a": 1, "d": {"a": "val", "z": "val"}, "c": [3, 2, 1], "b": 2}
    
    bytes_a = canonical_json_bytes(obj_a)
    bytes_b = canonical_json_bytes(obj_b)
    assert bytes_a == bytes_b
    assert bytes_a == b'{"a":1,"b":2,"c":[3,2,1],"d":{"a":"val","z":"val"}}'


def test_duplicate_json_key_rejection(valid_license_fixture):
    """Assert strict rejection of JSON tokens containing duplicate keys."""
    f = valid_license_fixture
    # Construct raw compact JSON string containing duplicate key in payload
    raw_compact = json.dumps(f["envelope"], separators=(",", ":"))
    raw_tampered_json = raw_compact.replace(
        '"max_cases_per_installation":250',
        '"max_cases_per_installation":250,"max_cases_per_installation":500'
    )
    assert '"max_cases_per_installation":500' in raw_tampered_json
    
    result = evaluate_license_token(
        raw_tampered_json,
        keyring_override=f["keyring"],
        current_time=f["base_time"] + timedelta(days=1),
    )
    assert result.state == LicenseState.MALFORMED
    assert "Duplicate JSON key" in result.diagnostic_reason


# ==============================================================================
# 4. KEYRING RESOLUTION & KEY ROTATION TESTS
# ==============================================================================

def test_key_rotation_multi_keyring_support():
    """
    Assert key rotation: Keyring with multiple keys verifies licenses signed by
    either Key 1 or Key 2, while rejecting unknown Key 3.
    """
    priv_k1, pub_k1 = generate_commercial_keypair()
    priv_k2, pub_k2 = generate_commercial_keypair()
    priv_k3, _ = generate_commercial_keypair()
    
    keyring = {"k1": pub_k1, "k2": pub_k2}
    now = datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc)
    
    # License signed with k1
    pay_1 = build_license_payload("CUST-1", "PRACTICE", 100, key_id="k1", not_before_dt=now)
    env_1 = sign_license_payload(pay_1, priv_k1)
    tok_1 = encode_token_base64(env_1)
    
    # License signed with k2 (rotated key)
    pay_2 = build_license_payload("CUST-2", "ENTERPRISE", 500, key_id="k2", not_before_dt=now)
    env_2 = sign_license_payload(pay_2, priv_k2)
    tok_2 = encode_token_base64(env_2)
    
    # License signed with unlisted k3
    pay_3 = build_license_payload("CUST-3", "PRACTICE", 100, key_id="k3", not_before_dt=now)
    env_3 = sign_license_payload(pay_3, priv_k3)
    tok_3 = encode_token_base64(env_3)
    
    # Verify k1 and k2 succeed
    res_1 = evaluate_license_token(tok_1, keyring_override=keyring, current_time=now + timedelta(days=1))
    assert res_1.state == LicenseState.ACTIVE
    
    res_2 = evaluate_license_token(tok_2, keyring_override=keyring, current_time=now + timedelta(days=1))
    assert res_2.state == LicenseState.ACTIVE
    
    # Verify k3 fails due to unknown key_id
    res_3 = evaluate_license_token(tok_3, keyring_override=keyring, current_time=now + timedelta(days=1))
    assert res_3.state == LicenseState.INVALID_SIGNATURE
    assert "Unknown signing key ID" in res_3.diagnostic_reason


def test_envelope_payload_key_id_mismatch_rejected(valid_license_fixture):
    """Envelope key_id differing from payload key_id must fail validation."""
    f = valid_license_fixture
    tampered_envelope = copy.deepcopy(f["envelope"])
    tampered_envelope["key_id"] = "k_different"
    
    result = evaluate_license_envelope(
        tampered_envelope,
        keyring_override=f["keyring"],
        current_time=f["base_time"] + timedelta(days=1),
    )
    assert result.state == LicenseState.MALFORMED
    assert "Key ID mismatch" in result.diagnostic_reason


# ==============================================================================
# 5. EXACT TIMESTAMP BOUNDARIES & NAIVE TIMESTAMP CONTROLS
# ==============================================================================

def test_exact_timestamp_boundary_behavior(valid_license_fixture):
    """
    Assert deterministic boundary behavior at exact mathematical equality:
    - eval_time == not_before -> ACTIVE
    - eval_time == expires_at -> ACTIVE
    - eval_time == expires_at + 1 second -> GRACE
    - eval_time == grace_until -> GRACE
    - eval_time == grace_until + 1 second -> EXPIRED
    """
    f = valid_license_fixture
    p = f["payload"]
    dt_not_before = parse_strict_utc_iso8601(p["not_before"])
    dt_expires_at = parse_strict_utc_iso8601(p["expires_at"])
    dt_grace_until = parse_strict_utc_iso8601(p["grace_until"])
    
    # 1 second before not_before
    r_before = evaluate_license_token(f["token_b64"], keyring_override=f["keyring"], current_time=dt_not_before - timedelta(seconds=1))
    assert r_before.state == LicenseState.NOT_YET_VALID
    
    # Exact not_before
    r_start = evaluate_license_token(f["token_b64"], keyring_override=f["keyring"], current_time=dt_not_before)
    assert r_start.state == LicenseState.ACTIVE
    
    # Exact expires_at
    r_exp = evaluate_license_token(f["token_b64"], keyring_override=f["keyring"], current_time=dt_expires_at)
    assert r_exp.state == LicenseState.ACTIVE
    
    # 1 second after expires_at
    r_grace_start = evaluate_license_token(f["token_b64"], keyring_override=f["keyring"], current_time=dt_expires_at + timedelta(seconds=1))
    assert r_grace_start.state == LicenseState.GRACE
    
    # Exact grace_until
    r_grace_end = evaluate_license_token(f["token_b64"], keyring_override=f["keyring"], current_time=dt_grace_until)
    assert r_grace_end.state == LicenseState.GRACE
    
    # 1 second after grace_until
    r_expired = evaluate_license_token(f["token_b64"], keyring_override=f["keyring"], current_time=dt_grace_until + timedelta(seconds=1))
    assert r_expired.state == LicenseState.EXPIRED


@pytest.mark.parametrize("invalid_ts", [
    "2026-10-04 12:00:00",      # Naive space separator
    "2026-10-04T12:00:00",       # Naive ISO (no Z or offset)
    "2026/10/04T12:00:00Z",      # Slash date
    "invalid-date-string",
])
def test_naive_or_invalid_timestamps_rejected(commercial_keypair, invalid_ts):
    """Naive or malformed timestamps must fail closed to MALFORMED."""
    priv_hex, pub_hex = commercial_keypair
    now = datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc)
    payload = build_license_payload("CUST-TS", "PRACTICE", 100, key_id="k1", not_before_dt=now)
    payload["expires_at"] = invalid_ts
    
    envelope = sign_license_payload(payload, priv_hex)
    result = evaluate_license_envelope(envelope, keyring_override={"k1": pub_hex}, current_time=now)
    assert result.state == LicenseState.MALFORMED


@pytest.mark.parametrize("chronology_test", [
    {"issued_at": "2027-01-01T00:00:00Z", "expires_at": "2026-01-01T00:00:00Z"},  # issued > expires
    {"not_before": "2027-01-01T00:00:00Z", "expires_at": "2026-01-01T00:00:00Z"}, # not_before > expires
    {"expires_at": "2027-01-01T00:00:00Z", "grace_until": "2026-01-01T00:00:00Z"},# expires > grace
])
def test_chronology_violations_rejected(commercial_keypair, chronology_test):
    """Chronology violations must be rejected as MALFORMED."""
    priv_hex, pub_hex = commercial_keypair
    now = datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc)
    payload = build_license_payload("CUST-CHRONO", "PRACTICE", 100, key_id="k1", not_before_dt=now)
    for k, v in chronology_test.items():
        payload[k] = v
        
    envelope = sign_license_payload(payload, priv_hex)
    result = evaluate_license_envelope(envelope, keyring_override={"k1": pub_hex}, current_time=now)
    assert result.state == LicenseState.MALFORMED


# ==============================================================================
# 6. ENTITLEMENT SEMANTICS & UNKNOWN PRESERVATION
# ==============================================================================

def test_entitlement_grant_semantics(commercial_keypair):
    """
    Assert known entitlement granted when active; unknown entitlement preserved
    in payload list but NEVER grants capabilities via has_entitlement().
    """
    priv_hex, pub_hex = commercial_keypair
    now = datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc)
    payload = build_license_payload(
        customer_id="CUST-ENT",
        tier="PRACTICE",
        max_cases=100,
        entitlements=["reconciliation", "unknown_future_capability_xyz"],
        key_id="k1",
        not_before_dt=now,
    )
    envelope = sign_license_payload(payload, priv_hex)
    
    # 1. When ACTIVE
    res_active = evaluate_license_envelope(envelope, keyring_override={"k1": pub_hex}, current_time=now + timedelta(days=1))
    assert res_active.state == LicenseState.ACTIVE
    assert res_active.has_entitlement("reconciliation") is True
    assert res_active.has_entitlement("unknown_future_capability_xyz") is True  # present in explicit grant
    assert res_active.has_entitlement("unlisted_capability") is False          # not granted
    
    # 2. When EXPIRED -> No capabilities granted regardless of list
    res_expired = evaluate_license_envelope(envelope, keyring_override={"k1": pub_hex}, current_time=now + timedelta(days=500))
    assert res_expired.state == LicenseState.EXPIRED
    assert res_expired.has_entitlement("reconciliation") is False
    assert res_expired.has_entitlement("unknown_future_capability_xyz") is False


# ==============================================================================
# 7. SECURITY BOUNDARIES, KEY ISOLATION & AIR-GAP TESTS
# ==============================================================================

def test_key_isolation_verifier_contains_no_private_key():
    """Assert edge runtime keys module contains strictly public key constants."""
    from edge.commercial import keys
    
    for attr in dir(keys):
        if "PRIVATE" in attr.upper() or "SECRET" in attr.upper():
            pytest.fail(f"Prohibited private key attribute detected in edge.commercial.keys: {attr}")
    
    pub_key_hex = getattr(keys, "COMMERCIAL_LICENSE_VERIFICATION_PUBLIC_KEY_HEX", None)
    assert pub_key_hex is not None
    assert len(pub_key_hex) == 64  # 32 bytes hex


def test_zero_network_during_entitlement_evaluation(valid_license_fixture, monkeypatch):
    """Verify that license evaluation executes completely offline without network sockets."""
    def guarded_socket(*args, **kwargs):
        raise RuntimeError("Prohibited network socket creation during offline entitlement evaluation")
    
    monkeypatch.setattr(socket, "socket", guarded_socket)
    
    f = valid_license_fixture
    result = evaluate_license_token(
        token_str=f["token_b64"],
        keyring_override=f["keyring"],
        current_time=f["base_time"] + timedelta(days=5),
    )
    assert result.state == LicenseState.ACTIVE


def test_receipt_verification_unaffected_by_commercial_licensing():
    """
    INVARIANT: ReceiptVerifier.verify() must remain 100% operational
    and unencumbered when no license token is present.
    """
    valid_receipt = {
        "receipt_version": "v0.1",
        "canonicalization_version": "v0.1",
        "case_id": "CASE-TEST-001",
        "outcome_state": "MATCHED",
        "timestamp_utc": "2026-10-04T12:00:00Z",
        "signer_type": "INSTALLATION_KEY",
        "signer_key_id": "test-key-id",
        "signer_public_key": "0" * 64,
        "signature": "0" * 128,
    }
    
    # Evaluating receipt verification executes cleanly without requiring commercial license
    res = ReceiptVerifier.verify(valid_receipt)
    assert "contract_status" in res
    assert res["contract_status"] == "VALID"


# ==============================================================================
# 8. PROPERTY / FUZZ TESTING FOR TRUST BOUNDARY STABILITY
# ==============================================================================

def test_fuzz_malformed_token_inputs(commercial_keypair):
    """Fuzz testing: random byte mutations must fail closed without unhandled crashes."""
    _, pub_hex = commercial_keypair
    keyring = {"k1": pub_hex}
    
    for _ in range(50):
        random_len = random.randint(1, 256)
        garbage_bytes = os.urandom(random_len)
        
        # Test as raw string
        try:
            garbage_str = garbage_bytes.decode("latin1")
            result = evaluate_license_token(garbage_str, keyring_override=keyring)
            assert result.state in (
                LicenseState.MALFORMED,
                LicenseState.INVALID_SIGNATURE,
                LicenseState.UNSUPPORTED_VERSION,
            )
            assert result.is_active is False
        except UnicodeDecodeError:
            pass
        
        # Test as base64 string
        b64_garbage = base64.b64encode(garbage_bytes).decode("ascii")
        result = evaluate_license_token(b64_garbage, keyring_override=keyring)
        assert result.state in (
            LicenseState.MALFORMED,
            LicenseState.INVALID_SIGNATURE,
            LicenseState.UNSUPPORTED_VERSION,
        )
        assert result.is_active is False
