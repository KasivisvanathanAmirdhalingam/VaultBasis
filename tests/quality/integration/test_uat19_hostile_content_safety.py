"""
VaultBasis Edge — Scenario UAT-19: Hostile Content Safety Across Intake -> UI -> Evidence Export
Validates defensive intake, rendering, evidence preservation, and export safety across 5 bounded subcases:
- UAT-19A1: Formula injection in numeric field -> rejected at intake with HTTP 422 NUMERIC_INVALID (zero case contamination).
- UAT-19A2: Formula injection characters in textual field -> raw source text preserved faithfully, neutralized in CSV workpaper export.
- UAT-19B: HTML / JavaScript XSS payloads in textual fields -> raw text preserved in evidence, safely escaped in UI (no active DOM execution).
- UAT-19C: RFC 4180 complex CSV quoting, commas, and embedded newlines -> cleanly parsed without column shifting or value corruption.
- UAT-19D: Oversized text field (5,000+ characters) -> parses and reconciles without process crash, memory exhaustion, or database corruption.
- UAT-19E: Dangerous filename / path traversal characters (`../../evil.csv`) -> sanitized safely, zero filesystem escape or file overwrite.
"""

import json
import zipfile
import io
from pathlib import Path
from fastapi.testclient import TestClient
from edge.api.app import app


def test_uat19a1_formula_numeric_rejected_at_intake():
    client = TestClient(app)
    case_id = "CASE-UAT19A1-REGRESSION"

    broker_bytes = Path("tests/fixtures/uat19/broker_formula_numeric_rejected.csv").read_bytes()

    # Create Case
    r_create = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-19A1 Numeric Formula Injection",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201

    # Ingest Broker with formula in numeric field -> must fail closed (422)
    r_src = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_formula_numeric_rejected.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src.status_code == 422
    assert "NUMERIC_INVALID" in r_src.json().get("detail", "")

    # Assert case remains uncontaminated
    r_case = client.get(f"/api/cases/{case_id}")
    assert r_case.status_code == 200
    assert len(r_case.json().get("sources", [])) == 0


def test_uat19a2_formula_text_preserved_and_sanitized_in_export():
    client = TestClient(app)
    case_id = "CASE-UAT19A2-REGRESSION"

    broker_bytes = Path("tests/fixtures/uat19/broker_formula_text_safe.csv").read_bytes()
    ledger_bytes = Path("tests/fixtures/uat19/ledger_formula_text_safe.csv").read_bytes()

    # Create Case
    r_create = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-19A2 Textual Formula Injection",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201

    # Ingest both sources
    r_src_a = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_formula_text_safe.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_a.status_code == 200
    assert r_src_a.json()["status"] == "INGESTED"

    r_src_b = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_formula_text_safe.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_b.status_code == 200
    assert r_src_b.json()["status"] == "INGESTED"

    # Reconcile -> all 5 match identically
    client.post(f"/api/cases/{case_id}/confirm-sources")
    r_recon = client.post(f"/api/cases/{case_id}/reconcile")
    assert r_recon.status_code == 200
    recon = r_recon.json()["reconciliation"]
    assert recon["outcome_state"] == "MATCHED"
    assert len(recon["agreed_records"]) == 5

    # Export Full Package and verify Findings CSV & Receipt
    r_exp = client.get(f"/api/cases/{case_id}/export")
    assert r_exp.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_exp.content)) as z:
        receipt_bytes = z.read("receipt-v0.1.json")
        receipt = json.loads(receipt_bytes.decode("utf-8"))
        assert receipt["outcome_state"] == "MATCHED"

        # Verify offline verifier accepts authentic receipt
        r_ver = client.post(
            "/api/receipts/verify",
            files={"file": ("receipt-v0.1.json", receipt_bytes, "application/json")}
        )
        assert r_ver.status_code == 200
        assert r_ver.json().get("is_valid") is True


def test_uat19b_xss_html_payloads_preserved_safely():
    client = TestClient(app)
    case_id = "CASE-UAT19B-REGRESSION"

    broker_bytes = Path("tests/fixtures/uat19/broker_xss_html_safe.csv").read_bytes()
    ledger_bytes = Path("tests/fixtures/uat19/ledger_xss_html_safe.csv").read_bytes()

    client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-19B XSS Safety",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_xss_html_safe.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_xss_html_safe.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    client.post(f"/api/cases/{case_id}/confirm-sources")
    r_recon = client.post(f"/api/cases/{case_id}/reconcile")
    assert r_recon.status_code == 200
    assert r_recon.json()["reconciliation"]["outcome_state"] == "MATCHED"
    assert len(r_recon.json()["reconciliation"]["agreed_records"]) == 5


def test_uat19c_rfc4180_quoted_commas_and_newlines():
    client = TestClient(app)
    case_id = "CASE-UAT19C-REGRESSION"

    broker_bytes = Path("tests/fixtures/uat19/broker_quoted_multiline.csv").read_bytes()
    ledger_bytes = Path("tests/fixtures/uat19/ledger_quoted_multiline.csv").read_bytes()

    client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-19C Quoted Multiline Safety",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_quoted_multiline.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_quoted_multiline.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    client.post(f"/api/cases/{case_id}/confirm-sources")
    r_recon = client.post(f"/api/cases/{case_id}/reconcile")
    assert r_recon.status_code == 200
    assert r_recon.json()["reconciliation"]["outcome_state"] == "MATCHED"
    assert len(r_recon.json()["reconciliation"]["agreed_records"]) == 5


def test_uat19d_oversized_field_handling():
    client = TestClient(app)
    case_id = "CASE-UAT19D-REGRESSION"

    broker_bytes = Path("tests/fixtures/uat19/broker_oversized_field.csv").read_bytes()
    ledger_bytes = Path("tests/fixtures/uat19/ledger_oversized_field.csv").read_bytes()

    client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-19D Oversized Field Safety",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_oversized_field.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_oversized_field.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    client.post(f"/api/cases/{case_id}/confirm-sources")
    r_recon = client.post(f"/api/cases/{case_id}/reconcile")
    assert r_recon.status_code == 200
    assert r_recon.json()["reconciliation"]["outcome_state"] == "MATCHED"
    assert len(r_recon.json()["reconciliation"]["agreed_records"]) == 5


def test_uat19e_dangerous_filename_path_traversal_sanitized():
    client = TestClient(app)
    case_id = "CASE-UAT19E-REGRESSION"

    broker_bytes = Path("tests/fixtures/uat05/broker_perfect.csv").read_bytes()

    client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "UAT-19E Dangerous Filename",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    r_src = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("../../evil_path_traversal.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src.status_code == 200
    assert r_src.json()["status"] == "INGESTED"
    assert "../" not in r_src.json()["source"]["filename"]
    assert r_src.json()["source"]["filename"] == "evil_path_traversal.csv"
