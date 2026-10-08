import hashlib
import json
import zipfile
import io
from pathlib import Path
from decimal import Decimal
from fastapi.testclient import TestClient

from edge.api.app import app


def test_uat09_missing_from_ledger_orphan():
    """
    Permanent regression test for UAT-09 (Missing from Ledger / Source-A Orphan).
    Validates:
    - 5 Broker transactions and 4 Ledger transactions where 4 match identically and 1 (AVAX) exists only in Broker 1099-DA.
    - Top-level outcome_state == 'MISSING_FROM_LEDGER'
    - 4 agreed records, 1 material difference ('MISSING_FROM_LEDGER'), 0 unresolved items
    - Absence of counterpart is represented faithfully (source_b_ref='NOT_FOUND', source_b_value=None)
    - Zero manufactured $0 values or synthetic taxpayer transactions
    - Difference description contains neutral factual guidance without blaming taxpayer or prescribing tax treatment
    - Receipt contains exactly 1 finding and authentic Ed25519 signature
    - Offline verifier returns PASS with tax correctness limitation disclaimer
    """
    client = TestClient(app)
    case_id = "CASE-UAT09-REGRESSION"

    # Load fixtures
    fixture_dir = Path("tests/fixtures/uat09")
    broker_bytes = (fixture_dir / "broker_orphan.csv").read_bytes()
    ledger_bytes = (fixture_dir / "ledger_orphan.csv").read_bytes()

    # Create Case
    r_create = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-09 Regression Test Case",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201

    # Ingest Source A
    r_src_a = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_orphan.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_a.status_code == 200

    # Ingest Source B
    r_src_b = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_orphan.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_b.status_code == 200

    # Reconcile
    r_recon = client.post(f"/api/cases/{case_id}/reconcile")
    assert r_recon.status_code == 200
    recon_data = r_recon.json().get("reconciliation", {})

    assert recon_data.get("outcome_state") == "MISSING_FROM_LEDGER"
    assert recon_data.get("assurance_level") == "L2_EVIDENCE_RECONCILED"
    assert len(recon_data.get("agreed_records", [])) == 4
    assert len(recon_data.get("material_differences", [])) == 1
    assert len(recon_data.get("unresolved_items", [])) == 0
    assert recon_data.get("comparison_group_count") == 5
    assert recon_data.get("matched_group_count") == 4
    assert recon_data.get("source_a_row_count") == 5
    assert recon_data.get("source_b_row_count") == 4

    diff = recon_data.get("material_differences")[0]
    assert diff.get("asset") == "AVAX"
    assert diff.get("difference_state") == "MISSING_FROM_LEDGER"
    assert diff.get("source_a_value") == "9950.00"
    assert diff.get("source_b_ref") == "NOT_FOUND"
    assert diff.get("source_b_value") is None
    assert "present in broker Form 1099-DA" in diff.get("description")
    assert "missing from tax ledger" in diff.get("description")
    assert "forgot" not in diff.get("description").lower()
    assert "incomplete" not in diff.get("description").lower()
    assert "form 8949" not in diff.get("description").lower()
    assert "gain" not in diff.get("description").lower()

    # Export & Verify
    r_export = client.get(f"/api/cases/{case_id}/export")
    assert r_export.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_export.content)) as z:
        receipt_bytes = z.read("receipt-v0.1.json")
        receipt_json = json.loads(receipt_bytes.decode("utf-8"))
        assert receipt_json.get("outcome_state") == "MISSING_FROM_LEDGER"
        assert len(receipt_json.get("material_differences", [])) == 1

        rec_diff = receipt_json.get("material_differences")[0]
        assert rec_diff.get("difference_state") == "MISSING_FROM_LEDGER"
        assert rec_diff.get("source_b_ref") == "NOT_FOUND"
        assert rec_diff.get("source_b_value") is None

        # Verify offline
        r_verify = client.post("/api/receipts/verify", files={"file": ("receipt-v0.1.json", receipt_bytes, "application/json")})
        assert r_verify.status_code == 200
        verify_data = r_verify.json()
        assert verify_data.get("overall_status") == "PASS"
        assert verify_data.get("is_valid") is True
        assert verify_data.get("checks", {}).get("signature_authenticity") == "PASS"
        assert verify_data.get("checks", {}).get("tax_correctness") == "NOT_DETERMINED"
