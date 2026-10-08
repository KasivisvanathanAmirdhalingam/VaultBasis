import hashlib
import json
import zipfile
import io
from pathlib import Path
from decimal import Decimal
from fastapi.testclient import TestClient

from edge.api.app import app


def test_uat08_simultaneous_proceeds_and_basis_difference():
    """
    Permanent regression test for UAT-08 (Simultaneous Proceeds & Basis Differences).
    Validates:
    - 5 paired transactions where 4 match identically and exactly 1 (AVAX) differs in both proceeds ($9,950.00 vs $10,000.00) and cost basis ($8,000.00 vs $8,050.00).
    - Top-level outcome_state evaluates per canonical precedence ('PROCEEDS_DIFFERENCE')
    - 4 agreed records, 2 material difference records (1 proceeds diff + 1 basis diff), 0 unresolved items
    - 1 affected transaction pair with both dimensions independently captured (zero arithmetic cancellation)
    - Difference descriptions contain neutral next-step guidance without speculative fee or tax hypotheses
    - Receipt contains exactly 2 findings and authentic Ed25519 signature
    - Offline verifier returns PASS with tax correctness limitation disclaimer
    """
    client = TestClient(app)
    case_id = "CASE-UAT08-REGRESSION"

    # Load fixtures
    fixture_dir = Path("tests/fixtures/uat08")
    broker_bytes = (fixture_dir / "broker_dual_diff.csv").read_bytes()
    ledger_bytes = (fixture_dir / "ledger_dual_diff.csv").read_bytes()

    # Create Case
    r_create = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-08 Regression Test Case",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201

    # Ingest Source A
    r_src_a = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_dual_diff.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_a.status_code == 200

    # Ingest Source B
    r_src_b = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_dual_diff.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_b.status_code == 200

    # Reconcile
    r_recon = client.post(f"/api/cases/{case_id}/reconcile")
    assert r_recon.status_code == 200
    recon_data = r_recon.json().get("reconciliation", {})

    assert recon_data.get("outcome_state") == "PROCEEDS_DIFFERENCE"
    assert recon_data.get("assurance_level") == "L2_EVIDENCE_RECONCILED"
    assert len(recon_data.get("agreed_records", [])) == 4
    assert len(recon_data.get("material_differences", [])) == 2
    assert len(recon_data.get("unresolved_items", [])) == 0
    assert recon_data.get("comparison_group_count") == 5
    assert recon_data.get("matched_group_count") == 4

    diffs = recon_data.get("material_differences")
    diff_states = [d.get("difference_state") for d in diffs]
    assert "PROCEEDS_DIFFERENCE" in diff_states
    assert "BASIS_DIFFERENCE" in diff_states

    # Check proceeds diff
    p_diff = next(d for d in diffs if d.get("difference_state") == "PROCEEDS_DIFFERENCE")
    assert p_diff.get("asset") == "AVAX"
    assert p_diff.get("source_a_value") == "9950.00"
    assert p_diff.get("source_b_value") == "10000.00"
    assert p_diff.get("variance") == "50.00"
    assert "Proceeds differ by $50.00" in p_diff.get("description")
    assert "fee" not in p_diff.get("description").lower()
    assert "commission" not in p_diff.get("description").lower()

    # Check basis diff
    b_diff = next(d for d in diffs if d.get("difference_state") == "BASIS_DIFFERENCE")
    assert b_diff.get("asset") == "AVAX"
    assert b_diff.get("source_a_value") == "8000.00"
    assert b_diff.get("source_b_value") == "8050.00"
    assert b_diff.get("variance") == "50.00"
    assert "Cost basis differs by $50.00" in b_diff.get("description")
    assert "fifo" not in b_diff.get("description").lower()
    assert "hifo" not in b_diff.get("description").lower()

    # Export & Verify
    r_export = client.get(f"/api/cases/{case_id}/export")
    assert r_export.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_export.content)) as z:
        receipt_bytes = z.read("receipt-v0.1.json")
        receipt_json = json.loads(receipt_bytes.decode("utf-8"))
        assert receipt_json.get("outcome_state") == "PROCEEDS_DIFFERENCE"
        assert len(receipt_json.get("material_differences", [])) == 2

        # Verify offline
        r_verify = client.post("/api/receipts/verify", files={"file": ("receipt-v0.1.json", receipt_bytes, "application/json")})
        assert r_verify.status_code == 200
        verify_data = r_verify.json()
        assert verify_data.get("overall_status") == "PASS"
        assert verify_data.get("is_valid") is True
        assert verify_data.get("checks", {}).get("signature_authenticity") == "PASS"
        assert verify_data.get("checks", {}).get("tax_correctness") == "NOT_DETERMINED"
