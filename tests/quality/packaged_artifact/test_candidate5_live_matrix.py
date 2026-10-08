"""
VaultBasis Edge — Packaged Candidate Live Artifact Regression Runner
Directly executes scenarios UAT-05 through UAT-12 over HTTP against the running packaged binary on http://127.0.0.1:8000.
"""

import json
import io
import zipfile
from pathlib import Path
import urllib.request
import urllib.parse
import mimetypes
import uuid


BASE_URL = "http://127.0.0.1:8000"


def post_json(endpoint: str, data: dict) -> dict:
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_multipart(endpoint: str, files: dict, form_data: dict = None) -> dict:
    boundary = uuid.uuid4().hex
    body = bytearray()
    
    if form_data:
        for k, v in form_data.items():
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode("utf-8"))
            body.extend(f"{v}\r\n".encode("utf-8"))
            
    for field_name, (filename, file_bytes) in files.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8"))
        body.extend(f"Content-Type: text/csv\r\n\r\n".encode("utf-8"))
        body.extend(file_bytes)
        body.extend(b"\r\n")
        
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(
        url,
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_bytes(endpoint: str) -> bytes:
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def run_live_scenario(scenario_id: str, broker_path: str, ledger_path: str, expected_state: str, expected_agreed: int, expected_diffs: int, expected_unres: int = 0):
    case_id = f"CASE-LIVE-PKG-{scenario_id}-{uuid.uuid4().hex[:6]}"
    
    # 1. Create Case
    create_res = post_json("/api/cases", {
        "case_id": case_id,
        "client_reference": f"Packaged Binary Live Test {scenario_id}",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert create_res.get("case_id") == case_id
    
    # 2. Ingest Source A
    b_bytes = Path(broker_path).read_bytes()
    src_a_res = post_multipart(
        f"/api/cases/{case_id}/sources",
        files={"file": (Path(broker_path).name, b_bytes)},
        form_data={"declared_schema": "AUTO"}
    )
    assert src_a_res.get("status") == "INGESTED"
    
    # 3. Ingest Source B
    l_bytes = Path(ledger_path).read_bytes()
    src_b_res = post_multipart(
        f"/api/cases/{case_id}/sources",
        files={"file": (Path(ledger_path).name, l_bytes)},
        form_data={"declared_schema": "AUTO"}
    )
    assert src_b_res.get("status") == "INGESTED"
    
    # 4. Reconcile
    recon_res = post_json(f"/api/cases/{case_id}/reconcile", {})
    assert recon_res.get("status") == "RECONCILED"
    recon_data = recon_res.get("reconciliation", {})
    
    assert recon_data.get("outcome_state") == expected_state, f"Expected {expected_state}, got {recon_data.get('outcome_state')}"
    assert len(recon_data.get("agreed_records", [])) == expected_agreed, f"Expected {expected_agreed} agreed, got {len(recon_data.get('agreed_records', []))}"
    assert len(recon_data.get("material_differences", [])) == expected_diffs, f"Expected {expected_diffs} diffs, got {len(recon_data.get('material_differences', []))}"
    assert len(recon_data.get("unresolved_items", [])) == expected_unres, f"Expected {expected_unres} unres, got {len(recon_data.get('unresolved_items', []))}"
    
    # 5. Export & Verify Receipt via Local Verification Endpoint
    export_bytes = get_bytes(f"/api/cases/{case_id}/export")
    with zipfile.ZipFile(io.BytesIO(export_bytes)) as z:
        receipt_bytes = z.read("receipt-v0.1.json")
        receipt_json = json.loads(receipt_bytes.decode("utf-8"))
        assert receipt_json.get("outcome_state") == expected_state
        assert receipt_json.get("receipt_id") is not None
        assert receipt_json.get("signature") is not None
        
        # Verify via local endpoint
        verify_boundary = uuid.uuid4().hex
        verify_body = bytearray()
        verify_body.extend(f"--{verify_boundary}\r\n".encode("utf-8"))
        verify_body.extend(b'Content-Disposition: form-data; name="file"; filename="receipt-v0.1.json"\r\n')
        verify_body.extend(b"Content-Type: application/json\r\n\r\n")
        verify_body.extend(receipt_bytes)
        verify_body.extend(b"\r\n")
        verify_body.extend(f"--{verify_boundary}--\r\n".encode("utf-8"))
        
        v_req = urllib.request.Request(
            f"{BASE_URL}/api/receipts/verify",
            data=bytes(verify_body),
            headers={"Content-Type": f"multipart/form-data; boundary={verify_boundary}"},
            method="POST"
        )
        with urllib.request.urlopen(v_req) as v_resp:
            v_data = json.loads(v_resp.read().decode("utf-8"))
            assert v_data.get("overall_status") == "PASS"
            assert v_data.get("is_valid") is True
            assert v_data.get("checks", {}).get("signature_authenticity") == "PASS"
            
    print(f"[{scenario_id}] LIVE PACKAGED BINARY EXECUTION: PASS (Outcome: {expected_state})")


def main():
    print("=== EXECUTING CANDIDATE 4 LIVE PACKAGED BINARY REGRESSION (http://127.0.0.1:8000) ===")
    
    # Health check
    health = json.loads(urllib.request.urlopen(f"{BASE_URL}/api/health").read().decode("utf-8"))
    print(f"Target Service: {health.get('service')} v{health.get('version')} (Commit: {health.get('source_commit')[:7]})")
    print(f"Installation Key: {health.get('installation_key_id')[:16]}...")
    
    # UAT-05
    run_live_scenario("UAT-05", "tests/fixtures/uat05/broker_perfect.csv", "tests/fixtures/uat05/ledger_perfect.csv", "MATCHED", 5, 0, 0)
    
    # UAT-06
    run_live_scenario("UAT-06", "tests/fixtures/uat06/broker_proceeds_diff.csv", "tests/fixtures/uat06/ledger_proceeds_diff.csv", "PROCEEDS_DIFFERENCE", 4, 1, 0)
    
    # UAT-07
    run_live_scenario("UAT-07", "tests/fixtures/uat07/broker_basis_diff.csv", "tests/fixtures/uat07/ledger_basis_diff.csv", "BASIS_DIFFERENCE", 4, 1, 0)
    
    # UAT-08
    run_live_scenario("UAT-08", "tests/fixtures/uat08/broker_dual_diff.csv", "tests/fixtures/uat08/ledger_dual_diff.csv", "PROCEEDS_DIFFERENCE", 4, 2, 0)
    
    # UAT-09
    run_live_scenario("UAT-09", "tests/fixtures/uat09/broker_orphan.csv", "tests/fixtures/uat09/ledger_orphan.csv", "MISSING_FROM_LEDGER", 4, 1, 0)
    
    # UAT-10
    run_live_scenario("UAT-10", "tests/fixtures/uat10/broker_orphan_b.csv", "tests/fixtures/uat10/ledger_orphan_b.csv", "MISSING_FROM_1099DA", 4, 1, 0)
    
    # UAT-11
    run_live_scenario("UAT-11", "tests/fixtures/uat11/broker_ambiguous.csv", "tests/fixtures/uat11/ledger_ambiguous.csv", "AMBIGUOUS_MATCH", 4, 1, 0)
    
    # UAT-12
    run_live_scenario("UAT-12", "tests/fixtures/uat12/broker_box2_no.csv", "tests/fixtures/uat12/ledger_box2_no.csv", "REPORTING_SCOPE_DIFFERENCE", 4, 1, 0)
    
    # UAT-13
    run_live_scenario("UAT-13", "tests/fixtures/uat13/broker_zero_basis.csv", "tests/fixtures/uat13/ledger_zero_basis.csv", "MATCHED", 5, 0, 0)
    
    # UAT-14
    run_live_scenario("UAT-14", "tests/fixtures/uat14/broker_missing_basis.csv", "tests/fixtures/uat14/ledger_missing_basis.csv", "UNRESOLVED_DATA", 4, 0, 1)
    
    print("=== ALL 10 SCENARIOS (UAT-05..14) QUALIFIED GREEN ON PACKAGED RUNTIME ===")


if __name__ == "__main__":
    main()

