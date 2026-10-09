import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from edge.api.app import app


def test_uat20_regulatory_routing_and_unsupported_boundaries():
    """
    Permanent regression test for UAT-20 (Regulatory Routing & Jurisdiction / Tax-Year Boundaries).
    
    Validates:
    - Supported case ('US', 2025) successfully reconciles under approved canonical ruleset 'VB_US_1099DA_2025_R1'
    - Unsupported tax years ('US', 2024), ('US', 2023) fail closed with HTTP 422 RULESET_UNSUPPORTED
    - Unsupported foreign jurisdictions ('UK', 2025), ('CA', 2025) fail closed with HTTP 422 RULESET_UNSUPPORTED
    - Zero synthetic ruleset generation (no fabricated ruleset IDs)
    - Zero fallback to US-2025 rules for foreign/unsupported domains
    - Zero signed outcome receipts emitted for unsupported cases
    - Clean, actionable diagnostic payload returned
    """
    client = TestClient(app)
    
    # Load sample source files for testing
    fixture_dir = Path("tests/fixtures/uat05")
    broker_bytes = (fixture_dir / "broker_perfect.csv").read_bytes()
    ledger_bytes = (fixture_dir / "ledger_perfect.csv").read_bytes()

    # 1. Supported Case: US / 2025
    case_us_2025 = "CASE-UAT20-US-2025"
    r_create = client.post("/api/cases", json={
        "case_id": case_us_2025,
        "client_reference": "Supported US 2025 Case",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201

    client.post(f"/api/cases/{case_us_2025}/sources", files={"file": ("broker.csv", broker_bytes, "text/csv")}, data={"declared_schema": "AUTO"})
    client.post(f"/api/cases/{case_us_2025}/sources", files={"file": ("ledger.csv", ledger_bytes, "text/csv")}, data={"declared_schema": "AUTO"})

    r_recon_valid = client.post(f"/api/cases/{case_us_2025}/reconcile")
    assert r_recon_valid.status_code == 200
    valid_data = r_recon_valid.json()
    assert valid_data["status"] == "RECONCILED"
    assert valid_data["receipt"]["ruleset_id"] == "VB_US_1099DA_2025_R1"

    # 2. Unsupported Tax Year: US / 2024
    case_us_2024 = "CASE-UAT20-US-2024"
    client.post("/api/cases", json={
        "case_id": case_us_2024,
        "client_reference": "Unsupported US 2024 Case",
        "tax_year": 2024,
        "jurisdiction": "US"
    })
    client.post(f"/api/cases/{case_us_2024}/sources", files={"file": ("broker.csv", broker_bytes, "text/csv")}, data={"declared_schema": "AUTO"})
    client.post(f"/api/cases/{case_us_2024}/sources", files={"file": ("ledger.csv", ledger_bytes, "text/csv")}, data={"declared_schema": "AUTO"})

    r_recon_us2024 = client.post(f"/api/cases/{case_us_2024}/reconcile")
    assert r_recon_us2024.status_code == 422
    assert "RULESET_UNSUPPORTED" in r_recon_us2024.json()["detail"]
    assert "2024" in r_recon_us2024.json()["detail"]

    # Ensure no receipt exists for US/2024
    r_export_us2024 = client.get(f"/api/cases/{case_us_2024}/export")
    assert r_export_us2024.status_code == 404

    # 3. Unsupported Tax Year: US / 2023
    case_us_2023 = "CASE-UAT20-US-2023"
    client.post("/api/cases", json={
        "case_id": case_us_2023,
        "client_reference": "Unsupported US 2023 Case",
        "tax_year": 2023,
        "jurisdiction": "US"
    })
    client.post(f"/api/cases/{case_us_2023}/sources", files={"file": ("broker.csv", broker_bytes, "text/csv")}, data={"declared_schema": "AUTO"})
    client.post(f"/api/cases/{case_us_2023}/sources", files={"file": ("ledger.csv", ledger_bytes, "text/csv")}, data={"declared_schema": "AUTO"})

    r_recon_us2023 = client.post(f"/api/cases/{case_us_2023}/reconcile")
    assert r_recon_us2023.status_code == 422
    assert "RULESET_UNSUPPORTED" in r_recon_us2023.json()["detail"]

    # 4. Unsupported Foreign Jurisdiction: UK / 2025
    case_uk_2025 = "CASE-UAT20-UK-2025"
    client.post("/api/cases", json={
        "case_id": case_uk_2025,
        "client_reference": "Unsupported UK 2025 Case",
        "tax_year": 2025,
        "jurisdiction": "UK"
    })
    client.post(f"/api/cases/{case_uk_2025}/sources", files={"file": ("broker.csv", broker_bytes, "text/csv")}, data={"declared_schema": "AUTO"})
    client.post(f"/api/cases/{case_uk_2025}/sources", files={"file": ("ledger.csv", ledger_bytes, "text/csv")}, data={"declared_schema": "AUTO"})

    r_recon_uk2025 = client.post(f"/api/cases/{case_uk_2025}/reconcile")
    assert r_recon_uk2025.status_code == 422
    assert "RULESET_UNSUPPORTED" in r_recon_uk2025.json()["detail"]
    assert "UK" in r_recon_uk2025.json()["detail"]

    # 5. Unsupported Foreign Jurisdiction: CA / 2025
    case_ca_2025 = "CASE-UAT20-CA-2025"
    client.post("/api/cases", json={
        "case_id": case_ca_2025,
        "client_reference": "Unsupported CA 2025 Case",
        "tax_year": 2025,
        "jurisdiction": "CA"
    })
    client.post(f"/api/cases/{case_ca_2025}/sources", files={"file": ("broker.csv", broker_bytes, "text/csv")}, data={"declared_schema": "AUTO"})
    client.post(f"/api/cases/{case_ca_2025}/sources", files={"file": ("ledger.csv", ledger_bytes, "text/csv")}, data={"declared_schema": "AUTO"})

    r_recon_ca2025 = client.post(f"/api/cases/{case_ca_2025}/reconcile")
    assert r_recon_ca2025.status_code == 422
    assert "RULESET_UNSUPPORTED" in r_recon_ca2025.json()["detail"]
    assert "CA" in r_recon_ca2025.json()["detail"]
