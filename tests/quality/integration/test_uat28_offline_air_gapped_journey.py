import io
import json
import os
import socket
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from edge.api.app import app
from apps.verifier.verify_receipt import verify_outcome_receipt


class AirGapNetworkGuard:
    """
    Simulates a strict air-gapped environment by intercepting socket connections.
    Permits only loopback (127.0.0.1, localhost, ::1) for local IPC and test client calls.
    Any attempt to connect to external IPs or hostnames immediately raises an OSError
    and records the attempted outbound connection.
    """
    def __init__(self):
        self.original_connect = socket.socket.connect
        self.outbound_attempts: List[str] = []

    def __enter__(self):
        def guarded_connect(sock_self, address):
            host = address[0] if isinstance(address, tuple) else str(address)
            if host not in ("127.0.0.1", "localhost", "::1"):
                attempt = f"{host}:{address[1] if isinstance(address, tuple) and len(address) > 1 else '?'}"
                self.outbound_attempts.append(attempt)
                raise OSError(f"AIR-GAP BLOCKED: Attempted outbound network connection to {attempt}")
            return self.original_connect(sock_self, address)

        socket.socket.connect = guarded_connect
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        socket.socket.connect = self.original_connect


def test_uat28_offline_air_gapped_journey():
    """
    Permanent regression test for UAT-28 (Offline / Air-Gapped Customer Journey).
    
    Proves that the complete practitioner workflow operates 100% locally with zero external
    network connectivity, zero CDN/cloud dependencies, and zero phone-home licensing requests.
    
    Customer Journey Steps in Air-Gap:
    1. System launch & status check under network isolation.
    2. Evaluation activation (offline local monotonic license initialization).
    3. Sample case loading & inspection.
    4. Production case creation.
    5. Source document ingestion (1099-DA & Client Ledger).
    6. Deterministic reconciliation execution.
    7. Preliminary receipt verification (Rev 1).
    8. Professional review actions and annotation.
    9. Review finalization & Ed25519 signing (Rev 2).
    10. Multi-format artifact export (Receipt JSON, Findings CSV, Evidence Bundle ZIP).
    11. Independent standalone verification of exported receipt with zero runtime daemon dependencies.
    12. Querying existing case and receipts to prove full persistence in air-gap.
    13. Verification that zero outbound connections were attempted during the journey.
    """
    with AirGapNetworkGuard() as network_guard:
        client = TestClient(app)
        
        # 1. System Version & Status
        r_ver = client.get("/api/system/version")
        assert r_ver.status_code == 200
        ver_data = r_ver.json()
        assert ver_data["product"] == "VaultBasis"
        assert "version" in ver_data
        assert "compatibility" in ver_data

        # 2. Start Evaluation (offline local)
        r_eval = client.post("/api/commercial/start-evaluation", json={"customer_name": "CPA AirGap Firm"})
        assert r_eval.status_code == 200
        
        r_status = client.get("/api/commercial/status")
        assert r_status.status_code == 200
        status_data = r_status.json()
        assert status_data["licensed"] is True
        assert status_data.get("tier") == "EVALUATION"

        # 3. Load Sample Case
        r_sample = client.post("/api/sample-case/load")
        assert r_sample.status_code == 200
        sample_data = r_sample.json()
        assert "sample_case_id" in sample_data or "case_id" in sample_data

        # 4. Create Production Case
        case_id = "CASE-UAT28-AIRGAP-01"
        r_create = client.post("/api/cases", json={
            "case_id": case_id,
            "client_reference": "Off-Grid Digital Holdings LLC",
            "tax_year": 2025,
            "jurisdiction": "US",
        })
        assert r_create.status_code in (200, 201)

        # 5. Ingest Source Documents
        fixture_dir = Path("tests/fixtures/uat21")
        broker_bytes = (fixture_dir / "broker_realistic.csv").read_bytes()
        ledger_bytes = (fixture_dir / "ledger_realistic.csv").read_bytes()

        r_src_da = client.post(
            f"/api/cases/{case_id}/sources",
            files={"file": ("broker_realistic.csv", broker_bytes, "text/csv")},
            data={"declared_schema": "AUTO"},
        )
        assert r_src_da.status_code == 200
        assert r_src_da.json()["status"] == "INGESTED"

        r_src_ledger = client.post(
            f"/api/cases/{case_id}/sources",
            files={"file": ("ledger_realistic.csv", ledger_bytes, "text/csv")},
            data={"declared_schema": "AUTO"},
        )
        assert r_src_ledger.status_code == 200
        assert r_src_ledger.json()["status"] == "INGESTED"

        # 6. Reconcile -> Generates Rev 1 (Preliminary Receipt)
        client.post(f"/api/cases/{case_id}/confirm-sources")
        r_recon = client.post(f"/api/cases/{case_id}/reconcile")
        assert r_recon.status_code == 200
        recon_res = r_recon.json()
        assert recon_res["status"] == "RECONCILED"
        assert recon_res["revision"] == 1
        assert recon_res["human_review_state"] == "UNREVIEWED"

        rev1_receipt = recon_res["receipt"]
        assert rev1_receipt["revision"] == 1
        assert rev1_receipt["human_review_state"] == "UNREVIEWED"
        assert rev1_receipt.get("prior_receipt_id") is None
        assert rev1_receipt["ruleset_id"] == "VB_US_1099DA_2025_R1"

        # 7. Check Preliminary Receipt via GET
        r_rcpt1 = client.get(f"/api/cases/{case_id}/receipt")
        assert r_rcpt1.status_code == 200
        rcpt1_data = r_rcpt1.json()
        assert rcpt1_data["receipt_id"] == rev1_receipt["receipt_id"]

        # 8. Record Human Review Item
        diff_eth = next(d for d in rev1_receipt["material_differences"] if d["asset"] == "ETH")
        r_review = client.post(f"/api/cases/{case_id}/reviews", json={
            "finding_id": diff_eth["difference_id"],
            "disposition": "REVIEWED",
            "note": "Air-gapped review confirmed fee variance against broker statement.",
            "reviewer_reference": "CPA-AIRGAP-99"
        })
        assert r_review.status_code in (200, 201)

        # 9. Finalize Review (Rev 2)
        r_finalize = client.post(f"/api/cases/{case_id}/finalize-review")
        assert r_finalize.status_code == 200
        final_res = r_finalize.json()
        assert final_res["status"] == "REVIEW_FINALIZED"
        assert final_res["revision"] == 2
        assert final_res["human_review_state"] == "REVIEWED_ANNOTATED"
        assert final_res["prior_receipt_id"] == rev1_receipt["receipt_id"]

        rev2_receipt = final_res["receipt"]
        assert rev2_receipt["revision"] == 2
        assert rev2_receipt["human_review_state"] == "REVIEWED_ANNOTATED"
        assert rev2_receipt["prior_receipt_id"] == rev1_receipt["receipt_id"]

        # 10. Export Artifacts
        # 10a. Receipt JSON Export
        r_exp_rcpt = client.get(f"/api/cases/{case_id}/export/receipt")
        assert r_exp_rcpt.status_code == 200
        exported_rcpt = r_exp_rcpt.json()
        assert exported_rcpt["receipt_id"] == rev2_receipt["receipt_id"]

        # 10b. Findings CSV Export
        r_exp_csv = client.get(f"/api/cases/{case_id}/export/findings")
        assert r_exp_csv.status_code == 200
        assert "text/csv" in r_exp_csv.headers.get("content-type", "")

        # 10c. Evidence Package ZIP Export
        r_exp_pkg = client.get(f"/api/cases/{case_id}/export/package")
        assert r_exp_pkg.status_code == 200
        with zipfile.ZipFile(io.BytesIO(r_exp_pkg.content), "r") as zf:
            namelist = zf.namelist()
            assert any("receipt" in name.lower() for name in namelist)

        # 11. Standalone Verification in Air-Gap
        # Verify receipt cryptography using local verifier with zero network
        verifier_result = verify_outcome_receipt(exported_rcpt)
        assert verifier_result.is_valid is True
        assert verifier_result.signature_valid is True
        assert verifier_result.schema_valid is True

        # 12. Query Existing Case & Audit Trail
        r_case_reload = client.get(f"/api/cases/{case_id}")
        assert r_case_reload.status_code == 200
        assert r_case_reload.json()["case_id"] == case_id

        # 13. Strict Zero Outbound Network Assertion
        assert network_guard.outbound_attempts == [], (
            f"Air-gap violation! Outbound connection attempts detected: {network_guard.outbound_attempts}"
        )
