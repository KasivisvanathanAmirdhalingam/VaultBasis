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
    # PAYMENT_CONFIRMED alone must be rejected (must advance to ORDER_ELIGIBLE_FOR_PROVISIONING)
    confirmed_order = copy.deepcopy(mock_orders["solo"])
    confirmed_order["paymentState"] = "PAYMENT_CONFIRMED"

    with pytest.raises(ValueError, match="Expected: ORDER_ELIGIBLE_FOR_PROVISIONING"):
        map_order_to_license_parameters(confirmed_order)

    pending_order = copy.deepcopy(mock_orders["solo"])
    pending_order["paymentState"] = "CHECKOUT_CREATED"

    with pytest.raises(ValueError, match="Expected: ORDER_ELIGIBLE_FOR_PROVISIONING"):
        map_order_to_license_parameters(pending_order)

    failed_order = copy.deepcopy(mock_orders["solo"])
    failed_order["paymentState"] = "PAYMENT_FAILED"

    with pytest.raises(ValueError, match="Expected: ORDER_ELIGIBLE_FOR_PROVISIONING"):
        map_order_to_license_parameters(failed_order)


def test_tampered_capacity_rejected(mock_orders):
    """Proves that capacity tampering relative to the plan catalog fails closed."""
    tampered_solo = copy.deepcopy(mock_orders["solo"])
    tampered_solo["caseCapacity"] = 9999  # Tampered capacity

    with pytest.raises(ValueError, match="Order capacity mismatch"):
        map_order_to_license_parameters(tampered_solo)


def test_issuance_ledger_idempotency_and_conflict_rejection(mock_orders, test_keypair, tmp_path):
    """Proves that identical requests return existing signed artifact, while conflicting payloads fail closed."""
    from tools.provision_order_license import LicenseIssuanceLedger

    priv_hex, pub_hex = test_keypair
    ledger_path = tmp_path / "issuance_ledger.json"
    ledger = LicenseIssuanceLedger(ledger_path)

    order = mock_orders["solo"]

    # 1. First issuance
    env1, audit1 = execute_provisioning_ceremony(
        order_record=order,
        signing_key_hex=priv_hex,
        ledger=ledger,
    )
    assert audit1["isReplayed"] is False

    # Check ledger durability and fields
    with open(ledger_path, "r", encoding="utf-8") as f:
        stored_ledger = json.load(f)
    ent_id = order["orderId"]
    assert ent_id in stored_ledger
    record = stored_ledger[ent_id]
    assert record["entitlement_id"] == ent_id
    assert len(record["canonical_payload_hash"]) == 64
    assert record["license_id"].startswith("LIC-VB-ESSENTIAL-")
    assert record["license_revision"] == 1
    assert record["key_id"] == "k1"
    assert len(record["output_artifact_sha256"]) == 64
    assert "issuance_timestamp" in record
    assert "envelope" in record

    # 2. Second issuance with same order -> idempotent replay
    env2, audit2 = execute_provisioning_ceremony(
        order_record=order,
        signing_key_hex=priv_hex,
        ledger=ledger,
    )
    assert audit2["isReplayed"] is True
    assert env1["signature"] == env2["signature"]

    # 3. Third issuance with changed payload for same orderId -> conflict rejection
    conflicting_order = copy.deepcopy(order)
    conflicting_order["customerName"] = "Hacker Impersonator"

    with pytest.raises(ValueError, match="Conflict: Entitlement .* already provisioned with different payload hash"):
        execute_provisioning_ceremony(
            order_record=conflicting_order,
            signing_key_hex=priv_hex,
            ledger=ledger,
        )


def test_edge_monotonic_license_replacement_enforcement(test_keypair, tmp_path):
    """
    Proves Edge policy enforces frozen replacement invariants:
    1. current revision 2 + incoming revision 1 -> reject (monotonic violation)
    2. current revision 2 + incoming revision 2 -> reject (monotonic violation)
    3. current revision 2 + incoming revision 3 -> accept
    4. different lineage revision 3          -> reject (lineage mismatch)
    5. untrusted key revision 999            -> reject (invalid signature / untrusted)
    """
    from edge.commercial.policy import CommercialPolicyService
    from tools.issue_license import issue_commercial_license

    priv_hex, pub_hex = test_keypair
    policy_service = CommercialPolicyService(
        license_dir=tmp_path / "license_store",
        keyring_override={"k1": pub_hex},
    )

    # Base: Install Revision 2
    token_rev2 = issue_commercial_license(
        signing_key_hex=priv_hex,
        customer_id="Acme CPA Corp",
        tier="PRACTICE",
        max_cases=50,
        revision=2,
    )
    res_install_rev2 = policy_service.install_license_token(token_rev2)
    assert res_install_rev2.is_active is True
    assert res_install_rev2.revision == 2

    # Case 1: incoming revision 1 (Lower revision) -> REJECT
    token_rev1 = issue_commercial_license(
        signing_key_hex=priv_hex,
        customer_id="Acme CPA Corp",
        tier="PRACTICE",
        max_cases=50,
        revision=1,
    )
    res_install_rev1 = policy_service.install_license_token(token_rev1)
    assert res_install_rev1.is_active is False
    assert "Monotonic replacement violation" in res_install_rev1.diagnostic_reason
    assert policy_service.evaluate_current_license().revision == 2

    # Case 2: incoming revision 2 (Same revision) -> REJECT
    res_install_rev2_again = policy_service.install_license_token(token_rev2)
    assert res_install_rev2_again.is_active is False
    assert "Monotonic replacement violation" in res_install_rev2_again.diagnostic_reason
    assert policy_service.evaluate_current_license().revision == 2

    # Case 3: incoming revision 3 (Higher revision, same lineage) -> ACCEPT
    token_rev3 = issue_commercial_license(
        signing_key_hex=priv_hex,
        customer_id="Acme CPA Corp",
        tier="PRACTICE",
        max_cases=50,
        revision=3,
    )
    res_install_rev3 = policy_service.install_license_token(token_rev3)
    assert res_install_rev3.is_active is True
    assert res_install_rev3.revision == 3
    assert policy_service.evaluate_current_license().revision == 3

    # Case 4: different lineage revision 4 (Different customer) -> REJECT
    token_diff_lineage = issue_commercial_license(
        signing_key_hex=priv_hex,
        customer_id="Different Firm LLC",
        tier="PRACTICE",
        max_cases=50,
        revision=4,
    )
    res_diff_lineage = policy_service.install_license_token(token_diff_lineage)
    assert res_diff_lineage.is_active is False
    assert "License lineage mismatch" in res_diff_lineage.diagnostic_reason
    # Current active license remains Acme CPA Corp rev 3
    active_eval = policy_service.evaluate_current_license()
    assert active_eval.revision == 3
    assert active_eval.customer_id == "Acme CPA Corp"

    # Case 5: untrusted key revision 999 -> REJECT
    untrusted_priv, untrusted_pub = generate_commercial_keypair()
    token_untrusted = issue_commercial_license(
        signing_key_hex=untrusted_priv,
        customer_id="Acme CPA Corp",
        tier="PRACTICE",
        max_cases=50,
        revision=999,
        key_id="k999_untrusted",
    )
    res_untrusted = policy_service.install_license_token(token_untrusted)
    assert res_untrusted.is_active is False
    assert res_untrusted.state == LicenseState.INVALID_SIGNATURE
    assert policy_service.evaluate_current_license().revision == 3


def test_provisioning_ceremony_execution_and_verification(mock_orders, test_keypair):
    """Executes full signing ceremony and verifies resulting envelope and audit log."""
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
            signer_workstation_id="VAULTBASIS-AIRGAP-SIGNER-01",
        )

        # 1. Verify envelope structure
        assert envelope["key_id"] == "k1"
        assert "signature" in envelope
        assert envelope["payload"]["tier"] == "PRACTICE"
        assert envelope["payload"]["max_cases_per_installation"] == 50
        assert envelope["payload"]["revision"] == 1
        assert envelope["payload"]["license_id"].startswith("LIC-VB-PRACTICE-")

        # 2. Verify audit record compliance
        assert audit["ceremonyType"] == "COMMERCIAL_LICENSE_ISSUANCE"
        assert audit["orderId"] == order["orderId"]
        assert audit["operatorId"] == "test-operator"
        assert audit["signerWorkstationId"] == "VAULTBASIS-AIRGAP-SIGNER-01"
        assert audit["zeroNetworkVerified"] is True
        assert audit["privateKeyNonExportVerified"] is True
        assert len(audit["inboundOrderDigest"]) == 64
        assert len(audit["canonicalPayloadDigest"]) == 64
        assert len(audit["outboundLicenseDigest"]) == 64
        assert audit["status"] == "PROVISIONED"

        # 3. Verify acceptance by local edge verification engine
        eval_result = evaluate_license_envelope(envelope)
        assert eval_result.state == LicenseState.ACTIVE
        assert eval_result.tier == LicenseTier.PRACTICE
        assert eval_result.max_cases_per_installation == 50
        assert eval_result.revision == 1
    finally:
        if original_key:
            COMMERCIAL_KEYRING["k1"] = original_key

