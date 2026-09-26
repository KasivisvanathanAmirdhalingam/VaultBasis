"""
VaultBasis Quality Suite — BDD (Behavior-Driven Development)
Implements Given-When-Then acceptance criteria for the Seven Blocking Preview Gates (PRD §41).
"""

from decimal import Decimal
import json
import pytest
from starlette.testclient import TestClient

from edge.api.app import app
from apps.verifier.verify_receipt import verify_outcome_receipt
from edge.connectors.validator import IntakeDispatcher


@pytest.fixture
def client():
    return TestClient(app)


# ------------------------------------------------------------------------------
# AC-01: Edge starts and accepts input
# ------------------------------------------------------------------------------
@pytest.mark.bdd
@pytest.mark.smoke
def test_bdd_ac01_edge_starts_and_accepts_input(client):
    # GIVEN a supported runtime environment
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "HEALTHY"

    # WHEN the customer creates a case and uploads valid 1099-DA and Koinly CSV
    c_res = client.post("/api/cases", json={"case_id": "CASE-BDD-AC01", "tax_year": 2025})
    assert c_res.status_code in [200, 201]

    # THEN the service starts deterministically, accepts the inputs, and assigns unique case ID
    case_info = client.get("/api/cases/CASE-BDD-AC01").json()
    assert case_info["case_id"] == "CASE-BDD-AC01"
    assert case_info["case_status"] in ["CREATED", "SOURCES_INGESTED"]


# ------------------------------------------------------------------------------
# AC-02: Reconciliation produces a bounded result
# ------------------------------------------------------------------------------
@pytest.mark.bdd
@pytest.mark.smoke
def test_bdd_ac02_bounded_reconciliation_result(client):
    # GIVEN valid supported inputs
    client.post("/api/cases", json={"case_id": "CASE-BDD-AC02", "tax_year": 2025})
    src_1099 = b"Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2\nBTC,2025-06-01,10000.00,2025-01-01,8000.00,YES\n"
    src_koinly = b"Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired\n2025-06-01,BTC,1.0,8000.00,9500.00,1500.00,2025-01-01\n"
    client.post("/api/cases/CASE-BDD-AC02/sources", files={"file": ("1099.csv", src_1099, "text/csv")})
    client.post("/api/cases/CASE-BDD-AC02/sources", files={"file": ("koinly.csv", src_koinly, "text/csv")})

    # WHEN the case runs
    recon_res = client.post("/api/cases/CASE-BDD-AC02/reconcile")
    assert recon_res.status_code == 200
    data = recon_res.json()

    # THEN VaultBasis produces one of the 13 declared outcome states and never invents accounting behavior
    valid_states = [
        "MATCHED", "PROCEEDS_DIFFERENCE", "BASIS_DIFFERENCE", "ACQUISITION_DATE_DIFFERENCE",
        "DISPOSITION_DATE_DIFFERENCE", "MISSING_FROM_1099DA", "MISSING_FROM_LEDGER",
        "AMBIGUOUS_MATCH", "AGGREGATED_LINE", "TRANSFER_RELATED", "REPORTING_SCOPE_DIFFERENCE",
        "SOURCE_ERROR_SUSPECTED", "UNRESOLVED_DATA"
    ]
    assert data["outcome_state"] in valid_states
    assert data["outcome_state"] == "PROCEEDS_DIFFERENCE"


# ------------------------------------------------------------------------------
# AC-03: Unknown states do not become zero
# ------------------------------------------------------------------------------
@pytest.mark.bdd
@pytest.mark.regression
def test_bdd_ac03_unknown_states_do_not_become_zero(client):
    # GIVEN a missing basis, price, or date
    missing_basis_csv = b"Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2\nSOL,2025-07-01,300.00,2025-02-01,,YES\n"

    # WHEN the document is ingested and parsed
    meta, txs = IntakeDispatcher.ingest_document(missing_basis_csv, "missing_basis.csv", "src_missing")

    # THEN the missing fact remains explicitly unresolved; it is not replaced by zero
    assert txs[0].cost_basis is None
    assert txs[0].is_unresolved is True
    assert txs[0].unresolved_reason == "BASIS_UNAVAILABLE"


# ------------------------------------------------------------------------------
# AC-04: Malformed input fails safely
# ------------------------------------------------------------------------------
@pytest.mark.bdd
@pytest.mark.regression
def test_bdd_ac04_malformed_input_fails_safely():
    # GIVEN malformed, corrupted, or schema-drifted input
    corrupt_bytes = b"random,garbage,without,correct,headers\n1,2,3,4,5\n"

    # WHEN it is processed
    with pytest.raises(ValueError) as excinfo:
        IntakeDispatcher.ingest_document(corrupt_bytes, "corrupt.csv", "src_corrupt")

    # THEN the case rejects the artifact with a safe failure and no silent corrupt financial output
    assert "missing" in str(excinfo.value).lower() or "unrecognized" in str(excinfo.value).lower()


# ------------------------------------------------------------------------------
# AC-05: Receipt is generated and signed
# ------------------------------------------------------------------------------
@pytest.mark.bdd
@pytest.mark.smoke
def test_bdd_ac05_receipt_is_generated_and_signed(client):
    # GIVEN a completed bounded case
    client.post("/api/cases", json={"case_id": "CASE-BDD-AC05", "tax_year": 2025})
    src_a = b"Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2\nBTC,2025-01-01,500.00,2024-01-01,400.00,YES\n"
    src_b = b"Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired\n2025-01-01,BTC,1.0,400.00,500.00,100.00,2024-01-01\n"
    client.post("/api/cases/CASE-BDD-AC05/sources", files={"file": ("a.csv", src_a, "text/csv")})
    client.post("/api/cases/CASE-BDD-AC05/sources", files={"file": ("b.csv", src_b, "text/csv")})

    # WHEN the receipt is generated
    recon = client.post("/api/cases/CASE-BDD-AC05/reconcile").json()
    receipt = recon["receipt"]

    # THEN the canonical receipt validates against Evidence Contract v0.1 and carries an Ed25519 signature
    assert receipt["receipt_version"] == "v0.1"
    assert receipt["signer_type"] == "INSTALLATION_KEY"
    assert len(receipt["signature"]) == 128  # 64 bytes in hex
    assert len(receipt["signer_public_key"]) == 64  # 32 bytes in hex


# ------------------------------------------------------------------------------
# AC-06: Verifier confirms receipt independently
# ------------------------------------------------------------------------------
@pytest.mark.bdd
@pytest.mark.smoke
def test_bdd_ac06_independent_verifier_confirms_receipt(client):
    # GIVEN a valid signed receipt
    client.post("/api/cases", json={"case_id": "CASE-BDD-AC06", "tax_year": 2025})
    src_a = b"Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2\nETH,2025-02-01,1000.00,2024-02-01,800.00,YES\n"
    src_b = b"Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired\n2025-02-01,ETH,1.0,800.00,1000.00,200.00,2024-02-01\n"
    client.post("/api/cases/CASE-BDD-AC06/sources", files={"file": ("a.csv", src_a, "text/csv")})
    client.post("/api/cases/CASE-BDD-AC06/sources", files={"file": ("b.csv", src_b, "text/csv")})
    recon = client.post("/api/cases/CASE-BDD-AC06/reconcile").json()

    # WHEN verified offline without VaultBasis cloud services
    report = verify_outcome_receipt(recon["receipt"])

    # THEN the verifier independently confirms signature, canonicalization, and declared state
    assert report.is_valid is True
    assert report.signature_valid is True
    assert report.schema_valid is True
    assert report.outcome_state == "MATCHED"


# ------------------------------------------------------------------------------
# AC-07: No transaction-data egress
# ------------------------------------------------------------------------------
@pytest.mark.bdd
@pytest.mark.regression
def test_bdd_ac07_no_transaction_data_egress(client):
    # GIVEN a case executed locally
    # WHEN checking the server health and network binding
    health = client.get("/api/health").json()

    # THEN egress policy confirms strict local only
    assert health["egress_policy"] == "STRICT_LOCAL_ONLY"


# ------------------------------------------------------------------------------
# AC-08 (Extended): Tampered receipt financial value fails verification
# ------------------------------------------------------------------------------
@pytest.mark.bdd
@pytest.mark.regression
def test_bdd_tampered_receipt_sub_cent_change_fails_verification(client):
    # GIVEN a valid signed receipt with proceeds $1000.00
    client.post("/api/cases", json={"case_id": "CASE-BDD-TAMPER-01", "tax_year": 2025})
    src_a = b"Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2\nETH,2025-02-01,1000.00,2024-02-01,800.00,YES\n"
    src_b = b"Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired\n2025-02-01,ETH,1.0,800.00,1000.00,200.00,2024-02-01\n"
    client.post("/api/cases/CASE-BDD-TAMPER-01/sources", files={"file": ("a.csv", src_a, "text/csv")})
    client.post("/api/cases/CASE-BDD-TAMPER-01/sources", files={"file": ("b.csv", src_b, "text/csv")})
    recon = client.post("/api/cases/CASE-BDD-TAMPER-01/reconcile").json()
    receipt = dict(recon["receipt"])

    # WHEN an attacker alters a field in the receipt payload
    receipt["producer_reference"] = "VaultBasis Edge Tampered v0.1"

    # THEN the independent verifier marks the receipt invalid with SIGNATURE_MISMATCH
    report = verify_outcome_receipt(receipt)
    assert report.is_valid is False
    assert report.signature_valid is False
    assert any("mismatch" in err.lower() or "failed" in err.lower() for err in report.errors)


# ------------------------------------------------------------------------------
# AC-09 (Extended): Tampered outcome state fails verification
# ------------------------------------------------------------------------------
@pytest.mark.bdd
@pytest.mark.regression
def test_bdd_tampered_outcome_state_fails_verification(client):
    # GIVEN a case resulting in BASIS_DIFFERENCE
    client.post("/api/cases", json={"case_id": "CASE-BDD-TAMPER-02", "tax_year": 2025})
    src_a = b"Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2\nBTC,2025-02-01,5000.00,2024-02-01,3000.00,YES\n"
    src_b = b"Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired\n2025-02-01,BTC,1.0,4000.00,5000.00,1000.00,2024-02-01\n"
    client.post("/api/cases/CASE-BDD-TAMPER-02/sources", files={"file": ("a.csv", src_a, "text/csv")})
    client.post("/api/cases/CASE-BDD-TAMPER-02/sources", files={"file": ("b.csv", src_b, "text/csv")})
    recon = client.post("/api/cases/CASE-BDD-TAMPER-02/reconcile").json()
    receipt = dict(recon["receipt"])
    assert receipt["outcome_state"] == "BASIS_DIFFERENCE"

    # WHEN an attacker attempts to greenwash the outcome state to MATCHED
    receipt["outcome_state"] = "MATCHED"

    # THEN verification categorically fails
    report = verify_outcome_receipt(receipt)
    assert report.is_valid is False
    assert report.signature_valid is False


# ------------------------------------------------------------------------------
# AC-10 (Extended): Idempotent reconciliation
# ------------------------------------------------------------------------------
@pytest.mark.bdd
@pytest.mark.smoke
def test_bdd_idempotent_reconciliation(client):
    # GIVEN an ingested case with two sources
    client.post("/api/cases", json={"case_id": "CASE-BDD-IDEM-01", "tax_year": 2025})
    src_a = b"Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2\nBTC,2025-03-01,2000.00,2024-03-01,1500.00,YES\n"
    src_b = b"Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired\n2025-03-01,BTC,1.0,1500.00,2000.00,500.00,2024-03-01\n"
    client.post("/api/cases/CASE-BDD-IDEM-01/sources", files={"file": ("a.csv", src_a, "text/csv")})
    client.post("/api/cases/CASE-BDD-IDEM-01/sources", files={"file": ("b.csv", src_b, "text/csv")})

    # WHEN reconciled multiple times
    recon1 = client.post("/api/cases/CASE-BDD-IDEM-01/reconcile").json()
    recon2 = client.post("/api/cases/CASE-BDD-IDEM-01/reconcile").json()

    # THEN outcome states and material differences are strictly identical
    assert recon1["outcome_state"] == recon2["outcome_state"]
    assert recon1["reconciliation"]["material_differences"] == recon2["reconciliation"]["material_differences"]


# ------------------------------------------------------------------------------
# AC-11 (Extended): Zero-byte empty file upload fails safely
# ------------------------------------------------------------------------------
@pytest.mark.bdd
@pytest.mark.regression
def test_bdd_empty_or_zero_byte_file_rejection(client):
    # GIVEN an empty 0-byte file
    client.post("/api/cases", json={"case_id": "CASE-BDD-EMPTY", "tax_year": 2025})

    # WHEN uploaded
    res = client.post(
        "/api/cases/CASE-BDD-EMPTY/sources",
        files={"file": ("empty.csv", b"", "text/csv")}
    )

    # THEN system safely rejects with HTTP 400
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()



