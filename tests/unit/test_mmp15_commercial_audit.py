"""
VaultBasis MMP-1.5 Commercial & Administrative Audit Event Log Test Suite
Tests MMP15-AUD-001:
1. Append-only administrative audit event recording in SQLite
2. Cryptographic hash chaining across sequence of events
3. Tamper-evidence detection (detects altered or deleted history)
4. Integration with license installation and firm profile lifecycle
5. Regulated identifier isolation in audit logs (PTIN/EFIN masked, never raw)
6. REST API endpoint GET /api/commercial/audit
"""

import json
import sqlite3
import pytest
from fastapi.testclient import TestClient

from edge.api.app import app
from edge.commercial.audit import (
    AuditEvent,
    AuditEventType,
    CommercialAuditService,
)
from edge.commercial.diagnostics import DiagnosticPackager
from edge.commercial.identity import FirmIdentity, FirmIdentityService
from edge.commercial.policy import CommercialPolicyService
from edge.storage.sqlite_store import SQLiteStore


@pytest.fixture
def audit_env(tmp_path):
    db_file = tmp_path / "audit_test.db"
    store = SQLiteStore(db_file)
    audit_service = CommercialAuditService(store=store, installation_id="INST-AUDIT-001")
    return store, audit_service


@pytest.fixture
def client(monkeypatch, tmp_path):
    test_db = tmp_path / "app_audit_test.db"
    store = SQLiteStore(test_db)
    audit_service = CommercialAuditService(store=store, installation_id="INST-APP-AUDIT")
    policy_service = CommercialPolicyService(
        store=store,
        license_dir=tmp_path / "lic",
        installation_id="INST-APP-AUDIT",
        audit_service=audit_service,
    )
    identity_service = FirmIdentityService(store, audit_service=audit_service)
    packager = DiagnosticPackager(store, policy_service, identity_service)

    monkeypatch.setattr("edge.api.app.db_store", store)
    monkeypatch.setattr("edge.api.app.commercial_audit_service", audit_service)
    monkeypatch.setattr("edge.api.app.commercial_policy", policy_service)
    monkeypatch.setattr("edge.api.app.firm_identity_service", identity_service)
    monkeypatch.setattr("edge.api.app.diagnostic_packager", packager)
    return TestClient(app)


def test_audit_event_recording_and_hash_chaining(audit_env):
    store, audit_service = audit_env

    # 1. Record genesis event
    ev1 = audit_service.record_event(
        AuditEventType.LICENSE_INSTALLED,
        actor_type="USER",
        actor_id="PREP-01",
        details={"tier": "STANDARD", "license_id": "LIC-001"},
    )
    assert ev1.previous_event_hash is None
    assert len(ev1.event_hash) == 64

    # 2. Record second event
    ev2 = audit_service.record_event(
        AuditEventType.FIRM_IDENTITY_CREATED,
        actor_type="USER",
        actor_id="PREP-01",
        details={"organization_id": "ORG-TEST"},
    )
    assert ev2.previous_event_hash == ev1.event_hash
    assert len(ev2.event_hash) == 64

    # 3. Record third event
    ev3 = audit_service.record_event(
        AuditEventType.DIAGNOSTIC_EXPORTED,
        actor_type="SYSTEM",
        actor_id="SYSTEM",
        details={"bundle_id": "DIAG-001"},
    )
    assert ev3.previous_event_hash == ev2.event_hash

    # 4. Verify chain integrity
    status = audit_service.verify_chain_integrity()
    assert status["valid"] is True
    assert status["event_count"] == 3
    assert status["broken_at"] is None


def test_audit_tamper_detection(audit_env):
    store, audit_service = audit_env

    # Record 3 events
    ev1 = audit_service.record_event(AuditEventType.LICENSE_INSTALLED, details={"tier": "STANDARD"})
    ev2 = audit_service.record_event(AuditEventType.FIRM_IDENTITY_CREATED, details={"org": "ORG-1"})
    ev3 = audit_service.record_event(AuditEventType.DIAGNOSTIC_EXPORTED, details={"id": "DIAG-1"})

    assert audit_service.verify_chain_integrity()["valid"] is True

    # Tamper with the middle event in SQLite
    with store._get_connection() as conn:
        conn.execute(
            "UPDATE commercial_audit_log SET details_json = ? WHERE event_id = ?",
            (json.dumps({"org": "TAMPERED-ORG"}), ev2.event_id),
        )

    # Verification must detect corruption
    status = audit_service.verify_chain_integrity()
    assert status["valid"] is False
    assert status["broken_at"] == ev2.event_id


def test_firm_identity_lifecycle_audit_emission(audit_env):
    store, audit_service = audit_env
    identity_service = FirmIdentityService(store, audit_service=audit_service)

    # Create identity with PTIN/EFIN
    ident = FirmIdentity(
        organization_id="ORG-ALPHA",
        firm_name="Alpha Firm",
        preparer_id="PREP-01",
        display_name="Preparer",
        ptin="P12345678",
        efin="654321",
    )
    identity_service.save_identity(ident)

    events = audit_service.get_events()
    assert len(events) == 1
    assert events[0].event_type == AuditEventType.FIRM_IDENTITY_CREATED
    # PTIN/EFIN must be masked in audit log details
    details_str = json.dumps(events[0].details)
    assert "P12345678" not in details_str
    assert "654321" not in details_str
    assert "P*****678" in details_str
    assert "***321" in details_str

    # Update identity
    ident.firm_name = "Alpha Firm Updated"
    identity_service.save_identity(ident)

    events_after_update = audit_service.get_events()
    assert len(events_after_update) == 2
    assert events_after_update[0].event_type == AuditEventType.FIRM_IDENTITY_UPDATED

    # Clear identity
    identity_service.clear_identity()
    events_after_del = audit_service.get_events()
    assert len(events_after_del) == 3
    assert events_after_del[0].event_type == AuditEventType.FIRM_IDENTITY_REMOVED


def test_api_commercial_audit_endpoint(client):
    # Trigger diagnostic export to generate an audit event
    res_diag = client.get("/api/system/diagnostic")
    assert res_diag.status_code == 200

    # Query audit endpoint
    res_audit = client.get("/api/commercial/audit")
    assert res_audit.status_code == 200
    data = res_audit.json()
    assert "events" in data
    assert "total_count" in data
    assert "chain_integrity" in data
    assert data["total_count"] >= 1
    assert data["chain_integrity"]["valid"] is True
    assert data["events"][0]["event_type"] == "DIAGNOSTIC_EXPORTED"
