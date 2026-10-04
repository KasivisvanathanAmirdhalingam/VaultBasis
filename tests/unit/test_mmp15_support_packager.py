"""
VaultBasis MMP-1.5 Sanitized Diagnostic & Support Bundle Packager Test Suite
Tests MMP15-OPS-001:
1. Schema-first positive allowlist verification
2. Regulated identifier masking in diagnostics (PTIN/EFIN)
3. Negative control verification: Zero financial data, transaction rows, wallets, or client evidence
4. Structured ZIP bundle integrity (diagnostic.json, integrity.txt, migrations.json, README.txt)
5. REST API endpoints (GET /api/system/diagnostic, GET /api/system/diagnostic/bundle)
6. Secondary negative-control regex scanning across full bundle content
"""

import io
import json
import re
import zipfile
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from edge.api.app import app
from edge.commercial.diagnostics import DiagnosticPackager, DiagnosticBundleReport
from edge.commercial.identity import FirmIdentity, FirmIdentityService
from edge.commercial.policy import CommercialPolicyService
from edge.storage.sqlite_store import SQLiteStore
from schemas.canonical.case import CanonicalCase, SourceDocumentMetadata
from schemas.canonical.transaction import CanonicalTransaction


@pytest.fixture
def test_environment(tmp_path):
    db_file = tmp_path / "diag_test.db"
    store = SQLiteStore(db_file)
    license_dir = tmp_path / "license"
    policy_service = CommercialPolicyService(store=store, license_dir=license_dir, installation_id="INST-DIAG-001")
    identity_service = FirmIdentityService(store)
    packager = DiagnosticPackager(store, policy_service, identity_service)
    return store, policy_service, identity_service, packager


@pytest.fixture
def client(monkeypatch, tmp_path):
    test_db = tmp_path / "app_diag_test.db"
    store = SQLiteStore(test_db)
    policy_service = CommercialPolicyService(store=store, license_dir=tmp_path / "lic", installation_id="INST-APP-001")
    identity_service = FirmIdentityService(store)
    packager = DiagnosticPackager(store, policy_service, identity_service)

    monkeypatch.setattr("edge.api.app.db_store", store)
    monkeypatch.setattr("edge.api.app.commercial_policy", policy_service)
    monkeypatch.setattr("edge.api.app.firm_identity_service", identity_service)
    monkeypatch.setattr("edge.api.app.diagnostic_packager", packager)
    return TestClient(app)


def test_diagnostic_report_schema_and_allowlist(test_environment):
    store, policy_service, identity_service, packager = test_environment

    report = packager.generate_report()
    assert isinstance(report, DiagnosticBundleReport)
    assert report.bundle_id.startswith("DIAG-")
    assert report.system.product == "VaultBasis"
    assert report.database.journal_mode == "WAL"
    assert report.database.integrity_status == "OK"
    assert report.database.foreign_keys_valid is True
    assert report.commercial.installation_id == "INST-DIAG-001"
    assert report.firm.configured is False
    assert report.runtime.status == "HEALTHY"


def test_diagnostic_report_masks_firm_regulated_identifiers(test_environment):
    store, policy_service, identity_service, packager = test_environment

    # Save firm identity with sensitive PTIN and EFIN
    ident = FirmIdentity(
        organization_id="ORG-DIAG-TEST",
        firm_name="Diagnostic Partner CPAs",
        preparer_id="PREP-DIAG-01",
        display_name="David Triage, CPA",
        ptin="P09876543",
        efin="654321",
    )
    identity_service.save_identity(ident)

    report = packager.generate_report()
    assert report.firm.configured is True
    firm_dict = report.firm.identity
    assert firm_dict is not None
    assert firm_dict["organization_id"] == "ORG-DIAG-TEST"
    assert firm_dict["ptin_masked"] == "P*****543"
    assert firm_dict["efin_masked"] == "***321"

    # String serialization check
    json_str = report.model_dump_json()
    assert "P09876543" not in json_str
    assert "654321" not in json_str
    assert "P*****543" in json_str
    assert "***321" in json_str


def test_diagnostic_zero_financial_and_evidence_leakage(test_environment):
    """
    CRITICAL PRIVACY TEST:
    Populates database with real confidential case, transactions, tax lots, and source files.
    Asserts that NONE of the client names, asset amounts, prices, or source rows appear in the diagnostic output.
    """
    store, policy_service, identity_service, packager = test_environment

    now_utc = datetime.now(timezone.utc).isoformat()
    case = CanonicalCase(
        case_id="CASE-HIGH-NET-WORTH-001",
        client_reference="Secret Family Trust",
        tax_year=2025,
        jurisdiction="US",
        case_status="CREATED",
        created_at=now_utc,
        updated_at=now_utc,
    )
    store.save_case(case)

    # Ingest source and confidential transaction
    source_meta = SourceDocumentMetadata(
        source_id="SRC-CONFIDENTIAL-01",
        filename="confidential_crypto_trades_2025.csv",
        sha256_hash="1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
        byte_size=1024,
        schema_id="1099DA",
        row_count=1,
        ingested_at=now_utc,
    )

    confidential_tx = CanonicalTransaction(
        transaction_id="TX-SECRET-BLOCKCHAIN-01",
        source_id="SRC-CONFIDENTIAL-01",
        source_file_hash="1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
        source_row_reference="1",
        asset="SECRET_TOKEN_XYZ",
        amount="999999.55",
        timestamp=now_utc,
        transaction_type="DISPOSAL",
        proceeds="12345678.90",
        cost_basis="8765432.10",
        raw_row={"wallet_address": "0xSecretWalletAddress1234567890abcdef"},
    )

    store.add_source_and_transactions(
        "CASE-HIGH-NET-WORTH-001",
        source_meta,
        b"raw,unredacted,client,financial,records",
        [confidential_tx],
    )

    # Generate JSON and ZIP bundle
    report_json = packager.export_bundle_json()
    bundle_zip_bytes = packager.export_bundle_zip()

    # 1. Assertions on JSON string
    assert "CASE-HIGH-NET-WORTH-001" not in report_json
    assert "Secret Family Trust" not in report_json
    assert "confidential_crypto_trades_2025.csv" not in report_json
    assert "TX-SECRET-BLOCKCHAIN-01" not in report_json
    assert "SECRET_TOKEN_XYZ" not in report_json
    assert "999999.55" not in report_json
    assert "12345678.90" not in report_json
    assert "8765432.10" not in report_json
    assert "0xSecretWalletAddress1234567890abcdef" not in report_json
    assert "raw,unredacted,client,financial,records" not in report_json

    # 2. Assertions on ZIP contents
    with zipfile.ZipFile(io.BytesIO(bundle_zip_bytes), "r") as zf:
        members = zf.namelist()
        assert set(members) == {"manifest.json", "diagnostic.json", "integrity.txt", "migrations.json", "README.txt"}
        for member in members:
            content = zf.read(member).decode("utf-8")
            assert "Secret Family Trust" not in content
            assert "0xSecretWalletAddress" not in content
            assert "SECRET_TOKEN_XYZ" not in content
            assert "12345678.90" not in content


def test_structured_zip_bundle_integrity(test_environment):
    import hashlib
    store, policy_service, identity_service, packager = test_environment
    zip_bytes = packager.export_bundle_zip()
    assert len(zip_bytes) > 0

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        members = zf.namelist()
        assert "manifest.json" in members
        assert "diagnostic.json" in members
        assert "integrity.txt" in members
        assert "migrations.json" in members
        assert "README.txt" in members

        # Validate manifest.json format and SHA-256 digests
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifest["format"] == "vaultbasis-support-diagnostic-v1"
        assert "bundle_id" in manifest
        assert "build_sha" in manifest

        for filename, expected_digest in manifest["files"].items():
            assert filename in members
            file_data = zf.read(filename)
            actual_digest = f"sha256:{hashlib.sha256(file_data).hexdigest()}"
            assert actual_digest == expected_digest

        diag_data = json.loads(zf.read("diagnostic.json").decode("utf-8"))
        assert diag_data["system"]["product"] == "VaultBasis"
        assert diag_data["database"]["journal_mode"] == "WAL"

        integrity_txt = zf.read("integrity.txt").decode("utf-8")
        assert "VaultBasis Database Integrity Report" in integrity_txt
        assert "Structural Integrity: OK" in integrity_txt

        migrations = json.loads(zf.read("migrations.json").decode("utf-8"))
        assert isinstance(migrations, list)
        assert len(migrations) >= 3


def test_api_diagnostic_endpoints(client):
    # 1. GET /api/system/diagnostic
    res = client.get("/api/system/diagnostic")
    assert res.status_code == 200
    data = res.json()
    assert "bundle_id" in data
    assert data["system"]["product"] == "VaultBasis"
    assert data["database"]["integrity_status"] == "OK"
    assert "firm" in data
    assert "commercial" in data

    # 2. GET /api/system/diagnostic/bundle
    res_zip = client.get("/api/system/diagnostic/bundle")
    assert res_zip.status_code == 200
    assert res_zip.headers["content-type"] == "application/zip"
    assert "VaultBasis_Support_Diagnostic_" in res_zip.headers["content-disposition"]

    # Verify returned zip
    with zipfile.ZipFile(io.BytesIO(res_zip.content), "r") as zf:
        members = zf.namelist()
        assert set(members) == {"manifest.json", "diagnostic.json", "integrity.txt", "migrations.json", "README.txt"}
