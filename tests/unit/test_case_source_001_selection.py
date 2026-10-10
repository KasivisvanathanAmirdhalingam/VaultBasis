"""
Tests for CASE-SOURCE-001: Active Source Selection, Monotonic Invalidation, and Confirmation Prerequisite.

Invariants Verified:
1. Exactly one ACTIVE broker source and one ACTIVE ledger source participate in reconciliation.
2. First source of a role becomes ACTIVE automatically.
3. Additional same-role source becomes INACTIVE.
4. No upload silently replaces an ACTIVE source.
5. Practitioner explicitly selects replacement via POST /sources/{source_id}/select.
6. Previously active source becomes SUPERSEDED.
7. SUPERSEDED source may later be explicitly re-selected.
8. Zero or multiple ACTIVE sources fail closed.
9. Any new relevant source upload increments source_revision.
10. Any source-selection change increments source_revision.
11. Confirmation binds exact active source set hash, current source_revision, and UTC timestamp.
12. Reconciliation requires confirmed_hash == current_source_set_hash AND confirmed_revision == source_revision,
    otherwise fails with HTTP 412 CONFIRMATION_REQUIRED.
13. Inactive source upload invalidates prior confirmation via source_revision counter even when active hash is unchanged.
14. Signed receipt binds exact active source IDs and hashes under existing frozen receipt-v0.1 schema.
15. Middleware security: Route protection for /confirm-sources and /sources/{source_id}/select.
"""
import pytest
from fastapi.testclient import TestClient

from edge.api.app import app
from apps.verifier.verify_receipt import verify_outcome_receipt


SAMPLE_BROKER_V1 = b"""Property,Units,Date sold,Proceeds,Date acquired,Cost basis,Box 2
BTC,1.0,2025-11-20,18400.00,2025-02-11,12100.00,YES
"""

SAMPLE_LEDGER_V1 = b"""Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired
2025-11-20,BTC,1.0,16300.00,18400.00,2100.00,2025-02-11
"""

SAMPLE_LEDGER_V2_CORRECTED = b"""Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired
2025-11-20,BTC,1.0,12100.00,18400.00,6300.00,2025-02-11
"""


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("VAULTBASIS_BYPASS_ENTITLEMENT", "1")
    return TestClient(app)


def test_src_01_and_02_lifecycle_upload_states_and_revision(client):
    """SRC-01 & SRC-02: First source of role is ACTIVE; additional is INACTIVE and increments revision."""
    case_res = client.post("/api/cases", json={"case_id": "CASE-SRC-01", "tax_year": 2025})
    assert case_res.status_code in [200, 201]

    # 1. Upload first broker (B1)
    b1_res = client.post(
        "/api/cases/CASE-SRC-01/sources",
        files={"file": ("broker_v1.csv", SAMPLE_BROKER_V1, "text/csv")},
        data={"source_type": "AUTO"}
    )
    assert b1_res.status_code == 200
    b1_meta = b1_res.json()["source"]
    assert b1_meta["source_status"] == "ACTIVE"

    # 2. Upload first ledger (L1)
    l1_res = client.post(
        "/api/cases/CASE-SRC-01/sources",
        files={"file": ("ledger_v1.csv", SAMPLE_LEDGER_V1, "text/csv")},
        data={"source_type": "AUTO"}
    )
    assert l1_res.status_code == 200
    l1_meta = l1_res.json()["source"]
    assert l1_meta["source_status"] == "ACTIVE"

    case_data = client.get("/api/cases/CASE-SRC-01").json()
    assert case_data["source_revision"] == 3  # Initial creation (1) + B1 (2) + L1 (3)

    # 3. Upload second ledger (L2 - corrected)
    l2_res = client.post(
        "/api/cases/CASE-SRC-01/sources",
        files={"file": ("ledger_v2_corrected.csv", SAMPLE_LEDGER_V2_CORRECTED, "text/csv")},
        data={"source_type": "AUTO"}
    )
    assert l2_res.status_code == 200
    l2_meta = l2_res.json()["source"]
    # Invariant: Second source becomes INACTIVE, does NOT silently overwrite L1!
    assert l2_meta["source_status"] == "INACTIVE"

    # Invariant: source_revision incremented on upload
    case_data = client.get("/api/cases/CASE-SRC-01").json()
    assert case_data["source_revision"] == 4
    # L1 remains ACTIVE
    assert case_data["sources"][l1_meta["source_id"]]["source_status"] == "ACTIVE"


def test_src_03_and_04_confirmation_prerequisite_and_invalidation(client):
    """
    SRC-03 & SRC-04:
    - Reconcile before confirmation fails with 412 CONFIRMATION_REQUIRED.
    - Confirmation allows reconcile.
    - Uploading even an INACTIVE source increments source_revision and invalidates confirmation.
    """
    case_id = "CASE-SRC-CONF-01"
    client.post("/api/cases", json={"case_id": case_id, "tax_year": 2025})

    b1_id = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker.csv", SAMPLE_BROKER_V1, "text/csv")},
    ).json()["source"]["source_id"]

    l1_id = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger.csv", SAMPLE_LEDGER_V1, "text/csv")},
    ).json()["source"]["source_id"]

    # Invariant 412: Reconcile without practitioner confirmation MUST fail
    recon_fail = client.post(f"/api/cases/{case_id}/reconcile")
    assert recon_fail.status_code == 412
    assert recon_fail.json()["detail"]["code"] == "CONFIRMATION_REQUIRED"

    # Practitioner confirms sources
    conf_res = client.post(f"/api/cases/{case_id}/confirm-sources")
    assert conf_res.status_code == 200
    conf_data = conf_res.json()
    assert conf_data["status"] == "CONFIRMED"
    assert conf_data["confirmed_source_revision"] == 3
    initial_hash = conf_data["confirmed_source_set_hash"]

    # Now reconciliation succeeds
    recon_ok = client.post(f"/api/cases/{case_id}/reconcile")
    assert recon_ok.status_code == 200
    assert recon_ok.json()["outcome_state"] == "BASIS_DIFFERENCE"

    # CPA now uploads corrected ledger L2 (which becomes INACTIVE initially)
    # The active source set hash does NOT change (still B1 + L1), but source_revision increments!
    client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_v2.csv", SAMPLE_LEDGER_V2_CORRECTED, "text/csv")},
    )

    # Invariant: Even though active sources did not change, reconciliation is BLOCKED (412)
    # because current source_revision > confirmed_source_revision!
    recon_invalidated = client.post(f"/api/cases/{case_id}/reconcile")
    assert recon_invalidated.status_code == 412
    assert recon_invalidated.json()["detail"]["code"] == "CONFIRMATION_REQUIRED"
    assert recon_invalidated.json()["detail"]["current_source_revision"] == 4
    assert recon_invalidated.json()["detail"]["confirmed_source_revision"] == 3


def test_src_05_and_06_explicit_selection_and_supersession(client):
    """
    SRC-05 & SRC-06:
    - Explicitly selecting L2 transitions L1 to SUPERSEDED and L2 to ACTIVE.
    - Selecting increments source_revision.
    - Confirmation binds new active source set.
    - Reconcile now evaluates B1 and L2 (resulting in MATCHED outcome).
    """
    case_id = "CASE-SRC-SELECT-01"
    client.post("/api/cases", json={"case_id": case_id, "tax_year": 2025})

    b1_id = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker.csv", SAMPLE_BROKER_V1, "text/csv")},
    ).json()["source"]["source_id"]

    l1_id = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_v1.csv", SAMPLE_LEDGER_V1, "text/csv")},
    ).json()["source"]["source_id"]

    l2_id = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_v2_corrected.csv", SAMPLE_LEDGER_V2_CORRECTED, "text/csv")},
    ).json()["source"]["source_id"]

    # Explicitly select L2 as the active ledger
    sel_res = client.post(f"/api/cases/{case_id}/sources/{l2_id}/select")
    assert sel_res.status_code == 200
    assert sel_res.json()["status"] == "SELECTED"
    assert sel_res.json()["new_status"] == "ACTIVE"

    case_state = client.get(f"/api/cases/{case_id}").json()
    assert case_state["sources"][l2_id]["source_status"] == "ACTIVE"
    assert case_state["sources"][l1_id]["source_status"] == "SUPERSEDED"

    # Confirm new source selection
    conf_res = client.post(f"/api/cases/{case_id}/confirm-sources")
    assert conf_res.status_code == 200
    assert conf_res.json()["active_sources"]["ledger"] == l2_id

    # Reconcile B1 + L2 -> Because costs match, outcome is MATCHED!
    recon_res = client.post(f"/api/cases/{case_id}/reconcile")
    assert recon_res.status_code == 200
    assert recon_res.json()["outcome_state"] == "MATCHED"

    # Receipt binds EXACT active sources (B1 and L2)
    receipt = recon_res.json()["receipt"]
    assert set(receipt["source_ids"]) == {b1_id, l2_id}
    assert l1_id not in receipt["source_ids"]

    # Verify receipt passes standalone offline verifier
    vr = verify_outcome_receipt(receipt)
    assert vr.is_valid is True


def test_src_07_superseded_source_can_be_reselected(client):
    """SRC-07: A previously SUPERSEDED source may be explicitly re-selected by practitioner."""
    case_id = "CASE-SRC-RESELECT-01"
    client.post("/api/cases", json={"case_id": case_id, "tax_year": 2025})

    b1_id = client.post(f"/api/cases/{case_id}/sources", files={"file": ("b.csv", SAMPLE_BROKER_V1, "text/csv")}).json()["source"]["source_id"]
    l1_id = client.post(f"/api/cases/{case_id}/sources", files={"file": ("l1.csv", SAMPLE_LEDGER_V1, "text/csv")}).json()["source"]["source_id"]
    l2_id = client.post(f"/api/cases/{case_id}/sources", files={"file": ("l2.csv", SAMPLE_LEDGER_V2_CORRECTED, "text/csv")}).json()["source"]["source_id"]

    # Select L2 -> L1 becomes SUPERSEDED
    client.post(f"/api/cases/{case_id}/sources/{l2_id}/select")
    case1 = client.get(f"/api/cases/{case_id}").json()
    assert case1["sources"][l1_id]["source_status"] == "SUPERSEDED"
    assert case1["sources"][l2_id]["source_status"] == "ACTIVE"

    # Practitioner changes their mind: Re-select L1!
    re_sel = client.post(f"/api/cases/{case_id}/sources/{l1_id}/select")
    assert re_sel.status_code == 200
    case2 = client.get(f"/api/cases/{case_id}").json()
    # Invariant: L1 is now ACTIVE again, L2 is now SUPERSEDED
    assert case2["sources"][l1_id]["source_status"] == "ACTIVE"
    assert case2["sources"][l2_id]["source_status"] == "SUPERSEDED"


def test_src_08_middleware_security_on_new_endpoints(client):
    """SRC-08: Security middleware rejects invalid Host, bad Origin, and Origin: null without token."""
    case_id = "CASE-SEC-001"
    client.post("/api/cases", json={"case_id": case_id, "tax_year": 2025})

    # Host validation: DNS rebinding defense
    bad_host_res = client.post(
        f"/api/cases/{case_id}/confirm-sources",
        headers={"Host": "evil-attacker.com"}
    )
    assert bad_host_res.status_code == 400

    # Cross-Origin mutation defense
    bad_origin_res = client.post(
        f"/api/cases/{case_id}/confirm-sources",
        headers={"Origin": "https://evil-attacker.com"}
    )
    assert bad_origin_res.status_code == 403

    # Origin: null defense (local file HTML attack defense)
    null_origin_res = client.post(
        f"/api/cases/{case_id}/confirm-sources",
        headers={"Origin": "null"}
    )
    assert null_origin_res.status_code == 403
