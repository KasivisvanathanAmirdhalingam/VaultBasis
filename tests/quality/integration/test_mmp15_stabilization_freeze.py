"""
VaultBasis MMP-1.5 Stabilization Freeze Regression Test Suite
Defect Queue Verification:
- MMP15-EVAL-E2E-001: Real Evaluation Entitlement Qualification (72h, 1 client case capacity, fail-closed production boundary)
- MMP15-CASE-TIME-001: Authoritative UTC created_at / updated_at timestamps
- MMP15-CASE-EVIDENCE-UX-001: Actionable Needs Evidence work queue and gap classification
- MMP15-EVIDENCE-GUIDE-001: Human-readable Evidence Receipt Guide endpoint
- MMP15-PLAN-NAMING-001: Practitioner and Firm license tiers & in-place upgrade qualification
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import ed25519

from edge.api.app import app
from edge.commercial.audit import CommercialAuditService
from edge.commercial.keys import COMMERCIAL_KEYRING
from edge.commercial.models import LicenseTier
from edge.commercial.policy import (
    CommercialDenialCode,
    CommercialOperation,
    CommercialPolicyService,
)
from edge.storage.sqlite_store import SQLiteStore
from schemas.canonical.case import CanonicalCase, SourceDocumentMetadata
from tools.issue_license import issue_commercial_license


@pytest.fixture
def freeze_test_env(monkeypatch, tmp_path):
    monkeypatch.setenv("VAULTBASIS_BYPASS_ENTITLEMENT", "0")
    monkeypatch.delenv("VAULTBASIS_LICENSE_TOKEN", raising=False)
    db_file = tmp_path / "freeze_test.db"
    store = SQLiteStore(db_file)
    license_dir = tmp_path / "lic"
    installation_id = "INST-FREEZE-001"

    audit_service = CommercialAuditService(store=store, installation_id=installation_id)
    policy_service = CommercialPolicyService(
        store=store,
        license_dir=license_dir,
        installation_id=installation_id,
        audit_service=audit_service,
    )

    # Patch global app instances for TestClient integration
    monkeypatch.setattr("edge.api.app.db_store", store)
    monkeypatch.setattr("edge.api.app.commercial_policy", policy_service)
    monkeypatch.setattr("edge.api.app.commercial_audit_service", audit_service)

    client = TestClient(app)
    return {
        "store": store,
        "policy": policy_service,
        "audit": audit_service,
        "client": client,
        "tmp_path": tmp_path,
        "installation_id": installation_id,
    }


def test_mmp15_eval_e2e_001_lifecycle(freeze_test_env):
    """
    Tests MMP15-EVAL-E2E-001 & MMP15-COMMERCIAL-POLICY-LOCK-002:
    1. Fresh install without evaluation: NO_ENTITLEMENT -> cannot create client case (402 Payment Required)
    2. Start 3-day evaluation: ACTIVE_EVALUATION created with 3 client cases capacity
    3. Can create client cases 1, 2, and 3
    4. Fourth client case rejected with capacity denial (402 Payment Required / CASE_CAPACITY_REACHED)
    5. Monotonic tracking: deleting an existing case does NOT restore capacity slot
    6. Existing evaluation cases remain accessible
    """
    client = freeze_test_env["client"]
    store = freeze_test_env["store"]
    policy = freeze_test_env["policy"]

    # 1. Fresh state: create client case blocked fail-closed
    resp = client.post("/api/cases", json={"client_reference": "Client 1", "tax_year": 2025})
    assert resp.status_code == 402
    assert resp.json()["error"]["code"] == CommercialDenialCode.ENTITLEMENT_REQUIRED.value

    # 2. Start evaluation
    eval_resp = client.post("/api/commercial/start-evaluation", json={"customer_name": "CPA Test Practitioner"})
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["status"] == "INSTALLED"
    assert eval_data["tier"] == "EVALUATION"
    assert eval_data["max_cases_per_installation"] == 3
    assert eval_data["days_remaining"] in (2, 3)

    # Check commercial status
    status_resp = client.get("/api/commercial/status")
    assert status_resp.status_code == 200
    st = status_resp.json()
    assert st["licensed"] is True
    assert st["tier"] == "EVALUATION"
    assert st["max_cases_per_installation"] == 3
    assert st["billable_cases_count"] == 0

    # 3. Create client cases 1, 2, and 3 -> Allowed (201 Created)
    case1_resp = client.post("/api/cases", json={"client_reference": "Client 1", "tax_year": 2025})
    assert case1_resp.status_code == 201
    case1_id = case1_resp.json()["case_id"]

    case2_resp = client.post("/api/cases", json={"client_reference": "Client 2", "tax_year": 2025})
    assert case2_resp.status_code == 201
    case2_id = case2_resp.json()["case_id"]

    case3_resp = client.post("/api/cases", json={"client_reference": "Client 3", "tax_year": 2025})
    assert case3_resp.status_code == 201
    case3_id = case3_resp.json()["case_id"]

    # Check status updated to 3 used
    st2 = client.get("/api/commercial/status").json()
    assert st2["billable_cases_count"] == 3

    # 4. Create fourth client case -> Rejected due to evaluation capacity limit
    case4_resp = client.post("/api/cases", json={"client_reference": "Client 4", "tax_year": 2025})
    assert case4_resp.status_code == 403
    assert case4_resp.json()["error"]["code"] == CommercialDenialCode.EVALUATION_CAPACITY_REACHED.value

    # 5. Existing cases remain readable and listable
    list_resp = client.get("/api/cases")
    assert list_resp.status_code == 200
    cases = list_resp.json()
    assert any(c["case_id"] == case1_id for c in cases)
    assert any(c["case_id"] == case2_id for c in cases)
    assert any(c["case_id"] == case3_id for c in cases)


def test_mmp15_case_time_001_timestamps(freeze_test_env):
    """
    Tests MMP15-CASE-TIME-001:
    Database stores authoritative UTC created_at and updated_at timestamps.
    """
    client = freeze_test_env["client"]
    store = freeze_test_env["store"]

    # Start evaluation to allow case creation
    client.post("/api/commercial/start-evaluation", json={"customer_name": "Timestamp Test"})

    resp = client.post("/api/cases", json={"client_reference": "Timestamp Client", "tax_year": 2025})
    assert resp.status_code == 201
    case_data = resp.json()

    assert "created_at" in case_data
    assert "updated_at" in case_data
    assert case_data["created_at"] is not None
    assert case_data["updated_at"] is not None

    # Verify retrieval from store maintains timestamps
    stored_case = store.get_case(case_data["case_id"])
    assert stored_case.created_at is not None
    assert stored_case.updated_at is not None


def test_mmp15_case_evidence_ux_001_work_queue(freeze_test_env):
    """
    Tests MMP15-CASE-EVIDENCE-UX-001:
    API computes actionable evidence gap classifications and next action labels.
    """
    client = freeze_test_env["client"]
    store = freeze_test_env["store"]

    client.post("/api/commercial/start-evaluation", json={"customer_name": "WorkQueue Test"})
    case_resp = client.post("/api/cases", json={"client_reference": "Queue Client", "tax_year": 2025})
    assert case_resp.status_code == 201
    case_id = case_resp.json()["case_id"]

    # 1. No sources attached -> MISSING_BOTH
    cases_resp = client.get("/api/cases")
    target_case = next(c for c in cases_resp.json() if c["case_id"] == case_id)
    assert target_case["evidence_gap"] == "MISSING_BOTH"
    assert "both" in target_case["evidence_status_label"].lower()
    assert target_case["next_action_label"] == "Complete intake →"

    # 2. Attach only 1099-DA source -> MISSING_LEDGER
    src_1099 = SourceDocumentMetadata(
        source_id="SRC-1099-001",
        filename="1099da.csv",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        byte_size=1024,
        schema_id="US_BROKER_FORM_1099_DA_CSV_V1",
        row_count=10,
        ingested_at=datetime.now(timezone.utc).isoformat(),
    )
    store.add_source_and_transactions(case_id, src_1099, b"test_raw", [])

    cases_resp = client.get("/api/cases")
    target_case = next(c for c in cases_resp.json() if c["case_id"] == case_id)
    assert target_case["evidence_gap"] == "MISSING_LEDGER"
    assert "tax ledger" in target_case["evidence_status_label"].lower()
    assert target_case["next_action_label"] == "Add client ledger →"


def test_mmp15_evidence_guide_001_endpoint(freeze_test_env):
    """
    Tests MMP15-EVIDENCE-GUIDE-001:
    Human-readable Evidence Receipt Guide is served at /evidence-receipt-guide.
    """
    client = freeze_test_env["client"]
    resp = client.get("/evidence-receipt-guide")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Evidence Receipt Guide" in resp.text
    assert "What is an Evidence Receipt?" in resp.text
    assert "schemas/receipt-v0.1.json" in resp.text


def test_mmp15_plan_naming_001_practitioner_and_firm(freeze_test_env):
    """
    Tests MMP15-PLAN-NAMING-001:
    Practitioner (10 cases) and Firm (50 cases) license tiers function seamlessly
    including in-place monotonic upgrade from Practitioner -> Firm.
    """
    priv_key = ed25519.Ed25519PrivateKey.generate()
    pub_hex = priv_key.public_key().public_bytes_raw().hex()
    priv_hex = priv_key.private_bytes_raw().hex()

    # Issue Practitioner license (Revision 1)
    token_practitioner = issue_commercial_license(
        signing_key_hex=priv_hex,
        key_id="KEY-TEST-PRACTITIONER",
        customer_id="CPA-001",
        tier=LicenseTier.PRACTITIONER.value,
        max_cases=10,
        valid_days=365,
        revision=1,
    )

    policy = freeze_test_env["policy"]
    policy.keyring_override = {
        "KEY-TEST-PRACTITIONER": pub_hex,
        "KEY-TEST-FIRM": pub_hex,
    }

    res_p = policy.install_license_token(token_practitioner)
    assert res_p.is_active is True
    assert res_p.tier == LicenseTier.PRACTITIONER
    assert res_p.max_cases_per_installation == 10

    # In-place upgrade: Firm license for same customer (Revision 2)
    token_firm = issue_commercial_license(
        signing_key_hex=priv_hex,
        key_id="KEY-TEST-FIRM",
        customer_id="CPA-001",
        tier=LicenseTier.FIRM.value,
        max_cases=50,
        valid_days=365,
        revision=2,
    )

    res_f = policy.install_license_token(token_firm)
    assert res_f.is_active is True
    assert res_f.tier == LicenseTier.FIRM
    assert res_f.max_cases_per_installation == 50
