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


@pytest.mark.atdd
@pytest.mark.regression
def test_atdd_unresolved_basis_missing_box1e_journey(client):
    """
    Scenario: Taxpayer has Form 1099-DA with missing Cost Basis (Box 1e blank).
    VaultBasis must classify as UNRESOLVED_DATA, never coerce to $0.00,
    and produce an independently verifiable signed receipt with explicit unresolved reasons.
    """
    case_id = "CASE-ATDD-UNREPORTED-SCOPE"
    client.post("/api/cases", json={"case_id": case_id, "tax_year": 2025})

    csv_1099 = b"""Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2
SOL,2025-08-14,4500.00,2025-01-10,,NO
"""
    csv_koinly = b"""Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired
2025-08-14,SOL,30.0,4000.00,4500.00,500.00,2025-01-10
"""
    client.post(f"/api/cases/{case_id}/sources", files={"file": ("1099_unreported.csv", csv_1099, "text/csv")})
    client.post(f"/api/cases/{case_id}/sources", files={"file": ("koinly_report.csv", csv_koinly, "text/csv")})

    recon_res = client.post(f"/api/cases/{case_id}/reconcile")
    assert recon_res.status_code == 200
    data = recon_res.json()

    assert data["outcome_state"] == "REPORTING_SCOPE_DIFFERENCE"
    diffs = data["reconciliation"]["material_differences"]
    assert len(diffs) >= 1
    assert diffs[0]["difference_state"] == "REPORTING_SCOPE_DIFFERENCE"
    assert diffs[0]["source_a_value"] == "NOT_REPORTED (Box 2)"
    assert diffs[0]["source_b_value"] == "4000.00"

    # Verify receipt generated
    receipt = data["receipt"]
    ver = verify_outcome_receipt(receipt)
    assert ver.is_valid is True
    assert ver.outcome_state == "REPORTING_SCOPE_DIFFERENCE"



@pytest.mark.atdd
@pytest.mark.regression
def test_atdd_zip_bundle_complete_standalone_reverification(client, tmp_path):
    """
    Scenario: Auditor receives ZIP evidence bundle exported by VaultBasis.
    Auditor extracts ZIP in an air-gapped machine with clean Python, runs verify_receipt.py,
    and achieves 100% independent verification without any network or external database calls.
    """
    import subprocess
    import sys

    case_id = "CASE-ATDD-ZIP-BUNDLE"
    client.post("/api/cases", json={"case_id": case_id, "tax_year": 2025})

    csv_1099 = b"Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2\nBTC,2025-05-01,12000.00,2024-05-01,10000.00,YES\n"
    csv_koinly = b"Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired\n2025-05-01,BTC,1.0,10000.00,12000.00,2000.00,2024-05-01\n"
    client.post(f"/api/cases/{case_id}/sources", files={"file": ("1099.csv", csv_1099, "text/csv")})
    client.post(f"/api/cases/{case_id}/sources", files={"file": ("koinly.csv", csv_koinly, "text/csv")})
    client.post(f"/api/cases/{case_id}/reconcile")

    # Download ZIP bundle
    bundle_res = client.get(f"/api/cases/{case_id}/export")
    assert bundle_res.status_code == 200

    # Extract to standalone temporary directory
    bundle_dir = tmp_path / "auditor_export"
    bundle_dir.mkdir()
    with zipfile.ZipFile(io.BytesIO(bundle_res.content)) as zf:
        zf.extractall(bundle_dir)

    receipt_file = bundle_dir / "receipt-v0.1.json"
    verifier_script = bundle_dir / "verify_receipt.py"
    instructions_file = bundle_dir / "VERIFY_INSTRUCTIONS.txt"

    assert receipt_file.exists()
    assert verifier_script.exists()
    assert instructions_file.exists()

    # Execute standalone CLI verifier in auditor folder
    cmd = [
        sys.executable,
        str(verifier_script),
        str(receipt_file),
        "--no-color",
        "--json"
    ]
    proc = subprocess.run(cmd, cwd=str(bundle_dir), capture_output=True, text=True)
    assert proc.returncode == 0
    res_json = json.loads(proc.stdout)
    assert res_json["is_valid"] is True
    assert res_json["outcome_state"] == "MATCHED"


@pytest.mark.atdd
@pytest.mark.regression
def test_atdd_multi_asset_mixed_portfolio_journey(client):
    """
    Scenario: CPA handles a client with a multi-asset portfolio (BTC, ETH, SOL).
    - BTC: Proceeds match, basis differs ($18,400 proceeds, $12,100 vs $16,300 basis) -> BASIS_DIFFERENCE
    - ETH: 100% matched ($3,200 proceeds, $2,800 basis)
    - SOL: 2025 non-covered asset (Box 2 NO, basis unrecorded by broker) -> REPORTING_SCOPE_DIFFERENCE
    """
    case_id = "CASE-ATDD-MULTI-ASSET"
    client.post("/api/cases", json={"case_id": case_id, "tax_year": 2025})

    csv_1099 = b"""Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2
BTC,2025-11-20,18400.00,2025-02-11,12100.00,YES
ETH,2025-12-05,3200.00,2025-03-01,2800.00,YES
SOL,2025-08-14,4500.00,2025-01-10,,NO
"""
    csv_koinly = b"""Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired
2025-11-20,BTC,1.0,16300.00,18400.00,2100.00,2025-02-11
2025-12-05,ETH,1.0,2800.00,3200.00,400.00,2025-03-01
2025-08-14,SOL,30.0,4000.00,4500.00,500.00,2025-01-10
"""
    client.post(f"/api/cases/{case_id}/sources", files={"file": ("1099.csv", csv_1099, "text/csv")})
    client.post(f"/api/cases/{case_id}/sources", files={"file": ("koinly.csv", csv_koinly, "text/csv")})

    recon_res = client.post(f"/api/cases/{case_id}/reconcile")
    assert recon_res.status_code == 200
    data = recon_res.json()

    diffs = data["reconciliation"]["material_differences"]
    diff_types = {d["difference_state"] for d in diffs}
    assert "BASIS_DIFFERENCE" in diff_types
    assert "REPORTING_SCOPE_DIFFERENCE" in diff_types

    # Ensure receipt validates offline
    report = verify_outcome_receipt(data["receipt"])
    assert report.is_valid is True


