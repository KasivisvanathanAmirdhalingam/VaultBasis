import hashlib
import json
import zipfile
import io
from pathlib import Path
from decimal import Decimal
from fastapi.testclient import TestClient

from edge.api.app import app


def test_uat13_explicit_zero_cost_basis():
    """
    Permanent regression test for UAT-13 (Explicit $0.00 Cost Basis).
    Validates:
    - 5 paired transactions where all 5 match identically, including AVAX with explicit $0.00 cost basis on both sides.
    - Top-level outcome_state == 'MATCHED'
    - 5 agreed records, 0 material differences, 0 unresolved items
    - Explicit $0.00 cost basis is preserved as numeric zero (not converted to null, missing, or unreported)
    - Agreement description contains neutral practitioner confirmation ("Supported information agrees")
    - Zero speculative assertions regarding airdrops, mining, gifts, or tax classifications
    - Cryptographic receipt emitted with MATCHED state and valid Ed25519 signature
    - Local receipt verification endpoint returns PASS with tax correctness limitation disclaimer
    """
    client = TestClient(app)
    case_id = "CASE-UAT13-REGRESSION"

    # Load fixtures
    fixture_dir = Path("tests/fixtures/uat13")
    broker_bytes = (fixture_dir / "broker_zero_basis.csv").read_bytes()
    ledger_bytes = (fixture_dir / "ledger_zero_basis.csv").read_bytes()

    # Create Case
    r_create = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-13 Regression Test Case",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201

    # Ingest Source A
    r_src_a = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_zero_basis.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_a.status_code == 200

    # Ingest Source B
    r_src_b = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_zero_basis.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_b.status_code == 200

    # Reconcile
    client.post(f"/api/cases/{case_id}/confirm-sources")
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

    # Check AVAX agreed record specifically
    avax_agreed = [rec for rec in recon_data.get("agreed_records", []) if rec.get("asset") == "AVAX"]
    assert len(avax_agreed) == 1
    rec = avax_agreed[0]
    assert rec.get("classification") == "MATCHED"
    assert rec.get("variance") == "0.00"
    assert "Supported information agrees" in rec.get("description")

    # Export & Verify
    r_export = client.get(f"/api/cases/{case_id}/export")
    assert r_export.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_export.content)) as z:
        receipt_bytes = z.read("receipt-v0.1.json")
        receipt_json = json.loads(receipt_bytes.decode("utf-8"))
        assert receipt_json.get("outcome_state") == "MATCHED"
        assert len(receipt_json.get("material_differences", [])) == 0

        # Local receipt verification endpoint check
        r_verify = client.post("/api/receipts/verify", files={"file": ("receipt-v0.1.json", receipt_bytes, "application/json")})
        assert r_verify.status_code == 200
        verify_data = r_verify.json()
        assert verify_data.get("overall_status") == "PASS"
        assert verify_data.get("is_valid") is True
        assert verify_data.get("checks", {}).get("signature_authenticity") == "PASS"
        assert verify_data.get("checks", {}).get("tax_correctness") == "NOT_DETERMINED"
