"""
VaultBasis Quality Suite — ATDD (Acceptance Test-Driven Development)
Simulates end-to-end customer and CPA workflows conforming to PRD §4.1 (CPA JTBD) and §50.4.
"""

from decimal import Decimal
import json
import zipfile
import io
import pytest
from starlette.testclient import TestClient

from edge.api.app import app
from apps.verifier.verify_receipt import verify_outcome_receipt


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.atdd
@pytest.mark.smoke
def test_atdd_cpa_reconciliation_workflow(client):
    """
    Scenario: CPA receives Form 1099-DA from Coinbase and Koinly Report from client.
    1. CPA creates local case 'CASE-CPA-2025-SMITH'.
    2. CPA uploads 1099-DA ($18,400 proceeds, $12,100 basis).
    3. CPA uploads Koinly Report ($18,400 proceeds, $16,300 basis).
    4. CPA triggers deterministic reconciliation.
    5. VaultBasis detects $4,200 basis difference, preserving provenance.
    6. System issues signed Ed25519 Outcome Receipt.
    7. CPA exports ZIP evidence bundle containing receipt, sources, and verifier.
    8. CPA verifies receipt offline with zero external network dependency.
    """
    # Step 1: Create Case
    case_res = client.post("/api/cases", json={
        "case_id": "CASE-CPA-2025-SMITH",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert case_res.status_code in [200, 201]

    # Step 2: Upload 1099-DA
    csv_1099 = b"""Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2
BTC,2025-11-20,18400.00,2025-02-11,12100.00,YES
"""
    up1_res = client.post(
        "/api/cases/CASE-CPA-2025-SMITH/sources",
        files={"file": ("coinbase_1099da.csv", csv_1099, "text/csv")},
        data={"source_type": "AUTO"}
    )
    assert up1_res.status_code == 200

    # Step 3: Upload Koinly Report
    csv_koinly = b"""Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired
2025-11-20,BTC,1.0,16300.00,18400.00,2100.00,2025-02-11
"""
    up2_res = client.post(
        "/api/cases/CASE-CPA-2025-SMITH/sources",
        files={"file": ("koinly_capital_gains.csv", csv_koinly, "text/csv")},
        data={"source_type": "AUTO"}
    )
    assert up2_res.status_code == 200

    # Step 4: Reconcile
    recon_res = client.post("/api/cases/CASE-CPA-2025-SMITH/reconcile")
    assert recon_res.status_code == 200
    recon = recon_res.json()

    # Step 5: Assert findings
    assert recon["outcome_state"] == "BASIS_DIFFERENCE"
    diffs = recon["reconciliation"]["material_differences"]
    assert len(diffs) == 1
    assert diffs[0]["asset"] == "BTC"
    assert diffs[0]["variance"] == "4200.00"

    # Step 6: Verify signed receipt
    receipt = recon["receipt"]
    assert receipt["receipt_version"] == "v0.1"
    assert receipt["signer_type"] == "INSTALLATION_KEY"
    assert receipt["signature"] is not None

    # Step 7: Export Evidence Bundle
    export_res = client.get("/api/cases/CASE-CPA-2025-SMITH/export")
    assert export_res.status_code == 200
    with zipfile.ZipFile(io.BytesIO(export_res.content)) as zf:
        namelist = zf.namelist()
        assert "receipt-v0.1.json" in namelist
        assert "verify_receipt.py" in namelist
        assert "VERIFY_INSTRUCTIONS.txt" in namelist

    # Step 8: Offline Independent Verification
    ver_res = verify_outcome_receipt(receipt)
    assert ver_res.is_valid is True
    assert ver_res.outcome_state == "BASIS_DIFFERENCE"


@pytest.mark.atdd
@pytest.mark.regression
def test_atdd_matched_self_filer_journey(client):
    """
    Scenario: Self-filer with perfectly aligned records between broker and ledger.
    Outcome state must be MATCHED with zero material differences.
    """
    client.post("/api/cases", json={"case_id": "CASE-MATCHED-DEMO", "tax_year": 2025})

    csv_1099 = b"""Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2
ETH,2025-10-15,3500.00,2025-01-10,2500.00,YES
"""
    csv_koinly = b"""Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired
2025-10-15,ETH,1.0,2500.00,3500.00,1000.00,2025-01-10
"""
    client.post("/api/cases/CASE-MATCHED-DEMO/sources", files={"file": ("1099.csv", csv_1099, "text/csv")})
    client.post("/api/cases/CASE-MATCHED-DEMO/sources", files={"file": ("koinly.csv", csv_koinly, "text/csv")})

    recon_res = client.post("/api/cases/CASE-MATCHED-DEMO/reconcile")
    assert recon_res.status_code == 200
    data = recon_res.json()

    assert data["outcome_state"] == "MATCHED"
    assert len(data["reconciliation"]["material_differences"]) == 0
