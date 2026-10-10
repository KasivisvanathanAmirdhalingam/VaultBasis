import hashlib
import json
import zipfile
import io
from pathlib import Path
from decimal import Decimal
from fastapi.testclient import TestClient

from edge.api.app import app


def test_uat12_form1099da_box2_unreported_basis():
    """
    Permanent regression test for UAT-12 (Form 1099-DA Box 2 = NO / Unreported Basis).
    Validates:
    - 5 paired transactions where 4 match identically and exactly 1 (AVAX) has Box 2 = NO with basis unreported by broker.
    - Top-level outcome_state == 'REPORTING_SCOPE_DIFFERENCE'
    - 4 agreed records, 1 material difference ('REPORTING_SCOPE_DIFFERENCE'), 0 basis diffs, 0 proceeds diffs, 0 unresolved items
    - Difference record does NOT coerce broker basis to $0.00 (source_a_value == 'NOT_REPORTED (Box 2)')
    - Difference record reports ledger basis of $8000.00 (source_b_value == '8000.00')
    - Difference description contains neutral next-step guidance without speculative securities classifications (e.g. 'uncovered security')
    - Receipt contains exactly 1 finding and authentic Ed25519 signature
    - Offline verifier returns PASS with tax correctness limitation disclaimer
    """
    client = TestClient(app)
    case_id = "CASE-UAT12-REGRESSION"

    # Load fixtures
    fixture_dir = Path("tests/fixtures/uat12")
    broker_bytes = (fixture_dir / "broker_box2_no.csv").read_bytes()
    ledger_bytes = (fixture_dir / "ledger_box2_no.csv").read_bytes()

    # Create Case
    r_create = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-12 Regression Test Case",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201

    # Ingest Source A
    r_src_a = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_box2_no.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_a.status_code == 200

    # Ingest Source B
    r_src_b = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_box2_no.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_b.status_code == 200

    # Reconcile
    client.post(f"/api/cases/{case_id}/confirm-sources")
    r_recon = client.post(f"/api/cases/{case_id}/reconcile")
    assert r_recon.status_code == 200
    recon_data = r_recon.json().get("reconciliation", {})

    assert recon_data.get("outcome_state") == "REPORTING_SCOPE_DIFFERENCE"
    assert recon_data.get("assurance_level") == "L2_EVIDENCE_RECONCILED"
    assert len(recon_data.get("agreed_records", [])) == 4
    assert len(recon_data.get("material_differences", [])) == 1
    assert len(recon_data.get("unresolved_items", [])) == 0
    assert recon_data.get("comparison_group_count") == 5
    assert recon_data.get("matched_group_count") == 4

    diff = recon_data.get("material_differences")[0]
    assert diff.get("asset") == "AVAX"
    assert diff.get("difference_state") == "REPORTING_SCOPE_DIFFERENCE"
    assert diff.get("source_a_value") == "NOT_REPORTED (Box 2)"
    assert diff.get("source_b_value") == "8000.00"
    assert diff.get("variance") is None
    assert "Broker did not report basis (Box 2 = NO)" in diff.get("description")
    assert "Client ledger reports basis of $8000.00" in diff.get("description")
    assert "uncovered security" not in diff.get("description").lower()
    assert "covered security" not in diff.get("description").lower()
    assert "form 8949" not in diff.get("description").lower()

    # Export & Verify
    r_export = client.get(f"/api/cases/{case_id}/export")
    assert r_export.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_export.content)) as z:
        receipt_bytes = z.read("receipt-v0.1.json")
        receipt_json = json.loads(receipt_bytes.decode("utf-8"))
        assert receipt_json.get("outcome_state") == "REPORTING_SCOPE_DIFFERENCE"
        assert len(receipt_json.get("material_differences", [])) == 1

        # Verify offline
        r_verify = client.post("/api/receipts/verify", files={"file": ("receipt-v0.1.json", receipt_bytes, "application/json")})
        assert r_verify.status_code == 200
        verify_data = r_verify.json()
        assert verify_data.get("overall_status") == "PASS"
        assert verify_data.get("is_valid") is True
        assert verify_data.get("checks", {}).get("signature_authenticity") == "PASS"
        assert verify_data.get("checks", {}).get("tax_correctness") == "NOT_DETERMINED"
