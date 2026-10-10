import hashlib
import json
import zipfile
import io
from pathlib import Path
from decimal import Decimal
from fastapi.testclient import TestClient

from edge.api.app import app


def test_uat11_fail_closed_ambiguous_match():
    """
    Permanent regression test for UAT-11 (Ambiguous Match / Multiple Identical Candidates).
    Validates:
    - 5 Broker transactions and 6 Ledger transactions where 4 match uniquely and 1 Broker transaction (AVAX) has 2 identical Ledger counterpart candidates.
    - Engine refuses to arbitrarily pick candidate 0 or 1, and fails closed with AMBIGUOUS_MATCH.
    - Top-level outcome_state == 'AMBIGUOUS_MATCH'
    - 4 agreed records, 1 material difference ('AMBIGUOUS_MATCH'), 0 unresolved items
    - Difference record preserves references to both candidate ledger rows
    - Zero arbitrary selection, zero silent deduplication, zero fabricated certainty
    - Difference description contains neutral guidance prompting practitioner review
    - Receipt contains exactly 1 finding and authentic Ed25519 signature
    - Offline verifier returns PASS with tax correctness limitation disclaimer
    """
    client = TestClient(app)
    case_id = "CASE-UAT11-REGRESSION"

    # Load fixtures
    fixture_dir = Path("tests/fixtures/uat11")
    broker_bytes = (fixture_dir / "broker_ambiguous.csv").read_bytes()
    ledger_bytes = (fixture_dir / "ledger_ambiguous.csv").read_bytes()

    # Create Case
    r_create = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-11 Regression Test Case",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201

    # Ingest Source A
    r_src_a = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_ambiguous.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_a.status_code == 200

    # Ingest Source B
    r_src_b = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_ambiguous.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_b.status_code == 200

    # Reconcile
    client.post(f"/api/cases/{case_id}/confirm-sources")
    r_recon = client.post(f"/api/cases/{case_id}/reconcile")
    assert r_recon.status_code == 200
    recon_data = r_recon.json().get("reconciliation", {})

    assert recon_data.get("outcome_state") == "AMBIGUOUS_MATCH"
    assert recon_data.get("assurance_level") == "L2_EVIDENCE_RECONCILED"
    assert len(recon_data.get("agreed_records", [])) == 4
    assert len(recon_data.get("material_differences", [])) == 1
    assert len(recon_data.get("unresolved_items", [])) == 0
    assert recon_data.get("comparison_group_count") == 5
    assert recon_data.get("matched_group_count") == 4
    assert recon_data.get("source_a_row_count") == 5
    assert recon_data.get("source_b_row_count") == 6

    diff = recon_data.get("material_differences")[0]
    assert diff.get("asset") == "AVAX"
    assert diff.get("difference_state") == "AMBIGUOUS_MATCH"
    assert diff.get("source_a_value") == "9950.00"
    assert "MULTIPLE_CANDIDATES" in diff.get("source_b_ref")
    assert "Multiple possible ledger counterparts" in diff.get("description")
    assert "Row:5" in diff.get("description")
    assert "Row:6" in diff.get("description")
    assert "fifo" not in diff.get("description").lower()
    assert "hifo" not in diff.get("description").lower()

    # Export & Verify
    r_export = client.get(f"/api/cases/{case_id}/export")
    assert r_export.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_export.content)) as z:
        receipt_bytes = z.read("receipt-v0.1.json")
        receipt_json = json.loads(receipt_bytes.decode("utf-8"))
        assert receipt_json.get("outcome_state") == "AMBIGUOUS_MATCH"
        assert len(receipt_json.get("material_differences", [])) == 1

        rec_diff = receipt_json.get("material_differences")[0]
        assert rec_diff.get("difference_state") == "AMBIGUOUS_MATCH"
        assert len(rec_diff.get("provenance_references", [])) >= 3  # 1 broker row + 2 ledger candidates

        # Verify offline
        r_verify = client.post("/api/receipts/verify", files={"file": ("receipt-v0.1.json", receipt_bytes, "application/json")})
        assert r_verify.status_code == 200
        verify_data = r_verify.json()
        assert verify_data.get("overall_status") == "PASS"
        assert verify_data.get("is_valid") is True
        assert verify_data.get("checks", {}).get("signature_authenticity") == "PASS"
        assert verify_data.get("checks", {}).get("tax_correctness") == "NOT_DETERMINED"
