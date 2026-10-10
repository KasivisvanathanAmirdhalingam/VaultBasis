"""
VaultBasis Edge — Scenario UAT-18: Duplicate Rows & Intra-File Ambiguity Boundaries
Validates deterministic handling of intra-file duplicates and collision ambiguity under IRS 1099-DA rules.
- UAT-18A: Exact duplicate rows within broker source (Line:5 and Line:6) vs single ledger row -> 5 MATCHED, 1 MISSING_FROM_LEDGER (Line:6 preserved, no silent deduplication).
- UAT-18B: Colliding ledger records on matching keys (date, asset) with differing proceeds -> 4 MATCHED, 1 AMBIGUOUS_MATCH (MULTIPLE_CANDIDATES (2), all candidate locators preserved).
"""

import json
import zipfile
import io
from pathlib import Path
from fastapi.testclient import TestClient
from edge.api.app import app


def test_uat18a_exact_duplicate_rows_preserved_and_unmatched():
    client = TestClient(app)
    case_id = "CASE-UAT18A-REGRESSION"

    broker_bytes = Path("tests/fixtures/uat18/broker_duplicates.csv").read_bytes()
    ledger_bytes = Path("tests/fixtures/uat18/ledger_single_counterpart.csv").read_bytes()

    # Create Case
    r_create = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-18A Exact Duplicates Test Case",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201

    # Ingest Broker (has duplicate AVAX row on Line:5 and Line:6)
    r_src_a = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_duplicates.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_a.status_code == 200
    assert r_src_a.json()["status"] == "INGESTED"

    # Ingest Ledger (has single AVAX row)
    r_src_b = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_single_counterpart.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_b.status_code == 200
    assert r_src_b.json()["status"] == "INGESTED"

    # Reconcile
    client.post(f"/api/cases/{case_id}/confirm-sources")
    r_recon = client.post(f"/api/cases/{case_id}/reconcile")
    assert r_recon.status_code == 200
    recon = r_recon.json()["reconciliation"]

    # 5 comparison groups match (4 controls + first AVAX), Line:6 AVAX is MISSING_FROM_LEDGER
    assert recon["outcome_state"] == "MISSING_FROM_LEDGER"
    assert recon["comparison_group_count"] == 6
    assert len(recon["agreed_records"]) == 5
    assert len(recon["material_differences"]) == 1

    diff = recon["material_differences"][0]
    assert diff["difference_state"] == "MISSING_FROM_LEDGER"
    assert diff["asset"] == "AVAX"
    assert "Line:6" in diff["source_a_ref"]
    assert diff["source_b_ref"] == "NOT_FOUND"
    assert diff["variance"] == "9950.00"

    # Export Receipt & Verify
    r_exp = client.get(f"/api/cases/{case_id}/export")
    assert r_exp.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_exp.content)) as z:
        receipt_bytes = z.read("receipt-v0.1.json")
        receipt = json.loads(receipt_bytes.decode("utf-8"))
        assert receipt["outcome_state"] == "MISSING_FROM_LEDGER"
        assert len(receipt.get("material_differences", [])) == 1
        assert "Line:6" in receipt["material_differences"][0]["source_a_ref"]


def test_uat18b_colliding_records_differing_evidence():
    client = TestClient(app)
    case_id = "CASE-UAT18B-REGRESSION"

    broker_bytes = Path("tests/fixtures/uat18/broker_colliding.csv").read_bytes()
    ledger_bytes = Path("tests/fixtures/uat18/ledger_colliding_diff_evidence.csv").read_bytes()

    # Create Case
    r_create = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-18B Colliding Records Test Case",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201

    # Ingest Broker (1 AVAX row)
    r_src_a = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_colliding.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_a.status_code == 200
    assert r_src_a.json()["status"] == "INGESTED"

    # Ingest Ledger (2 colliding AVAX rows with different proceeds)
    r_src_b = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_colliding_diff_evidence.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_b.status_code == 200
    assert r_src_b.json()["status"] == "INGESTED"

    # Reconcile
    client.post(f"/api/cases/{case_id}/confirm-sources")
    r_recon = client.post(f"/api/cases/{case_id}/reconcile")
    assert r_recon.status_code == 200
    recon = r_recon.json()["reconciliation"]

    # 4 agreed controls, 1 AMBIGUOUS_MATCH
    assert recon["outcome_state"] == "AMBIGUOUS_MATCH"
    assert recon["comparison_group_count"] == 5
    assert len(recon["agreed_records"]) == 4
    assert len(recon["material_differences"]) == 1

    diff = recon["material_differences"][0]
    assert diff["difference_state"] == "AMBIGUOUS_MATCH"
    assert diff["asset"] == "AVAX"
    assert "Line:5" in diff["source_a_ref"]
    assert "MULTIPLE_CANDIDATES" in diff["source_b_ref"]
    assert len(diff["provenance_references"]) == 3

    # Export Receipt & Verify
    r_exp = client.get(f"/api/cases/{case_id}/export")
    assert r_exp.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_exp.content)) as z:
        receipt_bytes = z.read("receipt-v0.1.json")
        receipt = json.loads(receipt_bytes.decode("utf-8"))
        assert receipt["outcome_state"] == "AMBIGUOUS_MATCH"
        assert len(receipt.get("material_differences", [])) == 1
        assert "MULTIPLE_CANDIDATES" in receipt["material_differences"][0]["source_b_ref"]
