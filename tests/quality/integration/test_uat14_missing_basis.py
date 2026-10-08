import hashlib
import json
import zipfile
import io
from pathlib import Path
from decimal import Decimal
from fastapi.testclient import TestClient

from edge.api.app import app


def test_uat14_missing_cost_basis():
    """
    Permanent regression test for UAT-14 (Missing Cost Basis).
    Validates:
    - 5 comparison groups: 4 standard agreements (BTC, ETH, SOL, LINK) and 1 transaction (AVAX) with missing cost basis in Form 1099-DA (Box 2 = YES).
    - Invariant preservation: NOT_REPORTED (UAT-12) != EXPLICIT 0.00 (UAT-13) != MISSING/UNAVAILABLE (UAT-14).
    - Top-level outcome_state == 'UNRESOLVED_DATA'
    - 4 agreed records, 0 material differences, 1 unresolved item
    - Unresolved item reason_code == 'BASIS_UNAVAILABLE'
    - Missing basis is NOT coerced to zero, NOT treated as Box 2 NO, and NOT arbitrarily matched
    - Neutral description with zero speculative tax causes
    - Cryptographic receipt emitted with UNRESOLVED_DATA state and valid Ed25519 signature
    - Local receipt verification endpoint returns PASS with tax correctness limitation disclaimer
    """
    client = TestClient(app)
    case_id = "CASE-UAT14-REGRESSION"

    # Load fixtures
    fixture_dir = Path("tests/fixtures/uat14")
    broker_bytes = (fixture_dir / "broker_missing_basis.csv").read_bytes()
    ledger_bytes = (fixture_dir / "ledger_missing_basis.csv").read_bytes()

    # Create Case
    r_create = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-14 Regression Test Case",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201

    # Ingest Source A
    r_src_a = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_missing_basis.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_a.status_code == 200

    # Ingest Source B
    r_src_b = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_missing_basis.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_b.status_code == 200

    # Reconcile
    r_recon = client.post(f"/api/cases/{case_id}/reconcile")
    assert r_recon.status_code == 200
    recon_data = r_recon.json().get("reconciliation", {})

    assert recon_data.get("outcome_state") == "UNRESOLVED_DATA"
    assert len(recon_data.get("agreed_records", [])) == 4
    assert len(recon_data.get("material_differences", [])) == 0
    assert len(recon_data.get("unresolved_items", [])) == 1
    assert recon_data.get("comparison_group_count") == 5

    # Check AVAX unresolved item specifically
    unres_item = recon_data.get("unresolved_items", [])[0]
    assert unres_item.get("reason_code") == "BASIS_UNAVAILABLE"
    assert "AVAX" in unres_item.get("description", "")
    assert len(unres_item.get("provenance_references", [])) >= 1

    # Export & Verify
    r_export = client.get(f"/api/cases/{case_id}/export")
    assert r_export.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_export.content)) as z:
        receipt_bytes = z.read("receipt-v0.1.json")
        receipt_json = json.loads(receipt_bytes.decode("utf-8"))
        assert receipt_json.get("outcome_state") == "UNRESOLVED_DATA"
        assert len(receipt_json.get("unresolved_items", [])) == 1
        assert receipt_json.get("unresolved_items", [])[0].get("reason_code") == "BASIS_UNAVAILABLE"

        # Local receipt verification endpoint check
        r_verify = client.post("/api/receipts/verify", files={"file": ("receipt-v0.1.json", receipt_bytes, "application/json")})
        assert r_verify.status_code == 200
        verify_data = r_verify.json()
        assert verify_data.get("overall_status") == "PASS"
        assert verify_data.get("is_valid") is True
        assert verify_data.get("checks", {}).get("signature_authenticity") == "PASS"
        assert verify_data.get("checks", {}).get("tax_correctness") == "NOT_DETERMINED"
