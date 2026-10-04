"""
Unit & Invariant Test Suite for MMP15-ENT-001 (Commercial License & Entitlement Engine).
Guarantees deterministic evaluation, cryptographic tamper detection, key isolation,
air-gap safety, and independence from receipt verification.
"""

import base64
import copy
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
from edge.commercial.keys import COMMERCIAL_LICENSE_VERIFICATION_PUBLIC_KEY_HEX
from edge.commercial.models import (
    LicenseEvaluationResult,
    LicensePayload,
    LicenseState,
    LicenseTier,
)
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
        not_before_dt=now,
    )
    envelope = sign_license_payload(payload, priv_hex)
    token_b64 = encode_token_base64(envelope)
    return {
        "priv_hex": priv_hex,
        "pub_hex": pub_hex,
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
        public_key_hex=f["pub_hex"],
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


@pytest.mark.parametrize("tier_name", ["TRIAL", "ESSENTIAL", "PRACTICE", "ENTERPRISE"])
def test_all_commercial_tiers_supported(commercial_keypair, tier_name):
    """Every defined commercial tier is valid and correctly recognized."""
    priv_hex, pub_hex = commercial_keypair
    now = datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc)
    payload = build_license_payload(
        customer_id="CUST-TIER-TEST",
        tier=tier_name,
        max_cases=50,
        not_before_dt=now,
    )
    envelope = sign_license_payload(payload, priv_hex)
    token = encode_token_base64(envelope)
    
    result = evaluate_license_token(token, public_key_hex=pub_hex, current_time=now + timedelta(days=1))
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
        public_key_hex=f["pub_hex"],
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
        public_key_hex=f["pub_hex"],
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
        public_key_hex=other_pub_hex,
        current_time=f["base_time"] + timedelta(days=1),
    )
    assert result.state == LicenseState.INVALID_SIGNATURE
    assert result.is_active is False


# ==============================================================================
# 3. TEMPORAL BOUNDARY & GRACE WINDOW TESTS
# ==============================================================================

def test_not_yet_valid_state(valid_license_fixture):
    """Current time before not_before yields NOT_YET_VALID."""
    f = valid_license_fixture
    before_time = f["base_time"] - timedelta(days=2)
    
    result = evaluate_license_token(
        token_str=f["token_b64"],
        public_key_hex=f["pub_hex"],
        current_time=before_time,
    )
    assert result.state == LicenseState.NOT_YET_VALID
    assert result.is_active is False


def test_grace_period_state(valid_license_fixture):
    """Expired after valid_days but within grace_days yields GRACE."""
    f = valid_license_fixture
    # Expired by 10 days, but 30-day grace has 20 days remaining
    grace_time = f["base_time"] + timedelta(days=375)
    
    result = evaluate_license_token(
        token_str=f["token_b64"],
        public_key_hex=f["pub_hex"],
        current_time=grace_time,
    )
    assert result.state == LicenseState.GRACE
    assert result.is_active is True
    assert result.grace_days_remaining == 20
    assert result.days_remaining == -10


def test_fully_expired_state(valid_license_fixture):
    """Past grace termination yields EXPIRED."""
    f = valid_license_fixture
    # 400 days past base_time (expires_at=365, grace_until=395)
    expired_time = f["base_time"] + timedelta(days=400)
    
    result = evaluate_license_token(
        token_str=f["token_b64"],
        public_key_hex=f["pub_hex"],
        current_time=expired_time,
    )
    assert result.state == LicenseState.EXPIRED
    assert result.is_active is False


# ==============================================================================
# 4. INSTALLATION BINDING TESTS
# ==============================================================================

def test_installation_binding_match(commercial_keypair):
    """Bound license evaluated on matching installation evaluates to ACTIVE."""
    priv_hex, pub_hex = commercial_keypair
    now = datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc)
    target_install_id = "inst-hash-789abc"
    
    payload = build_license_payload(
        customer_id="CUST-BOUND-TEST",
        tier="ENTERPRISE",
        max_cases=500,
        installation_id=target_install_id,
        not_before_dt=now,
    )
    envelope = sign_license_payload(payload, priv_hex)
    token = encode_token_base64(envelope)
    
    result = evaluate_license_token(
        token,
        public_key_hex=pub_hex,
        current_time=now + timedelta(days=1),
        current_installation_id=target_install_id,
    )
    assert result.state == LicenseState.ACTIVE
    assert result.installation_bound is True


def test_installation_binding_mismatch(commercial_keypair):
    """Bound license evaluated on different installation yields INSTALLATION_MISMATCH."""
    priv_hex, pub_hex = commercial_keypair
    now = datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc)
    
    payload = build_license_payload(
        customer_id="CUST-BOUND-TEST",
        tier="ENTERPRISE",
        max_cases=500,
        installation_id="inst-machine-A",
        not_before_dt=now,
    )
    envelope = sign_license_payload(payload, priv_hex)
    token = encode_token_base64(envelope)
    
    result = evaluate_license_token(
        token,
        public_key_hex=pub_hex,
        current_time=now + timedelta(days=1),
        current_installation_id="inst-machine-B",
    )
    assert result.state == LicenseState.INSTALLATION_MISMATCH
    assert result.is_active is False
    assert result.installation_bound is True


# ==============================================================================
# 5. SCHEMA, MALFORMED & UNKNOWN INPUT CONTROLS (FAIL-CLOSED)
# ==============================================================================

def test_unsupported_version_rejected(commercial_keypair):
    """License with unsupported version string yields UNSUPPORTED_VERSION."""
    priv_hex, pub_hex = commercial_keypair
    now = datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc)
    payload = build_license_payload(
        customer_id="CUST-VER-TEST",
        tier="PRACTICE",
        max_cases=100,
        not_before_dt=now,
    )
    payload["version"] = "v2.0"
    envelope = sign_license_payload(payload, priv_hex)
    
    result = evaluate_license_envelope(envelope, public_key_hex=pub_hex, current_time=now)
    assert result.state == LicenseState.UNSUPPORTED_VERSION
    assert result.is_active is False


@pytest.mark.parametrize("corrupt_token", [
    "",
    "   ",
    "not-base64-nor-json",
    "{}",
    '{"payload": "not a dict", "signature": "123"}',
    "e30=",  # base64 for "{}"
    "null",
])
def test_malformed_tokens_fail_closed(corrupt_token, commercial_keypair):
    """Malformed, garbage, or incomplete tokens fail closed to MALFORMED."""
    _, pub_hex = commercial_keypair
    result = evaluate_license_token(corrupt_token, public_key_hex=pub_hex)
    assert result.state == LicenseState.MALFORMED
    assert result.is_active is False


# ==============================================================================
# 6. SECURITY BOUNDARIES, KEY ISOLATION & AIR-GAP TESTS
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
        public_key_hex=f["pub_hex"],
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
    
    # Evaluating receipt verification should execute cleanly without requiring commercial license
    res = ReceiptVerifier.verify(valid_receipt)
    assert "contract_status" in res
    assert res["contract_status"] == "VALID"


# ==============================================================================
# 7. PROPERTY / FUZZ TESTING FOR TRUST BOUNDARY STABILITY
# ==============================================================================

def test_fuzz_malformed_token_inputs(commercial_keypair):
    """Fuzz testing: random byte mutations must fail closed without unhandled crashes."""
    _, pub_hex = commercial_keypair
    
    for _ in range(50):
        # Generate random garbage bytes
        random_len = random.randint(1, 256)
        garbage_bytes = os.urandom(random_len)
        
        # Test as raw string
        try:
            garbage_str = garbage_bytes.decode("latin1")
            result = evaluate_license_token(garbage_str, public_key_hex=pub_hex)
            assert result.state in (LicenseState.MALFORMED, LicenseState.INVALID_SIGNATURE)
            assert result.is_active is False
        except UnicodeDecodeError:
            pass
        
        # Test as base64 string
        b64_garbage = base64.b64encode(garbage_bytes).decode("ascii")
        result = evaluate_license_token(b64_garbage, public_key_hex=pub_hex)
        assert result.state in (LicenseState.MALFORMED, LicenseState.INVALID_SIGNATURE)
        assert result.is_active is False
