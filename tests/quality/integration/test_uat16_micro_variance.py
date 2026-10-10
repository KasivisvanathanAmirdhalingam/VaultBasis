import hashlib
import json
import zipfile
import io
from pathlib import Path
from decimal import Decimal
from fastapi.testclient import TestClient

from edge.api.app import app


def test_uat16_micro_variance_and_nonzero_difference():
    """
    Permanent regression test for UAT-16 (Micro-Variance / Any Nonzero Difference).
    Validates:
    - 5 comparison groups: 4 standard agreements (BTC, ETH, SOL, LINK) and 1 transaction (AVAX) with sub-cent micro-variance in proceeds (Broker: $9950.00000000 vs Ledger: $9950.00000001).
    - Invariant preservation: Any non-zero difference between supported records is detected and surfaced as a deterministic difference; zero implicit tolerance, zero rounding away.
    - Top-level outcome_state == 'PROCEEDS_DIFFERENCE'
    - 4 agreed records, 1 material difference, 0 unresolved items
    - Material difference state == 'PROCEEDS_DIFFERENCE', variance == '0.00000001'
    - Neutral description with exact dollar discrepancy
    - Cryptographic receipt emitted with PROCEEDS_DIFFERENCE state and valid Ed25519 signature
    - Local receipt verification endpoint returns PASS with tax correctness limitation disclaimer
    """
    client = TestClient(app)
    case_id = "CASE-UAT16-REGRESSION"

    # Load fixtures
    fixture_dir = Path("tests/fixtures/uat16")
    broker_bytes = (fixture_dir / "broker_micro_diff.csv").read_bytes()
    ledger_bytes = (fixture_dir / "ledger_micro_diff.csv").read_bytes()

    # Create Case
    r_create = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-16 Regression Test Case",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201

    # Ingest Source A
    r_src_a = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_micro_diff.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_a.status_code == 200

    # Ingest Source B
    r_src_b = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_micro_diff.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_b.status_code == 200

    # Reconcile
    client.post(f"/api/cases/{case_id}/confirm-sources")
    r_recon = client.post(f"/api/cases/{case_id}/reconcile")
    assert r_recon.status_code == 200
    recon_data = r_recon.json().get("reconciliation", {})

    assert recon_data.get("outcome_state") == "PROCEEDS_DIFFERENCE"
    assert len(recon_data.get("agreed_records", [])) == 4
    assert len(recon_data.get("material_differences", [])) == 1
    assert len(recon_data.get("unresolved_items", [])) == 0
    assert recon_data.get("comparison_group_count") == 5

    # Check AVAX material difference specifically
    diff = recon_data.get("material_differences", [])[0]
    assert diff.get("difference_state") == "PROCEEDS_DIFFERENCE"
    assert diff.get("asset") == "AVAX"
    assert Decimal(diff.get("variance")) == Decimal("0.00000001")
    assert diff.get("source_a_value") == "9950.00000000"
    assert diff.get("source_b_value") == "9950.00000001"
    assert "Proceeds differ by" in diff.get("description", "")

    # Export & Verify
    r_export = client.get(f"/api/cases/{case_id}/export")
    assert r_export.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_export.content)) as z:
        receipt_bytes = z.read("receipt-v0.1.json")
        receipt_json = json.loads(receipt_bytes.decode("utf-8"))
        assert receipt_json.get("outcome_state") == "PROCEEDS_DIFFERENCE"
        assert len(receipt_json.get("material_differences", [])) == 1

        # Local receipt verification endpoint check
        r_verify = client.post("/api/receipts/verify", files={"file": ("receipt-v0.1.json", receipt_bytes, "application/json")})
        assert r_verify.status_code == 200
        verify_data = r_verify.json()
        assert verify_data.get("overall_status") == "PASS"
        assert verify_data.get("is_valid") is True
        assert verify_data.get("checks", {}).get("signature_authenticity") == "PASS"
        assert verify_data.get("checks", {}).get("tax_correctness") == "NOT_DETERMINED"
