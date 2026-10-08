import pytest
import io
import json
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from edge.api.app import app, db_store, commercial_policy
from edge.commercial.policy import LicenseTier, LicenseState
from edge.assurance.reconciliation_engine import DeterministicReconciliationEngine
from tests.unit.test_mmp15_entitlement_enforcement import _make_test_token


from edge.commercial.policy import (
    CommercialDenialCode,
    CommercialOperation,
    CommercialPolicyService,
)
from edge.storage.sqlite_store import SQLiteStore
from tests.unit.test_mmp15_entitlement_enforcement import _make_test_token, _TEST_KEYRING


@pytest.fixture
def clean_commercial_env(monkeypatch, tmp_path):
    monkeypatch.setenv("VAULTBASIS_BYPASS_ENTITLEMENT", "0")
    monkeypatch.delenv("VAULTBASIS_LICENSE_TOKEN", raising=False)

    test_db_path = tmp_path / "test_sample_immutability.db"
    test_store = SQLiteStore(test_db_path)
    test_policy = CommercialPolicyService(
        store=test_store,
        license_dir=tmp_path / "license",
        keyring_override=_TEST_KEYRING,
    )

    monkeypatch.setattr("edge.api.app.db_store", test_store)
    monkeypatch.setattr("edge.api.app.commercial_policy", test_policy)

    return test_policy, test_store, tmp_path


@pytest.fixture
def client():
    return TestClient(app)


def test_bundled_sample_immutability_enforcement(clean_commercial_env, client):
    """
    REQ-SAM-001 / MMP15-UAT-PRESIGN-001 Invariant:
    Authentic bundled sample (CASE-SAMPLE-2025) is immutable reference evidence.
    All review, note, finalization, delete, and source mutation actions are strictly blocked (403).
    Viewing, reconciliation, and export remain unmetered.
    """
    policy, store, _ = clean_commercial_env

    # 1. Load sample case (unmetered)
    res_load = client.post("/api/sample-case/load")
    assert res_load.status_code == 200
    assert res_load.json()["case_id"] == "CASE-SAMPLE-2025"
    assert res_load.json()["case_kind"] == "BUNDLED_SAMPLE"
    assert store.count_billable_cases() == 0

    # 2. Reconcile sample case (unmetered, succeeds)
    res_recon = client.post("/api/cases/CASE-SAMPLE-2025/reconcile")
    assert res_recon.status_code == 200
    assert store.count_billable_cases() == 0

    # 3. Attempt finding disposition mutation -> MUST FAIL (403)
    res_review = client.post(
        "/api/cases/CASE-SAMPLE-2025/reviews",
        json={"finding_id": "DIFF-001", "disposition": "REVIEWED"}
    )
    assert res_review.status_code == 403
    assert "immutable demonstration baselines" in res_review.json()["detail"]
    assert "Clone this sample" in res_review.json()["detail"]

    # 4. Attempt practitioner note creation -> MUST FAIL (403)
    res_note = client.post(
        "/api/cases/CASE-SAMPLE-2025/reviews",
        json={"finding_id": "DIFF-001", "disposition": "REVIEWED", "note": "Adjust lot basis"}
    )
    assert res_note.status_code == 403
    assert "immutable demonstration baselines" in res_note.json()["detail"]

    # 5. Attempt review finalization -> MUST FAIL (403)
    res_finalize = client.post(
        "/api/cases/CASE-SAMPLE-2025/finalize-review",
        json={"reviewer_identity": "Practitioner"}
    )
    assert res_finalize.status_code == 403
    assert "immutable demonstration baselines" in res_finalize.json()["detail"]

    # 6. Attempt case deletion -> MUST FAIL (403)
    res_del = client.delete("/api/cases/CASE-SAMPLE-2025")
    assert res_del.status_code == 403
    assert "immutable demonstration baselines" in res_del.json()["detail"]

    # 7. Attempt source upload -> MUST FAIL (403)
    fake_csv = b"Timestamp,Transaction Type,Asset,Amount\n2025-01-01T00:00:00Z,Buy,BTC,1.0"
    res_upload = client.post(
        "/api/cases/CASE-SAMPLE-2025/sources",
        files={"file": ("extra.csv", fake_csv, "text/csv")},
        data={"source_type": "AUTO"}
    )
    assert res_upload.status_code == 403
    assert "immutable demonstration baselines" in res_upload.json()["detail"]

    # 8. Sample remains unmetered
    assert store.count_billable_cases() == 0


def test_sample_cloning_lifecycle_and_mutation(clean_commercial_env, client):
    """
    REQ-SAM-002 / REQ-COMM-001:
    Cloning an authentic sample creates a new PRODUCTION case that strips bundled provenance,
    consumes capacity, allows full practitioner reviews/notes, and issues revised receipts.
    """
    policy, store, _ = clean_commercial_env

    # 1. Load sample
    client.post("/api/sample-case/load")
    assert store.count_billable_cases() == 0

    # 2. Provision commercial license with capacity = 2
    token = _make_test_token(tier=LicenseTier.PRACTITIONER, max_cases=2)
    policy.install_license_token(token)

    # 3. Clone sample into production case
    res_clone = client.post(
        "/api/cases/CASE-SAMPLE-2025/clone",
        json={"new_case_id": "CASE-CLIENT-001", "client_reference": "Client Engagement 2025"}
    )
    assert res_clone.status_code == 201
    clone_data = res_clone.json()
    assert clone_data["case_id"] == "CASE-CLIENT-001"
    assert clone_data["client_reference"] == "Client Engagement 2025"

    # Verify provenance stripping & capacity metering
    persisted = store.get_case("CASE-CLIENT-001")
    assert persisted.case_kind == "PRODUCTION"
    assert persisted.sample_definition_id is None
    assert persisted.sample_manifest_digest is None
    assert store.count_billable_cases() == 1

    # 4. Reconcile cloned case
    res_recon = client.post("/api/cases/CASE-CLIENT-001/reconcile")
    assert res_recon.status_code == 200
    recon_json = res_recon.json()
    assert recon_json["status"] == "RECONCILED"
    assert recon_json["revision"] == 1
    assert recon_json["human_review_state"] == "UNREVIEWED"

    # 5. Record practitioner reviews and notes on cloned case (MUTATIONS PERMITTED)
    res_review1 = client.post(
        "/api/cases/CASE-CLIENT-001/reviews",
        json={"finding_id": "DIFF-001", "disposition": "REVIEWED", "note": "Reviewed broker vs ledger records."}
    )
    assert res_review1.status_code == 200
    assert res_review1.json()["status"] == "RECORDED"

    res_review2 = client.post(
        "/api/cases/CASE-CLIENT-001/reviews",
        json={"finding_id": "DIFF-002", "disposition": "FOLLOW_UP_REQUIRED", "note": "Requested exchange statement from client."}
    )
    assert res_review2.status_code == 200

    # 6. Finalize practitioner review -> issues Revision 2 Final Receipt
    res_final = client.post(
        "/api/cases/CASE-CLIENT-001/finalize-review",
        json={"reviewer_identity": "CPA Jane Doe", "notes": "Completed preliminary engagement review."}
    )
    assert res_final.status_code == 200
    final_json = res_final.json()
    assert final_json["status"] == "REVIEW_FINALIZED"
    assert final_json["revision"] == 2
    assert final_json["human_review_state"] == "REVIEWED_ANNOTATED"

    # 7. Export evidence package from cloned case
    res_exp = client.get("/api/cases/CASE-CLIENT-001/export")
    assert res_exp.status_code == 200
    assert res_exp.headers["content-type"] == "application/zip"

    # 8. Delete cloned case (PERMITTED for production case)
    res_del = client.delete("/api/cases/CASE-CLIENT-001")
    assert res_del.status_code == 200
    assert store.count_billable_cases() == 0


def test_deterministic_finding_language_safety(clean_commercial_env, client):
    """
    PROD-CONTRACT INVARIANT:
    Deterministic reconciliation findings must contain objective comparison facts
    and neutral professional review guidance.
    Must NOT contain speculative causal hypotheses, tax advice, or prescriptive Form 8949 codes.
    """
    client.post("/api/sample-case/load")
    res_recon = client.post("/api/cases/CASE-SAMPLE-2025/reconcile")
    assert res_recon.status_code == 200
    data = res_recon.json()

    diffs = data["receipt"]["material_differences"]
    descriptions = [d["description"] for d in diffs]
    combined_text = " ".join(descriptions)

    # Prohibited speculative hypotheses & prescriptive advice
    prohibited_phrases = [
        "Potential exchange fee",
        "exchange fee deducted",
        "specific-identification",
        "taxpayer specific-identification",
        "adjust tax lot proceeds",
        "Form 8949 Box B",
        "Code B",
        "declare basis on Form 8949",
        "Uncovered Security",
        "non-covered",
    ]
    for phrase in prohibited_phrases:
        assert phrase.lower() not in combined_text.lower(), f"Prohibited phrase '{phrase}' found in deterministic finding descriptions: {descriptions}"

    # Required neutral review guidance
    assert "Next step: Review" in combined_text or "Next step:" in combined_text

    # Verify specific findings
    avax_diff = next((d for d in diffs if d["asset"] == "AVAX"), None)
    assert avax_diff is not None
    assert "Proceeds differ by $50.00" in avax_diff["description"]
    assert "Broker: $9950.00" in avax_diff["description"]
    assert "Client ledger: $10000.00" in avax_diff["description"]
    assert "Next step: Review the underlying transaction records" in avax_diff["description"]

    btc_diff = next((d for d in diffs if d["asset"] == "BTC"), None)
    assert btc_diff is not None
    assert "Cost basis differs by $4200.00" in btc_diff["description"]
    assert "Broker: $12100.00" in btc_diff["description"]
    assert "Client ledger: $16300.00" in btc_diff["description"]
    assert "Next step: Review supporting basis documentation" in btc_diff["description"]

    sol_diff = next((d for d in diffs if d["asset"] == "SOL"), None)
    assert sol_diff is not None
    assert sol_diff["difference_state"] == "REPORTING_SCOPE_DIFFERENCE"
    assert "Broker did not report basis (Box 2 = NO)" in sol_diff["description"]
    assert "Client ledger reports basis of $4000.00" in sol_diff["description"]
    assert "Next step: Review supporting basis documentation" in sol_diff["description"]
