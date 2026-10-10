import hashlib
import json
import zipfile
import io
from pathlib import Path
from decimal import Decimal
from fastapi.testclient import TestClient

from edge.api.app import app
from schemas.canonical.case import CanonicalCase


def test_uat05_perfect_agreement_reconciliation():
    """
    Permanent regression test for UAT-05 (Perfect Agreement / DATA-01).
    Validates:
    - 5 identical broker vs ledger transactions (BTC, ETH, SOL, LINK, AVAX)
    - 5 paired groups, 5 agreed records, 0 material differences, 0 unresolved items
    - Top-level outcome state == 'MATCHED'
    - Receipt generation with 0 findings and authentic Ed25519 signature
    - Offline verifier returns PASS with tax correctness disclaimer
    """
    client = TestClient(app)
    case_id = "CASE-UAT05-REGRESSION"

    # Load fixtures
    fixture_dir = Path("tests/fixtures/uat05")
    broker_bytes = (fixture_dir / "broker_perfect.csv").read_bytes()
    ledger_bytes = (fixture_dir / "ledger_perfect.csv").read_bytes()

    # Create Case
    r_create = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-05 Regression Test Case",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201

    # Ingest Source A
    r_src_a = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_perfect.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_a.status_code == 200

    # Ingest Source B
    r_src_b = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_perfect.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_b.status_code == 200

    # Confirm Sources (CASE-SOURCE-001)
    r_conf = client.post(f"/api/cases/{case_id}/confirm-sources")
    assert r_conf.status_code == 200

    # Reconcile
    r_recon = client.post(f"/api/cases/{case_id}/reconcile")
    assert r_recon.status_code == 200
    recon_data = r_recon.json().get("reconciliation", {})

    assert recon_data.get("outcome_state") == "MATCHED"
    assert recon_data.get("assurance_level") == "L2_EVIDENCE_RECONCILED"
    assert len(recon_data.get("agreed_records", [])) == 5
    assert len(recon_data.get("material_differences", [])) == 0
    assert len(recon_data.get("unresolved_items", [])) == 0
    assert recon_data.get("comparison_group_count") == 5
    assert recon_data.get("matched_group_count") == 5

    # Export & Verify
    r_export = client.get(f"/api/cases/{case_id}/export")
    assert r_export.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_export.content)) as z:
        receipt_bytes = z.read("receipt-v0.1.json")
        receipt_json = json.loads(receipt_bytes.decode("utf-8"))
        assert receipt_json.get("outcome_state") == "MATCHED"
        assert len(receipt_json.get("material_differences", [])) == 0
        assert receipt_json.get("human_review_state") == "UNREVIEWED"

        # Verify offline
        r_verify = client.post("/api/receipts/verify", files={"file": ("receipt-v0.1.json", receipt_bytes, "application/json")})
        assert r_verify.status_code == 200
        verify_data = r_verify.json()
        assert verify_data.get("overall_status") == "PASS"
        assert verify_data.get("is_valid") is True
        assert verify_data.get("checks", {}).get("signature_authenticity") == "PASS"
        assert verify_data.get("checks", {}).get("tax_correctness") == "NOT_DETERMINED"
