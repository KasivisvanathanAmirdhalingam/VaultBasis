"""
VaultBasis MMP-1.5 Firm & Workspace Identity Test Suite
Tests MMP15-ORG-001:
1. Organization, workspace, and practitioner domain validation
2. Regulated identifier format validation (PTIN: PXXXXXXXX, EFIN: XXXXXX)
3. Regulated identifier isolation invariant (PTIN & EFIN 100% stripped from public projections)
4. Diagnostic redaction rules (PTIN & EFIN safely masked)
5. SQLite persistence & update round-trips
6. REST API endpoints (GET, POST, DELETE /api/firm/identity)
7. Fail-closed validation on invalid regulated identifiers
"""

import pytest
from fastapi.testclient import TestClient

from edge.api.app import app, db_store, firm_identity_service
from edge.commercial.identity import FirmIdentity, FirmIdentityService
from edge.storage.sqlite_store import SQLiteStore


@pytest.fixture
def temp_identity_service(tmp_path):
    db_file = tmp_path / "identity_test.db"
    store = SQLiteStore(db_file)
    return FirmIdentityService(store), store


@pytest.fixture
def client(monkeypatch, tmp_path):
    test_db = tmp_path / "app_identity_test.db"
    store = SQLiteStore(test_db)
    service = FirmIdentityService(store)
    monkeypatch.setattr("edge.api.app.db_store", store)
    monkeypatch.setattr("edge.api.app.firm_identity_service", service)
    return TestClient(app)


# ------------------------------------------------------------------------------
# 1. Domain Model Invariants
# ------------------------------------------------------------------------------

def test_firm_identity_valid_creation():
    ident = FirmIdentity(
        organization_id="ORG-ACME-TAX",
        firm_name="Acme Advisory Services LLP",
        office_id="OFFICE-NYC-01",
        workspace_id="WS-CRYPTO-TAX",
        preparer_id="PREP-JSMITH",
        display_name="Jane Smith, CPA",
        ptin="P01234567",
        efin="123456",
    )
    assert ident.organization_id == "ORG-ACME-TAX"
    assert ident.ptin == "P01234567"
    assert ident.efin == "123456"
    assert ident.created_at is not None
    assert ident.updated_at is not None


def test_firm_identity_ptin_validation():
    # Valid
    ident = FirmIdentity(
        organization_id="ORG-TEST",
        firm_name="Test Firm",
        preparer_id="PREP-01",
        display_name="Preparer",
        ptin="p98765432",  # lowercase should be normalized to uppercase
    )
    assert ident.ptin == "P98765432"

    # Invalid PTIN formats
    with pytest.raises(ValueError, match="Invalid PTIN format"):
        FirmIdentity(organization_id="ORG-TEST", firm_name="Test Firm", preparer_id="P1", display_name="Prep", ptin="12345678")

    with pytest.raises(ValueError, match="Invalid PTIN format"):
        FirmIdentity(organization_id="ORG-TEST", firm_name="Test Firm", preparer_id="P1", display_name="Prep", ptin="P123")


def test_firm_identity_efin_validation():
    # Valid
    ident = FirmIdentity(
        organization_id="ORG-TEST",
        firm_name="Test Firm",
        preparer_id="PREP-01",
        display_name="Preparer",
        efin="654321",
    )
    assert ident.efin == "654321"

    # Invalid EFIN formats
    with pytest.raises(ValueError, match="Invalid EFIN format"):
        FirmIdentity(organization_id="ORG-TEST", firm_name="Test Firm", preparer_id="P1", display_name="Prep", efin="12345")  # 5 digits

    with pytest.raises(ValueError, match="Invalid EFIN format"):
        FirmIdentity(organization_id="ORG-TEST", firm_name="Test Firm", preparer_id="P1", display_name="Prep", efin="ABC123")


def test_regulated_identifier_public_isolation():
    """
    CRITICAL SECURITY INVARIANT:
    Public metadata MUST NOT contain PTIN or EFIN raw values under any circumstances.
    """
    ident = FirmIdentity(
        organization_id="ORG-ACME",
        firm_name="Acme CPA",
        preparer_id="PREP-01",
        display_name="Jane Smith",
        ptin="P01234567",
        efin="123456",
    )
    pub = ident.to_public_metadata()
    assert "ptin" not in pub
    assert "efin" not in pub
    assert pub["has_ptin_configured"] is True
    assert pub["has_efin_configured"] is True
    assert pub["organization_id"] == "ORG-ACME"


def test_diagnostic_redaction():
    ident = FirmIdentity(
        organization_id="ORG-ACME",
        firm_name="Acme CPA",
        preparer_id="PREP-01",
        display_name="Jane Smith",
        ptin="P01234567",
        efin="123456",
    )
    diag = ident.to_redacted_diagnostic()
    assert diag["ptin_masked"] == "P*****567"
    assert diag["efin_masked"] == "***456"
    assert "P01234567" not in str(diag)
    assert "123456" not in str(diag)


# ------------------------------------------------------------------------------
# 2. Persistence Service Tests
# ------------------------------------------------------------------------------

def test_identity_service_persistence(temp_identity_service):
    service, store = temp_identity_service

    assert service.get_identity() is None
    assert service.get_public_identity() is None

    # Save identity
    ident = FirmIdentity(
        organization_id="ORG-PERSIST-01",
        firm_name="Persistence Firm LLC",
        office_id="OFFICE-BOS",
        workspace_id="WS-DEV",
        preparer_id="PREP-ALICE",
        display_name="Alice Brown, EA",
        ptin="P87654321",
        efin="998877",
    )
    service.save_identity(ident)

    # Reload from DB
    loaded = service.get_identity()
    assert loaded is not None
    assert loaded.organization_id == "ORG-PERSIST-01"
    assert loaded.firm_name == "Persistence Firm LLC"
    assert loaded.ptin == "P87654321"
    assert loaded.efin == "998877"

    # Update identity
    ident.display_name = "Alice Brown, CPA, EA"
    service.save_identity(ident)
    updated = service.get_identity()
    assert updated.display_name == "Alice Brown, CPA, EA"

    # Clear identity
    service.clear_identity()
    assert service.get_identity() is None


# ------------------------------------------------------------------------------
# 3. REST API Integration Tests
# ------------------------------------------------------------------------------

def test_api_firm_identity_lifecycle(client):
    # 1. Unconfigured state
    res_get1 = client.get("/api/firm/identity")
    assert res_get1.status_code == 200
    assert res_get1.json()["configured"] is False

    # 2. Update identity
    payload = {
        "organization_id": "ORG-ALPHA-TAX",
        "firm_name": "Alpha Tax Partners",
        "office_id": "OFFICE-WEST",
        "workspace_id": "WS-CRYPTO",
        "preparer_id": "PREP-JOHN",
        "display_name": "John Doe, CPA",
        "ptin": "P11223344",
        "efin": "556677",
    }
    res_post = client.post("/api/firm/identity", json=payload)
    assert res_post.status_code == 200
    post_data = res_post.json()
    assert post_data["status"] == "SAVED"
    assert post_data["configured"] is True
    assert post_data["organization_id"] == "ORG-ALPHA-TAX"
    assert "ptin" not in post_data
    assert "efin" not in post_data
    assert post_data["has_ptin_configured"] is True
    assert post_data["has_efin_configured"] is True

    # 3. Get populated public metadata
    res_get2 = client.get("/api/firm/identity")
    assert res_get2.status_code == 200
    get_data = res_get2.json()
    assert get_data["configured"] is True
    assert get_data["firm_name"] == "Alpha Tax Partners"
    assert "ptin" not in get_data
    assert "efin" not in get_data

    # 4. Clear identity
    res_del = client.delete("/api/firm/identity")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "CLEARED"

    # 5. Verify unconfigured again
    res_get3 = client.get("/api/firm/identity")
    assert res_get3.json()["configured"] is False


def test_api_firm_identity_invalid_ptin_rejected(client):
    payload = {
        "organization_id": "ORG-ALPHA-TAX",
        "firm_name": "Alpha Tax Partners",
        "preparer_id": "PREP-JOHN",
        "display_name": "John Doe, CPA",
        "ptin": "INVALID-PTIN-STRING",
    }
    res = client.post("/api/firm/identity", json=payload)
    assert res.status_code == 422
