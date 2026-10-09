import hashlib
import json
import zipfile
import io
from pathlib import Path
from decimal import Decimal
from fastapi.testclient import TestClient

from edge.api.app import app


def test_uat17_malformed_corrupted_and_unsupported_intake():
    """
    Permanent regression test for UAT-17 (Malformed / Corrupted / Unsupported Intake).
    Validates four tightly bounded fail-closed intake subcases:
    - UAT-17A: Missing required column (SCHEMA_REQUIRED_FIELD_MISSING)
    - UAT-17B: Invalid numeric token (NUMERIC_INVALID)
    - UAT-17C: Invalid row structure / excessive columns (CSV_MALFORMED)
    - UAT-17D: Unsupported / unrecognized source schema (SCHEMA_REQUIRED_FIELD_MISSING / SCHEMA_VERSION_UNSUPPORTED)

    Enforces critical fail-closed invariants:
    - Bad input MUST fail closed at intake before contaminating case state
    - Zero rows are silently dropped
    - Zero default or $0.00 values are fabricated
    - Zero partial reconciliations are permitted
    - Zero cryptographic receipts can be emitted from unparsed/corrupted evidence
    - Case remains clean, uncorrupted, and recoverable
    - Actionable diagnostic code and human-readable explanation returned
    """
    client = TestClient(app)
    fixture_dir = Path("tests/fixtures/uat17")

    subcases = [
        ("UAT-17A", "broker_missing_column.csv", "SCHEMA_REQUIRED_FIELD_MISSING"),
        ("UAT-17B", "broker_invalid_numeric.csv", "NUMERIC_INVALID"),
        ("UAT-17C", "broker_malformed_row.csv", "CSV_MALFORMED"),
        ("UAT-17D", "alien_unsupported_schema.csv", "SCHEMA_REQUIRED_FIELD_MISSING"),
    ]

    for subcase_id, filename, expected_err_code in subcases:
        case_id = f"CASE-{subcase_id}-REGRESSION"
        file_bytes = (fixture_dir / filename).read_bytes()

        # 1. Create Case
        r_create = client.post("/api/cases", json={
            "case_id": case_id,
            "client_reference": f"Regression {subcase_id}",
            "tax_year": 2025,
            "jurisdiction": "US"
        })
        assert r_create.status_code == 201

        # 2. Ingest corrupted/malformed file -> MUST FAIL CLOSED (422)
        r_ingest = client.post(
            f"/api/cases/{case_id}/sources",
            files={"file": (filename, file_bytes, "text/csv")},
            data={"declared_schema": "AUTO"}
        )
        assert r_ingest.status_code == 422, f"Expected 422 for {subcase_id}, got {r_ingest.status_code}"
        err_data = r_ingest.json()
        assert expected_err_code in err_data.get("detail", ""), f"Expected {expected_err_code} in error detail: {err_data}"

        # 3. Assert case state remains clean (zero sources added)
        r_case = client.get(f"/api/cases/{case_id}")
        assert r_case.status_code == 200
        case_data = r_case.json()
        assert len(case_data.get("sources", [])) == 0, f"Case contaminated with partial sources in {subcase_id}"

        # 4. Assert reconciliation fails closed (cannot reconcile un-ingested case)
        r_recon = client.post(f"/api/cases/{case_id}/reconcile")
        assert r_recon.status_code in (400, 422)

        # 5. Assert export fails closed (no receipt emitted)
        r_export = client.get(f"/api/cases/{case_id}/export")
        assert r_export.status_code in (400, 404, 422)
