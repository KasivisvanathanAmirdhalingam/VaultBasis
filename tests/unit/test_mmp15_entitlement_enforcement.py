"""
VaultBasis MMP-1.5 Entitlement Enforcement & Policy Test Suite
Tests MMP15-ENT-002:
1. Valid license -> Billable operation succeeds
2. No license -> Billable operation denied deterministically (ENTITLEMENT_REQUIRED, 402)
3. Expired license -> New billable work denied (LICENSE_EXPIRED, 403)
4. Grace license -> Grace policy enforced (LICENSE_GRACE_RESTRICTED, 403 for new cases)
5. Invalid signature -> Denied (LICENSE_INVALID, 403)
6. Wrong installation -> Denied (INSTALLATION_MISMATCH, 403)
7. Not yet valid license -> Denied (LICENSE_NOT_YET_VALID, 403)
8. Capacity available -> Case creation succeeds (201)
9. Capacity exceeded -> New case denied (CASE_CAPACITY_REACHED, 402)
10. Sample case -> Explicitly defined unmetered semantics (never counted against capacity)
11. Existing cases -> Remain accessible after expiry (200)
12. Evidence export -> Not commercial-metered; existing authorization still applies
13. Receipt verification -> Free and unmetered with no license (200)
14. Error model -> Stable machine-readable denial codes without internal crypto leakage
"""

import base64
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

from cryptography.hazmat.primitives.asymmetric import ed25519
from fastapi.testclient import TestClient

from edge.api.app import app
from edge.commercial.models import LicenseState, LicenseTier
from edge.commercial.policy import (
    CommercialDenialCode,
    CommercialOperation,
    CommercialPolicyService,
)
from edge.storage.sqlite_store import SQLiteStore
from schemas.canonical.case import CanonicalCase
from tools.issue_license import issue_commercial_license


# Deterministic test keys for commercial test harness
_TEST_PRIV_KEY = ed25519.Ed25519PrivateKey.generate()
_TEST_PRIV_HEX = _TEST_PRIV_KEY.private_bytes_raw().hex()
_TEST_PUB_HEX = _TEST_PRIV_KEY.public_key().public_bytes_raw().hex()
_TEST_KEY_ID = "KEY-COMMERCIAL-TEST-001"
_TEST_KEYRING = {_TEST_KEY_ID: _TEST_PUB_HEX}


def _make_test_token(
    tier: LicenseTier = LicenseTier.PRACTICE,
    max_cases: int = 5,
    issued_at_dt: Optional[datetime] = None,
    not_before_dt: Optional[datetime] = None,
    expires_at_dt: Optional[datetime] = None,
    grace_until_dt: Optional[datetime] = None,
    installation_id: Optional[str] = None,
    output_format: str = "base64",
    revision: int = 1,
) -> str:
    now = datetime.now(timezone.utc)
    issued_at = (issued_at_dt or now).strftime("%Y-%m-%dT%H:%M:%SZ")
    not_before = (not_before_dt or now).strftime("%Y-%m-%dT%H:%M:%SZ")
    expires_at = (expires_at_dt or (now + timedelta(days=365))).strftime("%Y-%m-%dT%H:%M:%SZ")
    grace_until = (grace_until_dt or (now + timedelta(days=395))).strftime("%Y-%m-%dT%H:%M:%SZ")

    return issue_commercial_license(
        signing_key_hex=_TEST_PRIV_HEX,
        customer_id="CUST-TEST-FIRM",
        tier=tier,
        max_cases=max_cases,
        license_id=f"LIC-TEST-{tier.value}",
        issued_at=issued_at,
        not_before=not_before,
        expires_at=expires_at,
        grace_until=grace_until,
        entitlements=["reconciliation", "offline_export"],
        installation_id=installation_id,
        key_id=_TEST_KEY_ID,
        output_format=output_format,
        revision=revision,
    )


@pytest.fixture
def clean_commercial_env(monkeypatch, tmp_path):
    """Sets up an isolated database, clean license store, and disables dev bypass."""
    monkeypatch.setenv("VAULTBASIS_BYPASS_ENTITLEMENT", "0")
    monkeypatch.delenv("VAULTBASIS_LICENSE_TOKEN", raising=False)

    test_db_path = tmp_path / "test_commercial.db"
    test_store = SQLiteStore(test_db_path)
    test_policy = CommercialPolicyService(
        store=test_store,
        license_dir=tmp_path / "license",
        keyring_override=_TEST_KEYRING,
    )

    # Patch global app instances for TestClient integration
    monkeypatch.setattr("edge.api.app.db_store", test_store)
    monkeypatch.setattr("edge.api.app.commercial_policy", test_policy)

    return test_policy, test_store, tmp_path


@pytest.fixture
def client():
    return TestClient(app)


# ------------------------------------------------------------------------------
# 1. Policy Service Direct Unit Tests
# ------------------------------------------------------------------------------

def test_policy_no_license_denied(clean_commercial_env):
    policy, store, _ = clean_commercial_env
    decision = policy.authorize(CommercialOperation.CREATE_CASE)
    assert not decision.allowed
    assert decision.reason_code == CommercialDenialCode.ENTITLEMENT_REQUIRED
    assert decision.http_status == 402
    assert "A valid commercial license is required" in decision.message
    assert decision.correlation_id.startswith("VB-ENT-")

    err_dict = decision.to_error_dict()
    assert err_dict["error"]["code"] == "ENTITLEMENT_REQUIRED"
    assert "upgrade_guidance" in err_dict["error"]


def test_policy_valid_license_authorized(clean_commercial_env):
    policy, store, _ = clean_commercial_env
    token = _make_test_token(tier=LicenseTier.PRACTICE, max_cases=10)
    policy.install_license_token(token)

    decision = policy.authorize(CommercialOperation.CREATE_CASE)
    assert decision.allowed
    assert decision.http_status == 200
    assert decision.license_state == LicenseState.ACTIVE
    assert decision.tier == LicenseTier.PRACTICE
    assert decision.max_cases == 10


def test_policy_expired_license_denied(clean_commercial_env):
    policy, store, _ = clean_commercial_env
    now = datetime.now(timezone.utc)
    # Chronologically valid, but expired in past
    token = _make_test_token(
        issued_at_dt=now - timedelta(days=60),
        not_before_dt=now - timedelta(days=60),
        expires_at_dt=now - timedelta(days=10),
        grace_until_dt=now - timedelta(days=5),
    )
    policy.install_license_token(token)

    decision = policy.authorize(CommercialOperation.CREATE_CASE)
    assert not decision.allowed
    assert decision.reason_code == CommercialDenialCode.LICENSE_EXPIRED
    assert decision.http_status == 403
    assert "expired" in decision.message.lower()


def test_policy_grace_license_restricts_new_cases(clean_commercial_env):
    policy, store, _ = clean_commercial_env
    now = datetime.now(timezone.utc)
    # Expired 5 days ago, but grace period lasts until +25 days -> currently in GRACE
    token = _make_test_token(
        issued_at_dt=now - timedelta(days=60),
        not_before_dt=now - timedelta(days=60),
        expires_at_dt=now - timedelta(days=5),
        grace_until_dt=now + timedelta(days=25),
    )
    policy.install_license_token(token)

    # Creating new cases is restricted in grace mode
    decision_create = policy.authorize(CommercialOperation.CREATE_CASE)
    assert not decision_create.allowed
    assert decision_create.reason_code == CommercialDenialCode.LICENSE_GRACE_RESTRICTED
    assert decision_create.http_status == 403

    # Reconciling existing work remains permitted
    decision_recon = policy.authorize(CommercialOperation.RECONCILE_CASE)
    assert decision_recon.allowed


def test_policy_not_yet_valid_license_denied(clean_commercial_env):
    policy, store, _ = clean_commercial_env
    now = datetime.now(timezone.utc)
    # Starts 5 days in the future
    token = _make_test_token(
        issued_at_dt=now,
        not_before_dt=now + timedelta(days=5),
        expires_at_dt=now + timedelta(days=365),
        grace_until_dt=now + timedelta(days=395),
    )
    policy.install_license_token(token)

    decision = policy.authorize(CommercialOperation.CREATE_CASE)
    assert not decision.allowed
    assert decision.reason_code == CommercialDenialCode.LICENSE_NOT_YET_VALID
    assert decision.http_status == 403


def test_policy_installation_mismatch_denied(clean_commercial_env):
    policy, store, _ = clean_commercial_env
    policy.installation_id = "INST-ALPHA-999"

    # Token bound to different installation
    token = _make_test_token(installation_id="INST-BETA-000")
    policy.install_license_token(token)

    decision = policy.authorize(CommercialOperation.CREATE_CASE)
    assert not decision.allowed
    assert decision.reason_code == CommercialDenialCode.INSTALLATION_MISMATCH
    assert decision.http_status == 403


def test_policy_tampered_signature_denied(clean_commercial_env):
    policy, store, _ = clean_commercial_env
    token = _make_test_token(output_format="json")
    env = json.loads(token)
    env["payload"]["max_cases_per_installation"] = 999999
    tampered_token = json.dumps(env)

    policy.install_license_token(tampered_token)
    decision = policy.authorize(CommercialOperation.CREATE_CASE)
    assert not decision.allowed
    assert decision.reason_code == CommercialDenialCode.LICENSE_INVALID
    assert decision.http_status == 403


def test_policy_capacity_limit_enforcement(clean_commercial_env):
    policy, store, _ = clean_commercial_env
    token = _make_test_token(tier=LicenseTier.TRIAL, max_cases=2)
    policy.install_license_token(token)

    # Initial state: 0 cases -> allowed
    d1 = policy.authorize(CommercialOperation.CREATE_CASE)
    assert d1.allowed

    # Simulate saving 2 persistent billable cases
    from schemas.canonical.case import CanonicalCase
    now_utc = datetime.now(timezone.utc).isoformat()
    store.save_case(CanonicalCase(case_id="CASE-PRACTITIONER-001", tax_year=2025, jurisdiction="US", case_status="CREATED", created_at=now_utc, updated_at=now_utc))
    store.save_case(CanonicalCase(case_id="CASE-PRACTITIONER-002", tax_year=2025, jurisdiction="US", case_status="CREATED", created_at=now_utc, updated_at=now_utc))

    # At capacity (2/2) -> new case creation denied
    d2 = policy.authorize(CommercialOperation.CREATE_CASE)
    assert not d2.allowed
    assert d2.reason_code == CommercialDenialCode.CASE_CAPACITY_REACHED
    assert d2.http_status == 402
    assert "reached the case limit for your current license" in d2.message

    # Bundled sample case does NOT consume capacity
    store.save_case(CanonicalCase(case_id="CASE-SAMPLE-2025", tax_year=2025, jurisdiction="US", case_status="CREATED", created_at=now_utc, updated_at=now_utc))
    assert store.count_billable_cases() == 2


# ------------------------------------------------------------------------------
# 2. REST API Integration Tests via TestClient
# ------------------------------------------------------------------------------

def test_api_create_case_denied_without_license(clean_commercial_env, client):
    res = client.post("/api/cases", json={"case_id": "CASE-UNLICENSED-001", "tax_year": 2025})
    assert res.status_code == 402
    data = res.json()
    assert data["error"]["code"] == "ENTITLEMENT_REQUIRED"
    assert "upgrade_guidance" in data["error"]
    assert "correlation_id" in data["error"]


def test_api_create_case_succeeds_with_license(clean_commercial_env, client):
    policy, store, _ = clean_commercial_env
    token = _make_test_token(tier=LicenseTier.ESSENTIAL, max_cases=5)
    
    # Install license via API endpoint
    res_inst = client.post("/api/commercial/license", json={"token": token})
    assert res_inst.status_code == 200
    assert res_inst.json()["license_state"] == "ACTIVE"
    assert res_inst.json()["tier"] == "ESSENTIAL"

    # Create case
    res_create = client.post("/api/cases", json={"case_id": "CASE-LICENSED-001", "tax_year": 2025})
    assert res_create.status_code == 201
    assert res_create.json()["case_id"] == "CASE-LICENSED-001"


def test_api_sample_case_unmetered_and_accessible_without_license(clean_commercial_env, client):
    """
    Bundled sample case must always be accessible and loadable for onboarding
    regardless of license state.
    """
    res = client.post("/api/sample-case/load")
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == "CASE-SAMPLE-2025"
    assert len(data["sources"]) == 2


def test_api_receipt_verification_unencumbered_without_license(clean_commercial_env, client):
    """
    Independent receipt verification must be 100% free and unmetered.
    """
    sample_receipt_path = Path(__file__).resolve().parent.parent / "fixtures" / "golden_receipt_valid.json"
    if not sample_receipt_path.is_file():
        pytest.skip("Fixture golden_receipt_valid.json not found")

    receipt_bytes = sample_receipt_path.read_bytes()
    res = client.post("/api/receipts/verify", files={"file": ("receipt.json", receipt_bytes, "application/json")})
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["overall_status"] == "PASS"


def test_api_existing_case_and_export_accessible_after_license_expiry(clean_commercial_env, client):
    """
    Data preservation invariant: An expired license must NOT ransom existing customer records
    or block evidence bundle export.
    """
    policy, store, _ = clean_commercial_env

    # 1. Install active license and create a case with sample sources and reconciliation
    token = _make_test_token(tier=LicenseTier.PRACTICE, max_cases=5)
    policy.install_license_token(token)

    res_sample = client.post("/api/sample-case/load")
    assert res_sample.status_code == 200

    res_recon = client.post("/api/cases/CASE-SAMPLE-2025/reconcile")
    assert res_recon.status_code == 200

    # 2. Now expire the license with monotonic revision 2 renewal
    now = datetime.now(timezone.utc)
    expired_token = _make_test_token(
        issued_at_dt=now - timedelta(days=60),
        not_before_dt=now - timedelta(days=60),
        expires_at_dt=now - timedelta(days=10),
        grace_until_dt=now - timedelta(days=5),
        revision=2,
    )
    policy.install_license_token(expired_token)

    # 3. New case creation is blocked
    res_blocked = client.post("/api/cases", json={"case_id": "CASE-NEW-BLOCKED", "tax_year": 2025})
    assert res_blocked.status_code == 403
    assert res_blocked.json()["error"]["code"] == "LICENSE_EXPIRED"

    # 4. Reading existing case is permitted
    res_get = client.get("/api/cases/CASE-SAMPLE-2025")
    assert res_get.status_code == 200
    assert res_get.json()["case_id"] == "CASE-SAMPLE-2025"

    # 5. Reading existing receipt is permitted
    res_rcpt = client.get("/api/cases/CASE-SAMPLE-2025/receipt")
    assert res_rcpt.status_code == 200

    # 6. Exporting evidence bundle is permitted
    res_exp = client.get("/api/cases/CASE-SAMPLE-2025/export")
    assert res_exp.status_code == 200
    assert res_exp.headers["content-type"] == "application/zip"


def test_api_commercial_status_endpoint(clean_commercial_env, client):
    policy, store, _ = clean_commercial_env
    
    # 1. Unlicensed status
    res1 = client.get("/api/commercial/status")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["licensed"] is False
    assert data1["unmetered_verification_active"] is True

    # 2. Licensed status
    token = _make_test_token(tier=LicenseTier.ENTERPRISE, max_cases=100)
    client.post("/api/commercial/license", json={"token": token})

    res2 = client.get("/api/commercial/status")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["licensed"] is True
    assert data2["tier"] == "ENTERPRISE"
    assert data2["max_cases_per_installation"] == 100
    assert data2["unmetered_verification_active"] is True


# ------------------------------------------------------------------------------
# 3. Adversarial Provenance & Anti-Laundering Tests
# ------------------------------------------------------------------------------

def test_adversarial_production_case_named_case_sample_2025_denied_without_license(clean_commercial_env, client):
    """
    Adversarial Boundary Test:
    A user cannot bypass commercial entitlement simply by naming their production case 'CASE-SAMPLE-2025'.
    Unmetered evaluation is granted only to authentic BUNDLED_SAMPLE provenance, not arbitrary strings.
    """
    policy, store, _ = clean_commercial_env

    # 1. Attempting to create a production case named 'CASE-SAMPLE-2025' without a license must return 402
    res_create = client.post("/api/cases", json={"case_id": "CASE-SAMPLE-2025", "tax_year": 2025})
    assert res_create.status_code == 402
    assert res_create.json()["error"]["code"] == "ENTITLEMENT_REQUIRED"

    # 2. Even if a PRODUCTION case with case_id="CASE-SAMPLE-2025" were saved directly into SQLite,
    # reconciling it without an authentic BUNDLED_SAMPLE provenance must fail closed (402).
    now_utc = datetime.now(timezone.utc).isoformat()
    spoofed_case = CanonicalCase(
        case_id="CASE-SAMPLE-2025",
        client_reference="Adversarial Client Data",
        tax_year=2025,
        jurisdiction="US",
        case_status="CREATED",
        case_kind="PRODUCTION",
        created_at=now_utc,
        updated_at=now_utc
    )
    store.save_case(spoofed_case)

    res_recon = client.post("/api/cases/CASE-SAMPLE-2025/reconcile")
    assert res_recon.status_code == 402
    assert res_recon.json()["error"]["code"] == "ENTITLEMENT_REQUIRED"


def test_adversarial_bundled_sample_rejects_client_csv_mutation(clean_commercial_env, client):
    """
    Anti-Sample-Laundering Invariant:
    A bundled sample case is immutable demonstration data. Attempting to upload
    custom client CSVs into a BUNDLED_SAMPLE container must be strictly rejected (403 Forbidden).
    """
    # 1. Load authentic bundled sample
    res_load = client.post("/api/sample-case/load")
    assert res_load.status_code == 200

    # 2. Attempt to upload arbitrary client CSV to the bundled sample
    fake_csv = b"Transaction_ID,Asset,Amount\nTX-999,BTC,100.0\n"
    res_upload = client.post(
        "/api/cases/CASE-SAMPLE-2025/sources",
        files={"file": ("client_private_data.csv", fake_csv, "text/csv")},
        data={"source_type": "AUTO"}
    )
    assert res_upload.status_code == 403
    assert "immutable demonstration baselines" in res_upload.json()["detail"]


def test_adversarial_authentic_bundled_sample_allowed_with_expired_license(clean_commercial_env, client):
    """
    Evaluation Invariant:
    Authentic bundled sample reconciliation and export remain 100% functional
    even when an installed commercial license is expired.
    """
    policy, store, _ = clean_commercial_env
    now = datetime.now(timezone.utc)
    expired_token = _make_test_token(
        issued_at_dt=now - timedelta(days=60),
        not_before_dt=now - timedelta(days=60),
        expires_at_dt=now - timedelta(days=10),
        grace_until_dt=now - timedelta(days=5),
    )
    policy.install_license_token(expired_token)

    # 1. Load authentic sample
    res_load = client.post("/api/sample-case/load")
    assert res_load.status_code == 200

    # 2. Reconcile sample case
    res_recon = client.post("/api/cases/CASE-SAMPLE-2025/reconcile")
    assert res_recon.status_code == 200

    # 3. Export sample evidence
    res_exp = client.get("/api/cases/CASE-SAMPLE-2025/export")
    assert res_exp.status_code == 200
    assert res_exp.headers["content-type"] == "application/zip"


def test_adversarial_caller_supplied_case_kind_cannot_bypass_stored_production_state(clean_commercial_env, client):
    """
    Provenance Defense Invariant:
    CommercialPolicyService NEVER trusts caller-supplied case_kind context.
    It resolves case_kind authoritatively from persisted SQLite state.
    """
    policy, store, _ = clean_commercial_env
    now_utc = datetime.now(timezone.utc).isoformat()

    # Save a production case in SQLite
    prod_case = CanonicalCase(
        case_id="CASE-REAL-PRODUCTION-001",
        client_reference="Paying Client",
        tax_year=2025,
        jurisdiction="US",
        case_status="CREATED",
        case_kind="PRODUCTION",
        created_at=now_utc,
        updated_at=now_utc
    )
    store.save_case(prod_case)

    # Caller attempts to spoof context={"case_kind": "BUNDLED_SAMPLE"} for this production case
    spoofed_context = {
        "case_id": "CASE-REAL-PRODUCTION-001",
        "case_kind": "BUNDLED_SAMPLE"  # Adversarial spoof attempt
    }
    decision = policy.authorize(CommercialOperation.RECONCILE_CASE, context=spoofed_context)
    assert not decision.allowed
    assert decision.http_status == 402
    assert decision.reason_code == CommercialDenialCode.ENTITLEMENT_REQUIRED


def test_adversarial_bundled_sample_deletion_rejected(clean_commercial_env, client):
    """
    Sample Immutability Invariant:
    A bundled sample case is an immutable system baseline and cannot be deleted via DELETE /api/cases/{id}.
    """
    res_load = client.post("/api/sample-case/load")
    assert res_load.status_code == 200

    res_del = client.delete("/api/cases/CASE-SAMPLE-2025")
    assert res_del.status_code == 403
    assert "immutable demonstration baselines" in res_del.json()["detail"]


def test_clone_sample_to_production_requires_license_and_consumes_capacity(clean_commercial_env, client):
    """
    Cloning Semantics Invariant:
    Cloning an authentic sample case produces a PRODUCTION case that loses sample provenance,
    requires active commercial entitlement to create, and consumes licensed capacity.
    """
    policy, store, _ = clean_commercial_env
    client.post("/api/sample-case/load")

    # 1. Unlicensed clone attempt is blocked (402)
    res_clone_unauth = client.post("/api/cases/CASE-SAMPLE-2025/clone", json={"new_case_id": "CASE-PROD-CLONE-001"})
    assert res_clone_unauth.status_code == 402
    assert res_clone_unauth.json()["error"]["code"] == "ENTITLEMENT_REQUIRED"

    # 2. Install license with capacity limit of 1
    token = _make_test_token(tier=LicenseTier.ESSENTIAL, max_cases=1)
    policy.install_license_token(token)

    # 3. Licensed clone succeeds and sets case_kind=PRODUCTION
    res_clone = client.post("/api/cases/CASE-SAMPLE-2025/clone", json={"new_case_id": "CASE-PROD-CLONE-001"})
    assert res_clone.status_code == 201
    data = res_clone.json()
    assert data["case_id"] == "CASE-PROD-CLONE-001"

    # Verify persisted state
    persisted = store.get_case("CASE-PROD-CLONE-001")
    assert persisted is not None
    assert persisted.case_kind == "PRODUCTION"
    assert persisted.sample_definition_id is None
    assert store.count_billable_cases() == 1

    # 4. Next case creation is blocked because capacity (1/1) is now reached
    res_next = client.post("/api/cases", json={"case_id": "CASE-EXCEEDED-002", "tax_year": 2025})
    assert res_next.status_code == 402
    assert res_next.json()["error"]["code"] == "CASE_CAPACITY_REACHED"


def test_adversarial_tampered_sample_manifest_digest_denied_without_license(clean_commercial_env, client):
    """
    Sample Digest Verification Invariant:
    A case claiming case_kind='BUNDLED_SAMPLE' but possessing an altered, forged,
    or mismatched sample_manifest_digest fails closed (402 ENTITLEMENT_REQUIRED).
    """
    policy, store, _ = clean_commercial_env
    now_utc = datetime.now(timezone.utc).isoformat()

    # Save a forged sample case with invalid manifest digest
    forged_sample = CanonicalCase(
        case_id="CASE-FORGED-SAMPLE-001",
        client_reference="Forged Sample Data",
        tax_year=2025,
        jurisdiction="US",
        case_status="CREATED",
        case_kind="BUNDLED_SAMPLE",
        sample_definition_id="SAMPLE-A-2025-01",
        sample_manifest_digest="0000000000000000000000000000000000000000000000000000000000000000",  # Forged digest
        created_at=now_utc,
        updated_at=now_utc
    )
    store.save_case(forged_sample)

    res_recon = client.post("/api/cases/CASE-FORGED-SAMPLE-001/reconcile")
    assert res_recon.status_code == 402
    assert res_recon.json()["error"]["code"] == "ENTITLEMENT_REQUIRED"


def test_sample_case_actions_rerun_and_reset_workflow(clean_commercial_env, client):
    """
    MMP15-EDGE-STATE-002:
    Validates sample case domain actions, unmetered reconciliation, deterministic rerun,
    and automated reset to pristine baseline.
    """
    policy, store, _ = clean_commercial_env

    # 1. Load canonical sample case
    res_load = client.post("/api/sample-case/load")
    assert res_load.status_code == 200
    case_data = res_load.json()
    assert case_data["case_id"] == "CASE-SAMPLE-2025"
    assert "actions" in case_data
    assert case_data["actions"]["can_reconcile"] is True
    assert case_data["actions"]["can_restart_sample"] is True
    assert case_data["actions"]["can_view_receipt"] is False

    # 2. Run deterministic reconciliation without any commercial license
    res_recon = client.post("/api/cases/CASE-SAMPLE-2025/reconcile")
    assert res_recon.status_code == 200
    assert "reconciliation" in res_recon.json()

    # 3. Fetch case detail and verify actions reflect completed state
    res_detail = client.get("/api/cases/CASE-SAMPLE-2025")
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert detail_data["actions"]["can_reconcile"] is True  # Rerun enabled
    assert detail_data["actions"]["can_view_receipt"] is True
    assert detail_data["actions"]["can_restart_sample"] is True

    # 4. Rerun deterministic reconciliation (Option A: deterministic rerun returns 200)
    res_rerun = client.post("/api/cases/CASE-SAMPLE-2025/reconcile")
    assert res_rerun.status_code == 200
    assert res_rerun.json()["status"] == "RECEIPT_ALREADY_ISSUED"

    # 5. Reset sample case to pristine baseline
    res_reset = client.post("/api/sample-case/reset")
    assert res_reset.status_code == 200
    reset_data = res_reset.json()
    assert reset_data["receipt_id"] is None
    assert reset_data["outcome_state"] is None
    assert reset_data["actions"]["can_view_receipt"] is False
    assert reset_data["actions"]["can_reconcile"] is True


def test_five_state_entitlement_status_vocabulary(clean_commercial_env):
    """
    MMP15-EDGE-STATE-002:
    Validates explicit 5-state entitlement status vocabulary:
    NO_ENTITLEMENT, ACTIVE_EVALUATION, ACTIVE_PAID_LICENSE, EXPIRED_EVALUATION, EXPIRED_PAID_LICENSE.
    """
    policy, store, _ = clean_commercial_env
    now = datetime.now(timezone.utc)

    # 1. No license installed -> NO_ENTITLEMENT
    status_none = policy.get_status(current_time=now)
    assert status_none["entitlement_state"] == "NO_ENTITLEMENT"
    assert status_none["licensed"] is False

    # 2. Active Evaluation license -> ACTIVE_EVALUATION
    eval_token = _make_test_token(
        tier=LicenseTier.EVALUATION,
        max_cases=1,
        expires_at_dt=now + timedelta(days=3),
        grace_until_dt=now + timedelta(days=5),
    )
    policy.install_license_token(eval_token)
    status_eval = policy.get_status(current_time=now)
    assert status_eval["entitlement_state"] == "ACTIVE_EVALUATION"
    assert status_eval["licensed"] is True
    assert "Evaluation Active" in status_eval["message"]

    # 3. Expired Evaluation license -> EXPIRED_EVALUATION
    status_eval_exp = policy.get_status(current_time=now + timedelta(days=6))
    assert status_eval_exp["entitlement_state"] == "EXPIRED_EVALUATION"
    assert status_eval_exp["licensed"] is False

    # 4. Active Paid license (Solo / Practice) -> ACTIVE_PAID_LICENSE
    paid_token = _make_test_token(
        tier=LicenseTier.PRACTICE,
        max_cases=50,
        expires_at_dt=now + timedelta(days=365),
        grace_until_dt=now + timedelta(days=375),
    )
    policy.remove_license_token()
    policy.install_license_token(paid_token)
    status_paid = policy.get_status(current_time=now)
    assert status_paid["entitlement_state"] == "ACTIVE_PAID_LICENSE"
    assert status_paid["licensed"] is True

    # 5. Expired Paid license -> EXPIRED_PAID_LICENSE
    status_paid_exp = policy.get_status(current_time=now + timedelta(days=380))
    assert status_paid_exp["entitlement_state"] == "EXPIRED_PAID_LICENSE"
    assert status_paid_exp["licensed"] is False




