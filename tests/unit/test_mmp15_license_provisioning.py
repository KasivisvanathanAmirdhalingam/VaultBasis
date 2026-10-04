"""
Unit & Ceremony Tests for VaultBasis Commercial License Provisioning Service (MMP15-PROD-LIC-001).

Validates:
- Order mapping for Solo (10 cases / ESSENTIAL) and Practice (50 cases / PRACTICE)
- Enforcement that only ORDER_ELIGIBLE_FOR_PROVISIONING orders can be provisioned
- Monotonic revision field preservation in signed payloads
- Full cryptographic signature verification against edge/commercial/engine.py
- Ceremony audit log completeness (inbound digest, key ID, outbound digest, operator record)
- Fail-closed behavior on capacity tampering or invalid state
"""

import copy
import json
import os
import pytest
from datetime import datetime, timezone
from pathlib import Path

from edge.commercial.engine import evaluate_license_envelope
from edge.commercial.keys import COMMERCIAL_KEYRING
from edge.commercial.models import LicenseState, LicenseTier
from tools.issue_license import generate_commercial_keypair
from tools.provision_order_license import (
    execute_provisioning_ceremony,
    map_order_to_license_parameters,
)


@pytest.fixture
def mock_orders():
    from datetime import timedelta
    now_dt = datetime.now(timezone.utc) - timedelta(minutes=5)
    end_dt = now_dt + timedelta(days=365)
    now = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    end = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    solo_order = {
        "schemaVersion": "1.0",
        "orderId": "ORD-2026-A1B2C3D4",
        "providerSessionId": "sess_solo_123",
        "customerEmail": "solo_cpa@firm.com",
        "customerName": "Sarah Solo, CPA",
        "firmName": None,
        "planId": "SOLO",
        "priceAmountCents": 49900,
        "priceCurrency": "USD",
        "caseCapacity": 10,
        "termStart": now,
        "termEnd": end,
        "paymentState": "ORDER_ELIGIBLE_FOR_PROVISIONING",
        "provisioningState": "ELIGIBLE",
        "revision": 1,
    }

    practice_order = {
        "schemaVersion": "1.0",
        "orderId": "ORD-2026-E5F6A7B8",
        "providerSessionId": "sess_practice_456",
        "customerEmail": "managing_partner@taxpractice.com",
        "customerName": "David Practice, CPA",
        "firmName": "Practice & Associates LLP",
        "planId": "PRACTICE",
        "priceAmountCents": 149900,
        "priceCurrency": "USD",
        "caseCapacity": 50,
        "termStart": now,
        "termEnd": end,
        "paymentState": "ORDER_ELIGIBLE_FOR_PROVISIONING",
        "provisioningState": "ELIGIBLE",
        "revision": 1,
    }

    return {"solo": solo_order, "practice": practice_order}


@pytest.fixture
def test_keypair():
    priv_hex, pub_hex = generate_commercial_keypair()
    return priv_hex, pub_hex


def test_order_mapping_solo_and_practice(mock_orders):
    """Validates deterministic mapping of plan, capacity, and revision."""
    solo_params = map_order_to_license_parameters(mock_orders["solo"])
    assert solo_params["tier"] == LicenseTier.ESSENTIAL
    assert solo_params["max_cases"] == 10
    assert solo_params["revision"] == 1
    assert "Sarah Solo, CPA" in solo_params["customer_id"]

    practice_params = map_order_to_license_parameters(mock_orders["practice"])
    assert practice_params["tier"] == LicenseTier.PRACTICE
    assert practice_params["max_cases"] == 50
    assert practice_params["revision"] == 1
    assert "David Practice, CPA" in practice_params["customer_id"]


def test_ineligible_order_state_rejected(mock_orders):
    """Proves that orders not in ORDER_ELIGIBLE_FOR_PROVISIONING fail closed."""
    pending_order = copy.deepcopy(mock_orders["solo"])
    pending_order["paymentState"] = "CHECKOUT_CREATED"

    with pytest.raises(ValueError, match="not eligible for license provisioning"):
        map_order_to_license_parameters(pending_order)

    failed_order = copy.deepcopy(mock_orders["solo"])
    failed_order["paymentState"] = "PAYMENT_FAILED"

    with pytest.raises(ValueError, match="not eligible for license provisioning"):
        map_order_to_license_parameters(failed_order)


def test_tampered_capacity_rejected(mock_orders):
    """Proves that capacity tampering relative to the plan catalog fails closed."""
    tampered_solo = copy.deepcopy(mock_orders["solo"])
    tampered_solo["caseCapacity"] = 9999  # Tampered capacity

    with pytest.raises(ValueError, match="Order capacity mismatch"):
        map_order_to_license_parameters(tampered_solo)


def test_provisioning_ceremony_execution_and_verification(mock_orders, test_keypair):
    """Executes full signing ceremony and verifies resulting envelope against engine."""
    priv_hex, pub_hex = test_keypair
    order = mock_orders["practice"]

    # Temporarily register test public key in keyring for engine verification
    original_key = COMMERCIAL_KEYRING.get("k1")
    COMMERCIAL_KEYRING["k1"] = pub_hex

    try:
        envelope, audit = execute_provisioning_ceremony(
            order_record=order,
            signing_key_hex=priv_hex,
            key_id="k1",
            operator_id="test-operator",
        )

        # 1. Verify envelope structure
        assert envelope["key_id"] == "k1"
        assert "signature" in envelope
        assert envelope["payload"]["tier"] == "PRACTICE"
        assert envelope["payload"]["max_cases_per_installation"] == 50
        assert envelope["payload"]["revision"] == 1
        assert envelope["payload"]["license_id"].startswith("LIC-VB-PRACTICE-")

        # 2. Verify audit record
        assert audit["ceremonyType"] == "COMMERCIAL_LICENSE_ISSUANCE"
        assert audit["orderId"] == order["orderId"]
        assert audit["operatorId"] == "test-operator"
        assert len(audit["inboundOrderDigest"]) == 64
        assert len(audit["outboundLicenseDigest"]) == 64
        assert audit["status"] == "PROVISIONED"

        # 3. Verify acceptance by local edge verification engine
        eval_result = evaluate_license_envelope(envelope)
        assert eval_result.state == LicenseState.ACTIVE
        assert eval_result.tier == LicenseTier.PRACTICE
        assert eval_result.max_cases_per_installation == 50
    finally:
        if original_key:
            COMMERCIAL_KEYRING["k1"] = original_key


def test_monotonic_revision_support(mock_orders, test_keypair):
    """Validates that replacement license revisions are monotonically incremented."""
    priv_hex, pub_hex = test_keypair
    order_rev2 = copy.deepcopy(mock_orders["solo"])
    order_rev2["revision"] = 2

    envelope, audit = execute_provisioning_ceremony(
        order_record=order_rev2,
        signing_key_hex=priv_hex,
        key_id="k1",
        operator_id="ops-replacement",
    )

    assert envelope["payload"]["revision"] == 2
    assert audit["revision"] == 2
