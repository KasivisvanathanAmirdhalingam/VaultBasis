"""
VaultBasis — Slice 2 & 3 Test Suite
Tests Intake Parsers (1099-DA, Koinly, Fallback), Canonical Case Models,
Deterministic Reconciliation Engine, 13 Outcome States, and FastAPI Endpoints.
"""

from decimal import Decimal
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from edge.api.app import app
from edge.assurance.reconciliation_engine import DeterministicReconciliationEngine
from edge.connectors.form1099da_parser import Form1099DAParser
from edge.connectors.koinly_parser import KoinlyCapitalGainsParser
from edge.connectors.validator import IntakeDispatcher
from edge.connectors.vaultbasis_csv_parser import VaultBasisCSVParser
from schemas.canonical.case import CanonicalCase


@pytest.fixture
def sample_1099da_csv():
    return b"""Property,Units,Date sold,Proceeds,Date acquired,Cost basis,Box 2
BTC,1.0,2025-11-20,18400.00,2025-02-11,12100.00,YES
ETH,1.0,2025-12-05,3200.00,2025-03-01,2800.00,YES
"""


@pytest.fixture
def sample_koinly_csv():
    return b"""Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired
2025-11-20,BTC,1.0,16300.00,18400.00,2100.00,2025-02-11
2025-12-05,ETH,1.0,2800.00,3200.00,400.00,2025-03-01
"""


@pytest.mark.smoke
def test_1099da_parser(sample_1099da_csv):
    txs = Form1099DAParser.parse(sample_1099da_csv, "src_1099", "hash123")
    assert len(txs) == 2
    assert txs[0].asset == "BTC"
    assert txs[0].proceeds == Decimal("18400.00")
    assert txs[0].cost_basis == Decimal("12100.00")
    assert txs[0].acquisition_date == "2025-02-11"
    assert txs[0].disposition_date == "2025-11-20"
    assert txs[0].basis_reported_to_irs == "YES"
    assert txs[0].is_unresolved is False


@pytest.mark.smoke
def test_koinly_parser(sample_koinly_csv):
    txs = KoinlyCapitalGainsParser.parse(sample_koinly_csv, "src_koinly", "hash456")
    assert len(txs) == 2
    assert txs[0].asset == "BTC"
    assert txs[0].proceeds == Decimal("18400.00")
    assert txs[0].cost_basis == Decimal("16300.00")
    assert txs[0].gain_loss == Decimal("2100.00")


@pytest.mark.regression
def test_fallback_csv_parser():
    fallback_csv = b"""date,asset,quantity,proceeds,cost_basis,date_acquired,source_ref
2025-08-10,SOL,10.0,1500.00,1200.00,2025-01-15,CustomLine1
"""
    txs = VaultBasisCSVParser.parse(fallback_csv, "src_fallback", "hash789")
    assert len(txs) == 1
    assert txs[0].asset == "SOL"
    assert txs[0].quantity == Decimal("10.0")
    assert txs[0].proceeds == Decimal("1500.00")


@pytest.mark.smoke
def test_intake_dispatcher_auto_detection(sample_1099da_csv, sample_koinly_csv):
    meta1, txs1 = IntakeDispatcher.ingest_document(sample_1099da_csv, "broker_1099da.csv", "src_1")
    assert meta1.schema_id == Form1099DAParser.SCHEMA_ID
    assert len(txs1) == 2

    meta2, txs2 = IntakeDispatcher.ingest_document(sample_koinly_csv, "koinly_export.csv", "src_2")
    assert meta2.schema_id == KoinlyCapitalGainsParser.SCHEMA_ID
    assert len(txs2) == 2


@pytest.mark.smoke
def test_deterministic_reconciliation_basis_difference(sample_1099da_csv, sample_koinly_csv):
    meta_a, txs_a = IntakeDispatcher.ingest_document(sample_1099da_csv, "1099da.csv", "src_1099")
    meta_b, txs_b = IntakeDispatcher.ingest_document(sample_koinly_csv, "koinly.csv", "src_koinly")

    case = CanonicalCase(
        case_id="CASE-TEST-001",
        tax_year=2025,
        jurisdiction="US",
        sources={meta_a.source_id: meta_a, meta_b.source_id: meta_b},
        transactions=txs_a + txs_b,
        created_at="2026-09-26T12:00:00Z",
        updated_at="2026-09-26T12:00:00Z"
    )

    result = DeterministicReconciliationEngine.reconcile_case(case)

    # In sample data:
    # BTC proceeds match ($18,400) but basis differs ($12,100 vs $16,300) -> BASIS_DIFFERENCE ($4,200)
    # ETH matches completely ($3,200 proceeds, $2,800 basis)
    assert result.outcome_state == "BASIS_DIFFERENCE"
    assert len(result.material_differences) == 1
    diff = result.material_differences[0]
    assert diff.difference_state == "BASIS_DIFFERENCE"
    assert diff.asset == "BTC"
    assert diff.variance == "4200.00"
    assert len(diff.provenance_references) >= 2


@pytest.mark.smoke
def test_unknown_basis_preservation_not_zero():
    # Test PRD Invariant: Missing basis does not become $0
    unres_csv = b"""Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2
SOL,2025-05-01,500.00,2025-01-01,,YES
"""
    txs = Form1099DAParser.parse(unres_csv, "src_unres", "hash_unres")
    assert txs[0].cost_basis is None
    assert txs[0].is_unresolved is True
    assert txs[0].unresolved_reason == "BASIS_UNAVAILABLE"


@pytest.mark.smoke
def test_fastapi_e2e_endpoints(sample_1099da_csv, sample_koinly_csv):
    client = TestClient(app)

    # 1. Healthcheck
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "HEALTHY"

    # 2. Create Case
    res_create = client.post("/api/cases", json={"case_id": "CASE-E2E-TEST", "tax_year": 2025})
    assert res_create.status_code in [200, 201]

    # 3. Upload 1099-DA
    res_up1 = client.post(
        "/api/cases/CASE-E2E-TEST/sources",
        files={"file": ("1099da.csv", sample_1099da_csv, "text/csv")},
        data={"source_type": "AUTO"}
    )
    assert res_up1.status_code == 200
    assert res_up1.json()["parsed_rows"] == 2

    # 4. Upload Koinly CSV
    res_up2 = client.post(
        "/api/cases/CASE-E2E-TEST/sources",
        files={"file": ("koinly.csv", sample_koinly_csv, "text/csv")},
        data={"source_type": "AUTO"}
    )
    assert res_up2.status_code == 200
    assert res_up2.json()["parsed_rows"] == 2

    # 4.5 Verify 412 Precondition Failed when unconfirmed (CASE-SOURCE-001)
    res_unconf = client.post("/api/cases/CASE-E2E-TEST/reconcile")
    assert res_unconf.status_code == 412
    assert res_unconf.json()["detail"]["code"] == "CONFIRMATION_REQUIRED"

    # Confirm active sources
    res_conf = client.post("/api/cases/CASE-E2E-TEST/confirm-sources")
    assert res_conf.status_code == 200
    assert res_conf.json()["status"] == "CONFIRMED"

    # 5. Trigger Reconciliation
    res_recon = client.post("/api/cases/CASE-E2E-TEST/reconcile")
    assert res_recon.status_code == 200
    recon_data = res_recon.json()
    assert recon_data["outcome_state"] == "BASIS_DIFFERENCE"
    assert "receipt" in recon_data
    assert recon_data["receipt"]["signature"] is not None

    # 6. Retrieve Signed Receipt
    res_rcpt = client.get("/api/cases/CASE-E2E-TEST/receipt")
    assert res_rcpt.status_code == 200
    assert res_rcpt.json()["receipt_id"] == recon_data["receipt_id"]

    # 7. Export ZIP Evidence Bundle
    res_export = client.get("/api/cases/CASE-E2E-TEST/export")
    assert res_export.status_code == 200
    assert res_export.headers["content-type"] == "application/zip"
    assert len(res_export.content) > 500  # valid zip file

    # 8. Independent Verification Endpoint
    res_verify = client.post(
        "/api/receipts/verify",
        files={"file": ("receipt.json", res_rcpt.content, "application/json")}
    )
    assert res_verify.status_code == 200
    report = res_verify.json()
    assert report["overall_status"] == "PASS"
    assert report["checks"]["signature_authenticity"] == "PASS"
    assert report["checks"]["schema_conformance"] == "PASS"


@pytest.mark.regression
def test_evidence_bundle_export_encoding_invariance(monkeypatch):
    """
    Focused regression test for MMP11-DIST-WIN-003:
    Proves that export_evidence_bundle succeeds and outputs a valid ZIP archive
    containing UTF-8 text assets even when the host default encoding is cp1252 (Windows ANSI).
    """
    import io
    import zipfile

    client = TestClient(app)

    # 1. Ensure sample case is loaded and reconciled
    load_res = client.post("/api/sample-case/load")
    assert load_res.status_code == 200
    recon_res = client.post("/api/cases/CASE-SAMPLE-2025/reconcile")
    assert recon_res.status_code == 200

    # 2. Simulate Windows host environment where default text reading (encoding=None) uses cp1252
    orig_read_text = Path.read_text

    def cp1252_default_read_text(self, encoding=None, errors=None):
        eff_encoding = encoding or "cp1252"
        return orig_read_text(self, encoding=eff_encoding, errors=errors)

    monkeypatch.setattr(Path, "read_text", cp1252_default_read_text)

    # 3. Export evidence bundle under simulated cp1252 host default locale
    res_export = client.get("/api/cases/CASE-SAMPLE-2025/export")
    assert res_export.status_code == 200
    assert res_export.headers["content-type"] == "application/zip"

    # 4. Open and inspect ZIP contents
    zip_buffer = io.BytesIO(res_export.content)
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        namelist = zf.namelist()
        assert "receipt-v0.1.json" in namelist
        assert "schemas/receipt-v0.1.json" in namelist
        assert "VERIFY_INSTRUCTIONS.txt" in namelist

        # 5. Assert schema and instructions decode cleanly as UTF-8
        instructions_content = zf.read("VERIFY_INSTRUCTIONS.txt").decode("utf-8")
        assert "VAULTBASIS OUTCOME RECEIPT VERIFICATION INSTRUCTIONS" in instructions_content

        schema_content = zf.read("schemas/receipt-v0.1.json").decode("utf-8")
        assert "$schema" in schema_content


@pytest.mark.regression
def test_evidence_bundle_export_allowlist_and_negative_controls():
    """
    Evidence Export Contract (MMP11-DIST-WIN-004):
    Positive allowlist: Only receipt, schema, raw evidence files, and instructions are permitted.
    Negative controls: Zero Python source (.py), bytecode (.pyc), caches, or internal tooling allowed.
    """
    import io
    import zipfile

    client = TestClient(app)
    load_res = client.post("/api/sample-case/load")
    assert load_res.status_code == 200
    recon_res = client.post("/api/cases/CASE-SAMPLE-2025/reconcile")
    assert recon_res.status_code == 200

    res_export = client.get("/api/cases/CASE-SAMPLE-2025/export")
    assert res_export.status_code == 200

    with zipfile.ZipFile(io.BytesIO(res_export.content), "r") as zf:
        namelist = zf.namelist()

        # 1. Positive Allowlist Validation: Every single member must match the declared contract
        allowed_exact = {
            "receipt-v0.1.json",
            "schemas/receipt-v0.1.json",
            "VERIFY_INSTRUCTIONS.txt",
            "VERIFY.html",
            "manifest.json"
        }
        for name in namelist:
            is_exact = name in allowed_exact
            is_evidence = name.startswith("evidence/")
            is_findings = name.startswith("VaultBasis_Findings_") and name.endswith(".csv")
            assert is_exact or is_evidence or is_findings, f"Unexpected member violating Evidence Export allowlist: {name}"

        # 2. Negative Controls: Absolute ban on Python files and internal directories
        assert "verify_receipt.py" not in namelist, "verify_receipt.py leaked at root of evidence bundle"
        assert "technical-verification/verify_receipt.py" not in namelist, "verify_receipt.py leaked in technical-verification/"
        assert not any(name.endswith((".py", ".pyc", ".pyd")) for name in namelist), "Python source/binary leaked in evidence bundle"
        assert not any(name.startswith(("technical-verification/", "__pycache__/", "build/", "dist/", ".git/")) for name in namelist), (
            "Internal development/tooling folder leaked in evidence bundle"
        )

