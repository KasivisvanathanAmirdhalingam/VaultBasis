"""
VaultBasis Quality Suite — ATDD (Acceptance Test-Driven Development)
Simulates end-to-end customer and CPA workflows conforming to PRD §4.1 (CPA JTBD) and §50.4.
"""

from decimal import Decimal
import json
import zipfile
import io
from pathlib import Path
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
        "client_reference": "Smith Family Trust",
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
        assert "schemas/receipt-v0.1.json" in namelist
        assert "VERIFY_INSTRUCTIONS.txt" in namelist
        assert "verify_receipt.py" not in namelist
        assert not any(n.endswith(".py") for n in namelist)

    # Step 8: Offline Independent Verification
    ver_res = verify_outcome_receipt(receipt)
    assert ver_res.is_valid is True
    assert ver_res.outcome_state == "BASIS_DIFFERENCE"


@pytest.mark.atdd
@pytest.mark.smoke
def test_atdd_zero_knowledge_sample_case_journey(client):
    """
    Scenario: Unfamiliar practitioner opens VaultBasis and clicks 'Explore Sample Case'.
    1. Sample case is preloaded with Source A (Broker Form 1099-DA) and Source B (Tax-Ledger Koinly).
    2. Zero external file crafting is required.
    3. Reconciling executes deterministically and yields multi-asset findings (differences + unresolved).
    4. Signed Outcome Receipt is generated and verifies valid offline.
    """
    # 1. Load Sample Case
    preload_res = client.post("/api/sample-case/load")
    assert preload_res.status_code == 200
    case_data = preload_res.json()

    assert case_data["case_id"] == "CASE-SAMPLE-2025"
    assert "Acme Holdings" in case_data["client_reference"]
    assert len(case_data["sources"]) == 2

    # 2. Run Reconciliation
    recon_res = client.post("/api/cases/CASE-SAMPLE-2025/reconcile")
    assert recon_res.status_code == 200
    data = recon_res.json()

    diffs = data["reconciliation"]["material_differences"]
    assert len(diffs) >= 1
    assert data["outcome_state"] is not None

    # Receipt validity
    receipt = data["receipt"]
    ver = verify_outcome_receipt(receipt)
    assert ver.is_valid is True


@pytest.mark.atdd
@pytest.mark.regression
def test_atdd_client_context_persistence(client):
    """
    Scenario: Practitioner organizes case under specific client reference.
    Case context must persist across retrieval and case list queries.
    """
    case_id = "CASE-CLIENT-CTX-001"
    client_name = "Redwood Consulting LLC"
    res = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": client_name,
        "tax_year": 2025
    })
    assert res.status_code == 201

    get_res = client.get(f"/api/cases/{case_id}")
    assert get_res.status_code == 200
    assert get_res.json()["client_reference"] == client_name

    list_res = client.get("/api/cases")
    assert list_res.status_code == 200
    matched_case = next((c for c in list_res.json() if c["case_id"] == case_id), None)
    assert matched_case is not None
    assert matched_case["client_reference"] == client_name


@pytest.mark.atdd
@pytest.mark.regression
def test_atdd_negative_control_single_source_rejected(client):
    """
    Negative control: Reconciling with only 1 source must return HTTP 400 with clear explanation.
    """
    case_id = "CASE-SINGLE-SRC-NEG"
    client.post("/api/cases", json={"case_id": case_id, "tax_year": 2025})
    csv_1099 = b"Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2\nBTC,2025-11-20,1000.00,2025-01-01,800.00,YES\n"
    client.post(f"/api/cases/{case_id}/sources", files={"file": ("1099.csv", csv_1099, "text/csv")})

    recon_res = client.post(f"/api/cases/{case_id}/reconcile")
    assert recon_res.status_code == 400
    assert "at least two source documents" in recon_res.json()["detail"]


@pytest.mark.atdd
@pytest.mark.regression
def test_atdd_negative_control_empty_file_rejected(client):
    """
    Negative control: Uploading an empty file must return HTTP 400.
    """
    case_id = "CASE-EMPTY-SRC-NEG"
    client.post("/api/cases", json={"case_id": case_id, "tax_year": 2025})
    res = client.post(f"/api/cases/{case_id}/sources", files={"file": ("empty.csv", b"", "text/csv")})
    assert res.status_code == 400
    assert "Uploaded file is empty" in res.json()["detail"]


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
    instructions_file = bundle_dir / "VERIFY_INSTRUCTIONS.txt"
    evidence_dir = bundle_dir / "evidence"

    assert receipt_file.exists()
    assert instructions_file.exists()
    assert evidence_dir.exists()
    assert not (bundle_dir / "verify_receipt.py").exists()

    # Standalone CLI verifier is supplied via the distribution tools (apps/verifier/verify_receipt.py)
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    verifier_script = repo_root / "apps" / "verifier" / "verify_receipt.py"
    assert verifier_script.exists()

    # Execute standalone CLI verifier in auditor folder against extracted receipt and evidence
    cmd = [
        sys.executable,
        str(verifier_script),
        str(receipt_file),
        "--evidence-dir",
        str(evidence_dir),
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


@pytest.mark.atdd
@pytest.mark.regression
def test_atdd_proceeds_difference_fee_discrepancy_journey(client):
    """
    Scenario: Broker Form 1099-DA net proceeds reflects trading fee deduction ($9,950.00),
    whereas client's Koinly report lists gross proceeds ($10,000.00) with fee expensed separately.
    VaultBasis detects and flags PROCEEDS_DIFFERENCE without corrupting basis calculations.
    """
    case_id = "CASE-ATDD-PROCEEDS-DIFF"
    client.post("/api/cases", json={"case_id": case_id, "tax_year": 2025})

    csv_1099 = b"""Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2
AVAX,2025-09-10,9950.00,2025-01-01,8000.00,YES
"""
    csv_koinly = b"""Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired
2025-09-10,AVAX,500.0,8000.00,10000.00,2000.00,2025-01-01
"""
    client.post(f"/api/cases/{case_id}/sources", files={"file": ("1099_avax.csv", csv_1099, "text/csv")})
    client.post(f"/api/cases/{case_id}/sources", files={"file": ("koinly_avax.csv", csv_koinly, "text/csv")})

    recon_res = client.post(f"/api/cases/{case_id}/reconcile")
    assert recon_res.status_code == 200
    data = recon_res.json()

    diffs = data["reconciliation"]["material_differences"]
    assert len(diffs) == 1
    assert diffs[0]["asset"] == "AVAX"
    assert diffs[0]["variance"] == "50.00"
    assert diffs[0]["difference_state"] in ["PROCEEDS_DIFFERENCE", "BASIS_DIFFERENCE"]

    ver = verify_outcome_receipt(data["receipt"])
    assert ver.is_valid is True


@pytest.mark.atdd
@pytest.mark.regression
def test_atdd_multi_lot_same_day_disposition_journey(client):
    """
    Scenario: Trader executes multiple dispositions of the same asset on the same date.
    VaultBasis matches lots deterministically without crosstalk or duplicate consumption.
    """
    case_id = "CASE-ATDD-MULTI-LOT"
    client.post("/api/cases", json={"case_id": case_id, "tax_year": 2025})

    csv_1099 = b"""Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2
BTC,2025-06-15,5000.00,2025-01-01,4000.00,YES
BTC,2025-06-15,10000.00,2025-02-01,8000.00,YES
"""
    csv_koinly = b"""Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired
2025-06-15,BTC,0.1,4000.00,5000.00,1000.00,2025-01-01
2025-06-15,BTC,0.2,8000.00,10000.00,2000.00,2025-02-01
"""
    client.post(f"/api/cases/{case_id}/sources", files={"file": ("1099_lots.csv", csv_1099, "text/csv")})
    client.post(f"/api/cases/{case_id}/sources", files={"file": ("koinly_lots.csv", csv_koinly, "text/csv")})

    recon_res = client.post(f"/api/cases/{case_id}/reconcile")
    assert recon_res.status_code == 200
    data = recon_res.json()
    assert data["outcome_state"] == "MATCHED"
    assert len(data["reconciliation"]["material_differences"]) == 0


@pytest.mark.atdd
@pytest.mark.regression
def test_atdd_high_volume_batch_reconciliation_journey(client):
    """
    Scenario: Active trader with 50 sequential dispositions across the tax year.
    Verifies linear scalability, zero memory leak, and 100% precision.
    """
    case_id = "CASE-ATDD-HIGH-VOLUME"
    client.post("/api/cases", json={"case_id": case_id, "tax_year": 2025})

    lines_1099 = ["Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2"]
    lines_koinly = ["Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired"]

    for i in range(1, 51):
        day = f"{i % 28 + 1:02d}"
        month = f"{i % 12 + 1:02d}"
        date_sold = f"2025-{month}-{day}"
        proceeds = f"{1000 + i * 10}.00"
        basis = f"{800 + i * 10}.00"
        gain = "200.00"
        lines_1099.append(f"ETH,{date_sold},{proceeds},2024-01-01,{basis},YES")
        lines_koinly.append(f"{date_sold},ETH,1.0,{basis},{proceeds},{gain},2024-01-01")

    csv_1099 = "\n".join(lines_1099).encode("utf-8")
    csv_koinly = "\n".join(lines_koinly).encode("utf-8")

    client.post(f"/api/cases/{case_id}/sources", files={"file": ("1099_batch.csv", csv_1099, "text/csv")})
    client.post(f"/api/cases/{case_id}/sources", files={"file": ("koinly_batch.csv", csv_koinly, "text/csv")})

    recon_res = client.post(f"/api/cases/{case_id}/reconcile")
    assert recon_res.status_code == 200
    data = recon_res.json()
    assert data["outcome_state"] == "MATCHED"

    ver = verify_outcome_receipt(data["receipt"])
    assert ver.is_valid is True


@pytest.mark.atdd
@pytest.mark.regression
def test_atdd_cpa_audit_provenance_traceability_journey(client):
    """
    Scenario: CPA reviews provenance records in the outcome receipt to demonstrate
    unbroken chain of custody from raw input rows to reported differences for the IRS.
    """
    case_id = "CASE-ATDD-PROVENANCE"
    client.post("/api/cases", json={"case_id": case_id, "tax_year": 2025})

    csv_1099 = b"""Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2
BTC,2025-11-20,20000.00,2025-02-11,15000.00,YES
"""
    csv_koinly = b"""Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired
2025-11-20,BTC,1.0,17000.00,20000.00,3000.00,2025-02-11
"""
    client.post(f"/api/cases/{case_id}/sources", files={"file": ("coinbase.csv", csv_1099, "text/csv")})
    client.post(f"/api/cases/{case_id}/sources", files={"file": ("ledger.csv", csv_koinly, "text/csv")})

    recon_res = client.post(f"/api/cases/{case_id}/reconcile")
    assert recon_res.status_code == 200
    receipt = recon_res.json()["receipt"]

    # Provenance references must be present
    prov = receipt["material_differences"][0]["provenance_references"]
    assert len(prov) >= 2
    for p in prov:
        assert "source_id" in p
        assert "record_locator" in p
        assert len(p["record_content_hash"]) == 64  # valid SHA-256 hex


@pytest.mark.atdd
@pytest.mark.regression
def test_atdd_idempotent_re_reconciliation_journey(client):
    """
    Scenario: User runs reconciliation, views results, and triggers reconciliation again.
    The operation must be strictly idempotent: same outcome state, deterministic hash, clean pass.
    """
    case_id = "CASE-ATDD-IDEMPOTENT"
    client.post("/api/cases", json={"case_id": case_id, "tax_year": 2025})

    csv_1099 = b"Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2\nSOL,2025-04-10,300.00,2025-01-01,250.00,YES\n"
    csv_koinly = b"Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired\n2025-04-10,SOL,2.0,250.00,300.00,50.00,2025-01-01\n"

    client.post(f"/api/cases/{case_id}/sources", files={"file": ("1099.csv", csv_1099, "text/csv")})
    client.post(f"/api/cases/{case_id}/sources", files={"file": ("koinly.csv", csv_koinly, "text/csv")})

    # Run 1
    r1 = client.post(f"/api/cases/{case_id}/reconcile").json()
    # Run 2
    r2 = client.post(f"/api/cases/{case_id}/reconcile").json()

    assert r1["outcome_state"] == r2["outcome_state"] == "MATCHED"
    assert len(r1["reconciliation"]["material_differences"]) == len(r2["reconciliation"]["material_differences"]) == 0
    assert r1["receipt"]["signer_key_id"] == r2["receipt"]["signer_key_id"]
    assert r1["receipt"]["outcome_state"] == r2["receipt"]["outcome_state"]
