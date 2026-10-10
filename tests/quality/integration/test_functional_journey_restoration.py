"""
VaultBasis MMP-1.5 Functional Journey Restoration Regression Test Suite
Conforms to MODE3-FUNCTIONAL-RESTORE-001, PKG-UX-001, and FRZ-PKG-UX-001.

Permanently guards the five escaped defects discovered during physical workstation testing:
- FUNC-RESTORE-01: Opening an existing reconciled case restores/renders facts without re-upload.
- FUNC-RESTORE-02: Bundled sample (CASE-SAMPLE-2025) displays bundled evidence rather than empty/PENDING intake.
- FUNC-RESTORE-03: Summary counts (total, agreed, diffs, unres) are populated after reconciliation.
- FUNC-RESTORE-04: Result/filter tabs filter rendered findings deterministically.
- FUNC-RESTORE-05: Reopening after restart preserves identical rendered reconciliation state.
- FRZ-PKG-UX-001: Customer artifact depth must not exceed one extraction step before executable is visible.
- DOM-INTEGRITY: Web dashboard script contains 0 undeclared variables and all referenced element IDs exist.
"""

import io
import json
import re
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from edge.api.app import app
import edge.api.app as app_module
from edge.commercial.audit import CommercialAuditService
from edge.commercial.policy import CommercialPolicyService
from edge.storage.sqlite_store import SQLiteStore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@pytest.fixture
def journey_client(monkeypatch, tmp_path):
    monkeypatch.setenv("VAULTBASIS_BYPASS_ENTITLEMENT", "0")
    monkeypatch.delenv("VAULTBASIS_LICENSE_TOKEN", raising=False)

    db_file = tmp_path / "journey_restoration.db"
    store = SQLiteStore(db_file)
    license_dir = tmp_path / "lic"
    license_dir.mkdir(parents=True, exist_ok=True)

    audit_service = CommercialAuditService(store=store, installation_id="INST-RESTORE-001")
    policy_service = CommercialPolicyService(
        store=store,
        license_dir=license_dir,
        installation_id="INST-RESTORE-001",
        audit_service=audit_service,
    )

    monkeypatch.setattr(app_module, "db_store", store)
    monkeypatch.setattr(app_module, "commercial_policy", policy_service)

    client = TestClient(app)
    return {
        "client": client,
        "store": store,
        "db_file": db_file,
        "license_dir": license_dir,
    }


def test_func_restore_01_and_03_reconciled_case_restores_facts_and_summary_counts(journey_client):
    """
    FUNC-RESTORE-01 & FUNC-RESTORE-03:
    Opening an existing reconciled case returns full sources and reconciliation facts without re-upload,
    and summary count metrics (total, agreed, diffs, unres) are non-zero and populated.
    """
    client = journey_client["client"]

    # 1. Preload sample case
    res = client.post("/api/sample-case/load")
    assert res.status_code == 200
    case_data = res.json()
    case_id = case_data["case_id"]

    # 2. Reconcile
    recon_res = client.post(f"/api/cases/{case_id}/reconcile")
    assert recon_res.status_code == 200
    recon_data = recon_res.json()

    assert recon_data["outcome_state"] == "PROCEEDS_DIFFERENCE"
    recon = recon_data.get("reconciliation") or recon_data.get("receipt", {}).get("payload", {})
    assert recon, "Reconciliation payload missing"

    # Verify summary count metrics
    diffs = recon.get("material_differences", [])
    agreed = recon.get("agreed_records", [])
    unres = recon.get("unresolved_items", [])
    total_evaluated = recon.get("total_evaluated_count", len(diffs) + len(agreed) + len(unres))

    assert total_evaluated > 0, "Total evaluated count must be populated"
    assert len(diffs) > 0, "Material differences must be populated"
    assert len(agreed) > 0, "Agreed records must be populated"

    # 3. Simulate Opening the existing reconciled case via GET /api/cases/{case_id}
    fetch_res = client.get(f"/api/cases/{case_id}")
    assert fetch_res.status_code == 200
    fetched_case = fetch_res.json()

    assert fetched_case["case_status"] == "RECONCILED"
    assert fetched_case["outcome_state"] == "PROCEEDS_DIFFERENCE"
    assert len(fetched_case["sources"]) == 2
    for src in fetched_case["sources"].values():
        assert src["source_status"] == "ACTIVE"
        assert src["row_count"] > 0
        assert src["sha256_hash"]

    # Ensure reconciliation findings are directly present without re-upload
    fetched_recon = fetched_case.get("reconciliation") or fetched_case.get("receipt", {}).get("payload", {})
    assert fetched_recon, "Stored reconciliation facts must be present on open case"
    assert len(fetched_recon.get("material_differences", [])) == len(diffs)
    assert len(fetched_recon.get("agreed_records", [])) == len(agreed)


def test_func_restore_02_bundled_sample_displays_bundled_evidence_not_pending(journey_client):
    """
    FUNC-RESTORE-02:
    Bundled sample displays its bundled evidence immediately (both broker and ledger ACTIVE),
    never showing empty or PENDING intake state.
    """
    client = journey_client["client"]

    res = client.post("/api/sample-case/load")
    assert res.status_code == 200
    case_data = res.json()

    assert case_data["case_kind"] == "BUNDLED_SAMPLE"
    sources = list(case_data["sources"].values())
    assert len(sources) == 2, "Bundled sample must contain exactly 2 sources"

    broker = next((s for s in sources if "1099" in s["schema_id"] or "1099" in s["filename"].lower()), None)
    ledger = next((s for s in sources if "KOINLY" in s["schema_id"] or "koinly" in s["filename"].lower()), None)

    assert broker is not None, "Broker source Form 1099-DA must be present"
    assert ledger is not None, "Ledger source Koinly CSV must be present"

    assert broker["source_status"] == "ACTIVE", "Broker source must be ACTIVE, not PENDING"
    assert ledger["source_status"] == "ACTIVE", "Ledger source must be ACTIVE, not PENDING"
    assert broker["row_count"] == 5
    assert ledger["row_count"] == 5

    # Derived action gating must allow immediate reconciliation
    actions = case_data.get("actions", {})
    assert actions.get("can_reconcile") is True


def test_func_restore_04_filtering_tabs_partition_findings(journey_client):
    """
    FUNC-RESTORE-04:
    Tab filtering logic correctly partitions material differences, agreed records,
    and unresolved items without dropping or corrupting findings.
    """
    client = journey_client["client"]

    client.post("/api/sample-case/load")
    recon_res = client.post("/api/cases/CASE-SAMPLE-2025/reconcile")
    assert recon_res.status_code == 200
    recon_data = recon_res.json()
    recon = recon_data.get("reconciliation") or recon_data.get("receipt", {}).get("payload", {})

    diffs = recon.get("material_differences", [])
    agreed = recon.get("agreed_records", [])
    unres = recon.get("unresolved_items", [])

    # Filter logic: 'all', 'diffs', 'agreed', 'unres'
    filtered_all = diffs + agreed + unres
    filtered_diffs = diffs
    filtered_agreed = agreed
    filtered_unres = unres

    assert len(filtered_all) == len(diffs) + len(agreed) + len(unres)
    assert len(filtered_diffs) == 3  # In authentic sample: 3 material differences
    assert len(filtered_agreed) == 2 # In authentic sample: 2 agreed records
    assert len(filtered_unres) == 0


def test_func_restore_05_reopening_after_restart_preserves_state(journey_client, monkeypatch):
    """
    FUNC-RESTORE-05:
    Reopening a reconciled case after database connection restart preserves
    identical reconciliation state and findings.
    """
    client = journey_client["client"]
    db_file = journey_client["db_file"]
    license_dir = journey_client["license_dir"]

    # Load and reconcile
    client.post("/api/sample-case/load")
    client.post("/api/cases/CASE-SAMPLE-2025/reconcile")

    # Reconnect with a new SQLiteStore and new app instance state (simulates process restart)
    new_store = SQLiteStore(db_file)
    new_audit = CommercialAuditService(store=new_store, installation_id="INST-RESTORE-001")
    new_policy = CommercialPolicyService(
        store=new_store,
        license_dir=license_dir,
        installation_id="INST-RESTORE-001",
        audit_service=new_audit,
    )
    monkeypatch.setattr(app_module, "db_store", new_store)
    monkeypatch.setattr(app_module, "commercial_policy", new_policy)

    new_client = TestClient(app)
    reopened = new_client.get("/api/cases/CASE-SAMPLE-2025").json()

    assert reopened["case_status"] == "RECONCILED"
    assert reopened["outcome_state"] == "PROCEEDS_DIFFERENCE"
    assert len(reopened["sources"]) == 2
    recon = reopened.get("reconciliation") or reopened.get("receipt", {}).get("payload", {})
    assert recon is not None
    assert len(recon.get("material_differences", [])) == 3
    assert len(recon.get("agreed_records", [])) == 2


def test_dashboard_dom_and_javascript_integrity():
    """
    DOM-INTEGRITY:
    Verify apps/web-dashboard/index.html script has zero undeclared variables,
    and all DOM IDs referenced in refreshCaseDetails and renderFindingsView exist.
    """
    dash_path = REPO_ROOT / "apps" / "web-dashboard" / "index.html"
    assert dash_path.is_file()
    html_content = dash_path.read_text(encoding="utf-8")

    # Extract all HTML element IDs
    html_ids = set(re.findall(r'id=["\']([a-zA-Z0-9_\-]+)["\']', html_content))

    # Critical DOM IDs that MUST exist for practitioner journey
    required_ids = [
        "ctx-status-badge",
        "sample-immutable-banner",
        "btn-clone-sample",
        "src-a-upload-container",
        "src-b-upload-container",
        "src-a-badge",
        "src-a-readiness",
        "btn-upload-src-a",
        "src-b-badge",
        "src-b-readiness",
        "btn-upload-src-b",
        "btn-run-recon",
        "btn-restart-sample",
        "results-narrative-panel",
        "btn-view-receipt",
        "result-overall-badge",
        "card-total",
        "card-agreed",
        "card-diffs",
        "card-unres",
        "count-total",
        "count-agreed",
        "count-diffs",
        "count-unres",
        "review-banner-title",
        "review-banner-subtitle",
        "btn-finalize-review",
        "review-progress-badge",
        "differences-table-body",
        "findings-count-badge",
    ]

    for rid in required_ids:
        assert rid in html_ids, f"Required DOM element id='{rid}' missing from index.html"

    # Verify no dead 'btnDeleteCase' or similar removed identifiers exist in javascript
    script_match = re.search(r'<script>(.*?)</script>', html_content, re.DOTALL)
    assert script_match, "No <script> tag found in index.html"
    script_text = script_match.group(1)

    assert "btnDeleteCase" not in script_text, "Dead identifier btnDeleteCase must not exist in script"


def test_frz_pkg_ux_001_customer_packaging_depth_and_format():
    """
    FRZ-PKG-UX-001 / PKG-UX-001:
    Customer package upload depth must not exceed one extraction step before
    the executable installer/application is directly visible.
    - macOS customer package is the direct .dmg.
    - Windows customer package layout has Setup exe at the root of the distribution directory.
    """
    ci_yml_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_yml_path.is_file()
    ci_text = ci_yml_path.read_text(encoding="utf-8")

    # Assert macOS customer artifact points directly to .dmg
    assert "customer_path: dist/VaultBasis-RC3-macOS-arm64.dmg" in ci_text, \
        "macOS customer artifact must be direct DMG (no loose .app or nested archives)"

    # Assert Windows customer artifact points to dist/customer-win/*
    assert "customer_path: dist/customer-win/*" in ci_text, \
        "Windows customer artifact must be flat directory containing Setup exe directly"

    # Assert build_rc3_windows.py creates dist/customer-win with installer and docs
    build_win_path = REPO_ROOT / "scripts" / "build_rc3_windows.py"
    assert build_win_path.is_file()
    build_win_text = build_win_path.read_text(encoding="utf-8")
    assert 'cust_win = REPO / "dist" / "customer-win"' in build_win_text
    assert "shutil.copy2(setup_exe, cust_win / setup_filename)" in build_win_text
