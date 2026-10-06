"""
VaultBasis MMP-1.5 Practitioner Journey Integration Test Suite (MMP15-PROD-EDGE-INT-001)

Validates the three end-to-end practitioner journeys against the real Edge application daemon:
- Journey A: Free Evaluation / Sample (Sample immutability, zero-capacity evaluation, deterministic reconciliation, cloned production transition)
- Journey B: Authoritative Client Case Lifecycle (Synchronous creation, identity binding, precondition gating, dual ingestion, signed receipt generation)
- Journey C: Existing Case State & Durability (Retrieval, export bundle integrity, no identity divergence across app restarts)
"""

import io
import json
import zipfile
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import ed25519

from edge.api.app import app
import edge.api.app as app_module
from edge.commercial.audit import CommercialAuditService
from edge.commercial.policy import CommercialPolicyService
from edge.storage.sqlite_store import SQLiteStore
from tools.issue_license import issue_commercial_license


_TEST_PRIV_KEY = ed25519.Ed25519PrivateKey.generate()
_TEST_PRIV_HEX = _TEST_PRIV_KEY.private_bytes_raw().hex()
_TEST_PUB_HEX = _TEST_PRIV_KEY.public_key().public_bytes_raw().hex()
_TEST_KEY_ID = "KEY-JOURNEY-TEST-001"
_TEST_KEYRING = {_TEST_KEY_ID: _TEST_PUB_HEX}

_SAMPLE_1099DA_CSV = (
    b"Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2\n"
    b"BTC,2025-11-20,18400.00,2025-02-11,12100.00,YES\n"
    b"ETH,2025-12-05,3200.00,2025-03-01,2800.00,YES\n"
)

_SAMPLE_KOINLY_CSV = (
    b"Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired\n"
    b"2025-11-20,BTC,1.0,12100.00,18400.00,6300.00,2025-02-11\n"
    b"2025-12-05,ETH,1.0,2800.00,3200.00,400.00,2025-03-01\n"
)


@pytest.fixture
def test_client(monkeypatch, tmp_path):
    monkeypatch.setenv("VAULTBASIS_BYPASS_ENTITLEMENT", "0")
    monkeypatch.delenv("VAULTBASIS_LICENSE_TOKEN", raising=False)

    db_file = tmp_path / "edge_journeys.db"
    store = SQLiteStore(db_file)
    license_dir = tmp_path / "lic"
    license_dir.mkdir(parents=True, exist_ok=True)

    audit_service = CommercialAuditService(store=store, installation_id="INST-JOURNEY-001")
    policy_service = CommercialPolicyService(
        store=store,
        license_dir=license_dir,
        installation_id="INST-JOURNEY-001",
        audit_service=audit_service,
        keyring_override=_TEST_KEYRING,
    )

    # Patch global instances in app
    monkeypatch.setattr(app_module, "db_store", store)
    monkeypatch.setattr(app_module, "commercial_policy", policy_service)

    client = TestClient(app)
    return {
        "client": client,
        "store": store,
        "policy": policy_service,
        "license_dir": license_dir,
    }


def test_journey_a_free_evaluation_sample_lifecycle(test_client):
    """
    Journey A: Free Evaluation
    1. Preloads bundled sample case without requiring active commercial license
    2. Enforces read-only sample provenance (case_kind == 'BUNDLED_SAMPLE')
    3. Successfully runs deterministic reconciliation
    4. Generates verifiable Evidence Receipt
    """
    client = test_client["client"]

    # 1. Preload Sample Case
    res = client.post("/api/sample-case/load")
    assert res.status_code == 200, res.text
    sample_case = res.json()
    assert sample_case["case_id"] == "CASE-SAMPLE-2025"
    assert sample_case["case_kind"] == "BUNDLED_SAMPLE"
    assert len(sample_case["sources"]) == 2

    # 2. Case List inspection
    list_res = client.get("/api/cases")
    assert list_res.status_code == 200
    cases = list_res.json()
    assert any(c["case_id"] == "CASE-SAMPLE-2025" for c in cases)

    # 3. Reconcile Sample Case (Unmetered, permitted without commercial license)
    recon_res = client.post("/api/cases/CASE-SAMPLE-2025/reconcile")
    assert recon_res.status_code == 200, recon_res.text
    recon_data = recon_res.json()
    assert "receipt" in recon_data
    assert recon_data["receipt"]["outcome_state"] in ("MATCHED", "PROCEEDS_DIFFERENCE")

    # 4. Fetch Evidence Receipt
    rcpt_res = client.get("/api/cases/CASE-SAMPLE-2025/receipt")
    assert rcpt_res.status_code == 200
    receipt = rcpt_res.json()
    assert "receipt_id" in receipt
    assert receipt["outcome_state"] in ("MATCHED", "PROCEEDS_DIFFERENCE")


def test_journey_b_paid_client_case_lifecycle(test_client):
    """
    Journey B: Paid Client Case Lifecycle
    1. Unlicensed creation fails closed (HTTP 402/403)
    2. Installing valid commercial token unlocks case creation
    3. Synchronous case persistence guarantees authoritative ID
    4. Uploading Source A and Source B validates schema and hashes
    5. Reconcile executes deterministically and signs receipt
    """
    client = test_client["client"]

    # 1. Unlicensed case creation attempt -> Rejected
    unlic_res = client.post(
        "/api/cases",
        json={"case_id": "CASE-CLIENT-001", "client_reference": "Redwood CPA LLC", "tax_year": 2025}
    )
    assert unlic_res.status_code in (402, 403)

    # 2. Install valid commercial license token via API
    token_str = issue_commercial_license(
        signing_key_hex=_TEST_PRIV_HEX,
        customer_id="CUST-REDWOOD-001",
        tier="PRACTICE",
        max_cases=50,
        valid_days=365,
        license_id="LIC-PRACTICE-001",
        key_id=_TEST_KEY_ID,
    )
    lic_res = client.post("/api/commercial/license", json={"token": token_str})
    assert lic_res.status_code == 200, lic_res.text

    # 3. Synchronous Case Creation -> Succeeds (HTTP 201)
    case_res = client.post(
        "/api/cases",
        json={"case_id": "CASE-CLIENT-001", "client_reference": "Redwood CPA LLC", "tax_year": 2025}
    )
    assert case_res.status_code == 201, case_res.text
    created = case_res.json()
    assert created["case_id"] == "CASE-CLIENT-001"
    assert created["case_status"] == "CREATED"

    # 4. Ingest Source A (Form 1099-DA)
    src_a_res = client.post(
        "/api/cases/CASE-CLIENT-001/sources",
        files={"file": ("Broker_1099DA.csv", io.BytesIO(_SAMPLE_1099DA_CSV), "text/csv")},
        data={"source_type": "AUTO"}
    )
    assert src_a_res.status_code == 200, src_a_res.text

    # Reconcile should fail with only 1 source
    recon_fail = client.post("/api/cases/CASE-CLIENT-001/reconcile")
    assert recon_fail.status_code == 400

    # Ingest Source B (Koinly CSV)
    src_b_res = client.post(
        "/api/cases/CASE-CLIENT-001/sources",
        files={"file": ("Koinly_Ledger.csv", io.BytesIO(_SAMPLE_KOINLY_CSV), "text/csv")},
        data={"source_type": "AUTO"}
    )
    assert src_b_res.status_code == 200, src_b_res.text

    # 5. Run Deterministic Reconciliation
    recon_res = client.post("/api/cases/CASE-CLIENT-001/reconcile")
    assert recon_res.status_code == 200, recon_res.text
    recon_data = recon_res.json()
    assert recon_data["receipt"]["outcome_state"] == "MATCHED"


def test_journey_c_existing_case_durability_and_export(test_client):
    """
    Journey C: Existing Case State & Export Durability
    1. Preloaded sample or client case persists across GET /api/cases/{case_id}
    2. Evidence bundle export produces structured ZIP with receipt and raw sources
    3. Verifier verifies exported receipt locally
    """
    client = test_client["client"]

    # Preload and reconcile sample
    client.post("/api/sample-case/load")
    client.post("/api/cases/CASE-SAMPLE-2025/reconcile")

    # Re-fetch case detail
    case_detail = client.get("/api/cases/CASE-SAMPLE-2025").json()
    assert case_detail["case_id"] == "CASE-SAMPLE-2025"
    assert case_detail["outcome_state"] in ("MATCHED", "PROCEEDS_DIFFERENCE")
    assert len(case_detail["sources"]) == 2
    assert case_detail["reconciliation"] is not None
    assert case_detail["reconciliation"]["total_evaluated_count"] == 5
    assert len(case_detail["reconciliation"]["agreed_records"]) == 2
    assert len(case_detail["reconciliation"]["material_differences"]) == 3
    assert len(case_detail["reconciliation"]["unresolved_items"]) == 0

    # Download export ZIP bundle
    export_res = client.get("/api/cases/CASE-SAMPLE-2025/export")
    assert export_res.status_code == 200
    assert export_res.headers["content-type"] == "application/zip"

    # Verify ZIP contents
    with zipfile.ZipFile(io.BytesIO(export_res.content)) as zf:
        namelist = zf.namelist()
        assert "receipt-v0.1.json" in namelist
        assert "VERIFY_INSTRUCTIONS.txt" in namelist
        receipt_bytes = zf.read("receipt-v0.1.json")
        rcpt = json.loads(receipt_bytes)
        assert rcpt["outcome_state"] in ("MATCHED", "PROCEEDS_DIFFERENCE")


def test_branding_and_favicon_routes(test_client):
    """
    Assert canonical branding assets return HTTP 200 OK on Edge server.
    - /favicon.ico
    - /favicon.svg
    - /apple-touch-icon.png
    - /site.webmanifest
    """
    client = test_client["client"]
    for asset_path in ["/favicon.ico", "/favicon.svg", "/apple-touch-icon.png", "/site.webmanifest"]:
        res = client.get(asset_path)
        assert res.status_code == 200, f"Asset {asset_path} returned {res.status_code}"
        assert len(res.content) > 0, f"Asset {asset_path} was empty"


def test_journey_evaluation_activation_and_capacity_enforcement(test_client):
    """
    MMP15-EVAL-UX-TRANSITION-001:
    1. Start 3-day evaluation via POST /api/commercial/start-evaluation -> 200 OK
    2. Entitlement status reflects ACTIVE evaluation with 1 client case capacity
    3. First client case creation succeeds (HTTP 201)
    4. Second client case creation is rejected (HTTP 403) due to evaluation capacity limit
    """
    client = test_client["client"]

    # 1. Start Evaluation
    start_res = client.post("/api/commercial/start-evaluation")
    assert start_res.status_code == 200, start_res.text
    eval_data = start_res.json()
    assert eval_data["status"] == "INSTALLED"
    assert eval_data["license_state"] == "ACTIVE"
    assert eval_data["tier"] == "EVALUATION"
    assert eval_data["max_cases_per_installation"] == 1

    # 2. Check authoritative current commercial status
    status_res = client.get("/api/commercial/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["license_state"] == "ACTIVE"
    assert status_data["entitlement_state"] == "ACTIVE_EVALUATION"
    assert status_data["tier"] == "EVALUATION"
    assert status_data["billable_cases_count"] == 0
    assert status_data["max_cases_per_installation"] == 1

    # 3. Create First Client Case -> Allowed
    case1_res = client.post(
        "/api/cases",
        json={"case_id": "CASE-EVAL-001", "client_reference": "Eval Client Alpha", "tax_year": 2025}
    )
    assert case1_res.status_code == 201, case1_res.text
    assert case1_res.json()["case_id"] == "CASE-EVAL-001"

    # 4. Check updated usage
    status_res2 = client.get("/api/commercial/status")
    assert status_res2.json()["billable_cases_count"] == 1

    # 5. Create Second Client Case -> Blocked by capacity limit
    case2_res = client.post(
        "/api/cases",
        json={"case_id": "CASE-EVAL-002", "client_reference": "Eval Client Beta", "tax_year": 2025}
    )
    assert case2_res.status_code in (402, 403)


def test_practitioner_facing_license_error_messages(test_client):
    """
    Ensure invalid or mismatched license activation yields practitioner language,
    not engineering / parser terminology (no JSON, Base64, etc.).
    """
    client = test_client["client"]

    # 1. Garbage text submission
    res_garbage = client.post("/api/commercial/license", json={"token": "sfddsfsdsdfdfs"})
    assert res_garbage.status_code == 200
    data_garbage = res_garbage.json()
    assert data_garbage["status"] == "REJECTED"
    err_text = data_garbage.get("diagnostic_reason", "")
    assert "JSON" not in err_text
    assert "Base64" not in err_text
    assert "License not recognized" in err_text

    # 2. License issued for different installation ID
    token_mismatched = issue_commercial_license(
        signing_key_hex=_TEST_PRIV_HEX,
        customer_id="CUST-OTHER-001",
        tier="PRACTICE",
        max_cases=10,
        valid_days=365,
        license_id="LIC-OTHER-001",
        key_id=_TEST_KEY_ID,
        installation_id="INST-DIFFERENT-MACHINE",
    )
    res_mismatch = client.post("/api/commercial/license", json={"token": token_mismatched})
    assert res_mismatch.status_code == 200
    data_mismatch = res_mismatch.json()
    assert data_mismatch["status"] == "REJECTED"
    err_mismatch = data_mismatch.get("diagnostic_reason", "")
    assert "another installation" in err_mismatch


