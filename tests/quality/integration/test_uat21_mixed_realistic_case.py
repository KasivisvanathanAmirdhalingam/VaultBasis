"""
VaultBasis Edge — Scenario UAT-21: Comprehensive Mixed Realistic Case
Validates that multiple independent reconciliation outcome classes coexist in a single realistic case (US / Tax Year 2025)
without precedence logic collapsing, erasing, or suppressing component differences.
- 1 MATCHED (BTC)
- 1 PROCEEDS_DIFFERENCE (ETH)
- 1 BASIS_DIFFERENCE (SOL)
- 1 MISSING_FROM_LEDGER (LINK)
- 1 REPORTING_SCOPE_DIFFERENCE (DOGE)
- 1 UNRESOLVED_DATA item (ADA)
- 1 AMBIGUOUS_MATCH (UNI)
- 1 MISSING_FROM_1099DA (AVAX)
Top-level outcome state evaluates to UNRESOLVED_DATA while preserving all 6 material differences and 1 unresolved item.
"""

import json
import zipfile
import io
from pathlib import Path
from fastapi.testclient import TestClient
from edge.api.app import app


def test_uat21_comprehensive_mixed_realistic_case():
    client = TestClient(app)
    case_id = "CASE-UAT21-REGRESSION"

    broker_bytes = Path("tests/fixtures/uat21/broker_realistic.csv").read_bytes()
    ledger_bytes = Path("tests/fixtures/uat21/ledger_realistic.csv").read_bytes()

    # Create Case
    r_create = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-21 Mixed Realistic Case Regression",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201

    # Ingest Broker
    r_src_a = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_realistic.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_a.status_code == 200
    assert r_src_a.json()["status"] == "INGESTED"

    # Ingest Ledger
    r_src_b = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_realistic.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_b.status_code == 200
    assert r_src_b.json()["status"] == "INGESTED"

    # Reconcile
    client.post(f"/api/cases/{case_id}/confirm-sources")
    r_recon = client.post(f"/api/cases/{case_id}/reconcile")
    assert r_recon.status_code == 200
    recon = r_recon.json()["reconciliation"]

    # Precedence: top-level outcome state is UNRESOLVED_DATA
    assert recon["outcome_state"] == "UNRESOLVED_DATA"
    assert recon["comparison_group_count"] == 8
    assert len(recon["agreed_records"]) == 1
    assert len(recon["material_differences"]) == 6
    assert len(recon["unresolved_items"]) == 1

    # Verify each component finding is preserved
    diff_map = {d["asset"]: d for d in recon["material_differences"]}
    assert "ETH" in diff_map and diff_map["ETH"]["difference_state"] == "PROCEEDS_DIFFERENCE"
    assert "SOL" in diff_map and diff_map["SOL"]["difference_state"] == "BASIS_DIFFERENCE"
    assert "LINK" in diff_map and diff_map["LINK"]["difference_state"] == "MISSING_FROM_LEDGER"
    assert "DOGE" in diff_map and diff_map["DOGE"]["difference_state"] == "REPORTING_SCOPE_DIFFERENCE"
    assert "UNI" in diff_map and diff_map["UNI"]["difference_state"] == "AMBIGUOUS_MATCH"
    assert "AVAX" in diff_map and diff_map["AVAX"]["difference_state"] == "MISSING_FROM_1099DA"

    assert recon["unresolved_items"][0]["reason_code"] == "BASIS_UNAVAILABLE"
    assert recon["agreed_records"][0]["asset"] == "BTC"

    # Export Receipt & Verify
    r_exp = client.get(f"/api/cases/{case_id}/export")
    assert r_exp.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_exp.content)) as z:
        receipt_bytes = z.read("receipt-v0.1.json")
        receipt = json.loads(receipt_bytes.decode("utf-8"))
        assert receipt["outcome_state"] == "UNRESOLVED_DATA"
        assert len(receipt["material_differences"]) == 6
        assert len(receipt["unresolved_items"]) == 1

        r_ver = client.post(
            "/api/receipts/verify",
            files={"file": ("receipt-v0.1.json", receipt_bytes, "application/json")}
        )
        assert r_ver.status_code == 200
        assert r_ver.json()["overall_status"] == "PASS"
        assert r_ver.json()["is_valid"] is True
