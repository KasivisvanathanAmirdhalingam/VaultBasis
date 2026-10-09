"""
VaultBasis Edge — Packaged Candidate 7 Live Artifact Regression Runner
Directly executes scenarios UAT-05 through UAT-21 (including UAT-20 and UAT-21) over HTTP against the running packaged binary on http://127.0.0.1:8000.
"""

import json
import io
import zipfile
from pathlib import Path
import urllib.request
import urllib.error
import urllib.parse
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
    
    receipt = recon_res.get("receipt", {})
    assert receipt.get("ruleset_id") == "VB_US_1099DA_2025_R1", f"Expected ruleset_id VB_US_1099DA_2025_R1, got {receipt.get('ruleset_id')}"

    # 5. Export & Verify Receipt via Local Verification Endpoint
    export_bytes = get_bytes(f"/api/cases/{case_id}/export")
    with zipfile.ZipFile(io.BytesIO(export_bytes)) as z:
        receipt_bytes = z.read("receipt-v0.1.json")
        receipt_json = json.loads(receipt_bytes.decode("utf-8"))
        assert receipt_json.get("outcome_state") == expected_state
        assert receipt_json.get("receipt_id") is not None
        assert receipt_json.get("signature") is not None
        assert receipt_json.get("ruleset_id") == "VB_US_1099DA_2025_R1"
        
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


def run_live_fail_closed_intake(scenario_id: str, fixture_path: str, expected_code: str):
    case_id = f"CASE-LIVE-PKG-{scenario_id}-{uuid.uuid4().hex[:6]}"
    
    # 1. Create Case
    create_res = post_json("/api/cases", {
        "case_id": case_id,
        "client_reference": f"Packaged Binary Live Test {scenario_id}",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert create_res.get("case_id") == case_id
    
    # 2. Ingest corrupted file -> must fail closed (422)
    b_bytes = Path(fixture_path).read_bytes()
    try:
        post_multipart(
            f"/api/cases/{case_id}/sources",
            files={"file": (Path(fixture_path).name, b_bytes)},
            form_data={"declared_schema": "AUTO"}
        )
        raise AssertionError(f"[{scenario_id}] Expected 422 HTTP error but request succeeded")
    except urllib.error.HTTPError as e:
        assert e.code == 422
        err_body = json.loads(e.read().decode("utf-8"))
        assert expected_code in err_body.get("detail", "")
        
    # 3. Assert Case State remains uncontaminated
    case_req = urllib.request.Request(f"{BASE_URL}/api/cases/{case_id}", method="GET")
    with urllib.request.urlopen(case_req) as c_resp:
        case_data = json.loads(c_resp.read().decode("utf-8"))
        assert len(case_data.get("sources", [])) == 0

    print(f"[{scenario_id}] LIVE PACKAGED BINARY EXECUTION: PASS (Failed Closed with {expected_code})")


def run_live_regulatory_routing_boundary(scenario_id: str, jurisdiction: str, tax_year: int):
    case_id = f"CASE-LIVE-PKG-{scenario_id}-{uuid.uuid4().hex[:6]}"
    
    # 1. Create Case
    create_res = post_json("/api/cases", {
        "case_id": case_id,
        "client_reference": f"Packaged Binary Live Regulatory Test {scenario_id}",
        "tax_year": tax_year,
        "jurisdiction": jurisdiction
    })
    assert create_res.get("case_id") == case_id
    
    # 2. Ingest standard sources
    b_bytes = Path("tests/fixtures/uat05/broker_perfect.csv").read_bytes()
    l_bytes = Path("tests/fixtures/uat05/ledger_perfect.csv").read_bytes()
    
    post_multipart(f"/api/cases/{case_id}/sources", files={"file": ("broker.csv", b_bytes)}, form_data={"declared_schema": "AUTO"})
    post_multipart(f"/api/cases/{case_id}/sources", files={"file": ("ledger.csv", l_bytes)}, form_data={"declared_schema": "AUTO"})
    
    # 3. Attempt reconciliation -> Must fail closed with 422 RULESET_UNSUPPORTED
    try:
        post_json(f"/api/cases/{case_id}/reconcile", {})
        raise AssertionError(f"[{scenario_id}] Expected 422 RULESET_UNSUPPORTED but reconciliation succeeded!")
    except urllib.error.HTTPError as e:
        assert e.code == 422
        err_body = json.loads(e.read().decode("utf-8"))
        assert "RULESET_UNSUPPORTED" in err_body.get("detail", "")
        print(f"[{scenario_id}] LIVE REGULATORY ROUTING: PASS (Denied with HTTP 422 RULESET_UNSUPPORTED: {err_body.get('detail')})")
        
    # 4. Confirm no receipt was issued / export is 404
    try:
        get_bytes(f"/api/cases/{case_id}/export")
        raise AssertionError(f"[{scenario_id}] Expected 404 on export for un-reconciled case")
    except urllib.error.HTTPError as e:
        assert e.code == 404


def main():
    print("=== EXECUTING CANDIDATE 7 LIVE PACKAGED BINARY REGRESSION (http://127.0.0.1:8000) ===")
    
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
    
def run_live_professional_review_lifecycle():
    scenario_id = "UAT-22"
    case_id = f"CASE-LIVE-PKG-{scenario_id}-{uuid.uuid4().hex[:6]}"
    
    # 1. Create Case
    create_res = post_json("/api/cases", {
        "case_id": case_id,
        "client_reference": "Packaged Binary Live Professional Review UAT-22",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert create_res.get("case_id") == case_id
    
    # Negative assertion: Cannot finalize review before reconciliation
    try:
        post_json(f"/api/cases/{case_id}/finalize-review", {})
        raise AssertionError("Expected 400 when finalizing review before reconciliation")
    except urllib.error.HTTPError as e:
        assert e.code == 400

    # 2. Ingest Multi-Finding Sources
    b_bytes = Path("tests/fixtures/uat21/broker_realistic.csv").read_bytes()
    l_bytes = Path("tests/fixtures/uat21/ledger_realistic.csv").read_bytes()
    
    post_multipart(f"/api/cases/{case_id}/sources", files={"file": ("broker_realistic.csv", b_bytes)}, form_data={"declared_schema": "AUTO"})
    post_multipart(f"/api/cases/{case_id}/sources", files={"file": ("ledger_realistic.csv", l_bytes)}, form_data={"declared_schema": "AUTO"})
    
    # 3. Reconcile (Generates Rev 1 Preliminary Receipt)
    recon_res = post_json(f"/api/cases/{case_id}/reconcile", {})
    assert recon_res.get("status") == "RECONCILED"
    assert recon_res.get("revision") == 1
    assert recon_res.get("human_review_state") == "UNREVIEWED"
    prelim_receipt = recon_res.get("receipt", {})
    assert prelim_receipt.get("ruleset_id") == "VB_US_1099DA_2025_R1"
    assert prelim_receipt.get("outcome_state") == "UNRESOLVED_DATA"
    assert len(prelim_receipt.get("material_differences", [])) == 6
    assert len(prelim_receipt.get("unresolved_items", [])) == 1
    
    diff_eth = next(d for d in prelim_receipt["material_differences"] if d["asset"] == "ETH")
    diff_sol = next(d for d in prelim_receipt["material_differences"] if d["asset"] == "SOL")
    diff_link = next(d for d in prelim_receipt["material_differences"] if d["asset"] == "LINK")
    unres_ada = prelim_receipt["unresolved_items"][0]
    
    # 4. Review Actions
    # Negative assertion: Invalid disposition rejected
    try:
        post_json(f"/api/cases/{case_id}/reviews", {
            "finding_id": diff_eth["difference_id"],
            "disposition": "INVALID_DISPOSITION",
            "note": "Bad test"
        })
        raise AssertionError("Expected 400 for invalid disposition")
    except urllib.error.HTTPError as e:
        assert e.code == 400
        
    # ETH -> REVIEWED
    post_json(f"/api/cases/{case_id}/reviews", {
        "finding_id": diff_eth["difference_id"],
        "disposition": "REVIEWED",
        "note": "Verified broker exchange settlement statement; fee deducted.",
        "reviewer_reference": "CPA Senior Reviewer #412"
    })
    
    # SOL -> FOLLOW_UP_REQUIRED
    post_json(f"/api/cases/{case_id}/reviews", {
        "finding_id": diff_sol["difference_id"],
        "disposition": "FOLLOW_UP_REQUIRED",
        "note": "Requested original staking reward cost basis lot documentation.",
        "reviewer_reference": "CPA Senior Reviewer #412"
    })
    
    # ADA -> LEFT_UNRESOLVED
    post_json(f"/api/cases/{case_id}/reviews", {
        "finding_id": unres_ada["item_id"],
        "disposition": "LEFT_UNRESOLVED",
        "note": "Missing acquisition basis from defunct overseas exchange.",
        "reviewer_reference": "CPA Senior Reviewer #412"
    })
    
    # 5. Invariant Checks
    case_receipt_check = json.loads(urllib.request.urlopen(f"{BASE_URL}/api/cases/{case_id}/receipt").read().decode("utf-8"))
    eth_check = next(d for d in case_receipt_check["material_differences"] if d["asset"] == "ETH")
    assert eth_check["difference_state"] == "PROCEEDS_DIFFERENCE"  # Reviewed != Agreed
    assert eth_check["variance"] == "199.50"
    assert eth_check["source_a_value"] == diff_eth["source_a_value"]
    assert eth_check["source_b_value"] == diff_eth["source_b_value"]
    
    # 6. Finalize Review (Generates Rev 2 Reviewed Receipt)
    final_res = post_json(f"/api/cases/{case_id}/finalize-review", {})
    assert final_res.get("status") == "REVIEW_FINALIZED"
    assert final_res.get("revision") == 2
    assert final_res.get("prior_receipt_id") == prelim_receipt["receipt_id"]
    assert final_res.get("human_review_state") == "REVIEWED_ANNOTATED"
    final_receipt = final_res.get("receipt", {})
    assert final_receipt.get("revision") == 2
    
    # 7. Sample Immutability Check
    try:
        post_json("/api/cases/CASE-SAMPLE-2025/reviews", {
            "finding_id": "DIFF-001",
            "disposition": "REVIEWED",
            "note": "Illegal edit on sample"
        })
        raise AssertionError("Expected 403 on sample case review mutation")
    except urllib.error.HTTPError as e:
        assert e.code == 403
        
    # 8. Re-finalization monotonic revision increment
    post_json(f"/api/cases/{case_id}/reviews", {
        "finding_id": diff_link["difference_id"],
        "disposition": "REVIEWED",
        "note": "Additional statement provided."
    })
    refinal_res = post_json(f"/api/cases/{case_id}/finalize-review", {})
    assert refinal_res.get("revision") == 3
    assert refinal_res.get("prior_receipt_id") == final_receipt["receipt_id"]
    
    # 9. Export & Offline Verifier Check
    zip_bytes = get_bytes(f"/api/cases/{case_id}/export")
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        exported_receipt = json.loads(z.read("receipt-v0.1.json").decode("utf-8"))
        assert exported_receipt["revision"] == 3
        assert exported_receipt["human_review_state"] == "REVIEWED_ANNOTATED"
        
        # Verify via offline verifier endpoint
        ver_res = post_multipart("/api/receipts/verify", files={"file": ("receipt-v0.1.json", z.read("receipt-v0.1.json"))})
        assert ver_res.get("overall_status") == "PASS"
        assert ver_res.get("checks", {}).get("signature_authenticity") == "PASS"
        assert ver_res.get("checks", {}).get("tax_correctness") == "NOT_DETERMINED"
        
    print(f"[{scenario_id}] LIVE PACKAGED BINARY EXECUTION: PASS (Professional Review Lifecycle & Invariants Validated)")


def main():
    print("=== EXECUTING CANDIDATE 7 LIVE PACKAGED BINARY REGRESSION (http://127.0.0.1:8000) ===")
    
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
    
    # UAT-15
    run_live_scenario("UAT-15", "tests/fixtures/uat15/broker_norm.csv", "tests/fixtures/uat15/ledger_norm.csv", "MATCHED", 5, 0, 0)
    
    # UAT-16 (Micro-Variance / Sub-Cent Decimal Precision)
    run_live_scenario("UAT-16", "tests/fixtures/uat16/broker_micro_diff.csv", "tests/fixtures/uat16/ledger_micro_diff.csv", "PROCEEDS_DIFFERENCE", 4, 1, 0)
    
    # UAT-17 (Fail-Closed Intake Rejections)
    run_live_fail_closed_intake("UAT-17A", "tests/fixtures/uat17/broker_missing_column.csv", "SCHEMA_REQUIRED_FIELD_MISSING")
    run_live_fail_closed_intake("UAT-17B", "tests/fixtures/uat17/broker_invalid_numeric.csv", "NUMERIC_INVALID")
    run_live_fail_closed_intake("UAT-17C", "tests/fixtures/uat17/broker_malformed_row.csv", "CSV_MALFORMED")
    run_live_fail_closed_intake("UAT-17D", "tests/fixtures/uat17/alien_unsupported_schema.csv", "SCHEMA_REQUIRED_FIELD_MISSING")
    
    # UAT-18 (Duplicate Rows & Colliding Candidates)
    run_live_scenario("UAT-18A", "tests/fixtures/uat18/broker_duplicates.csv", "tests/fixtures/uat18/ledger_single_counterpart.csv", "MISSING_FROM_LEDGER", 5, 1, 0)
    run_live_scenario("UAT-18B", "tests/fixtures/uat18/broker_colliding.csv", "tests/fixtures/uat18/ledger_colliding_diff_evidence.csv", "AMBIGUOUS_MATCH", 4, 1, 0)
    
    # UAT-19 (Hostile Payload Safety & Neutralization)
    run_live_fail_closed_intake("UAT-19A1", "tests/fixtures/uat19/broker_formula_numeric_rejected.csv", "NUMERIC_INVALID")
    run_live_scenario("UAT-19A2", "tests/fixtures/uat19/broker_formula_text_safe.csv", "tests/fixtures/uat19/ledger_formula_text_safe.csv", "MATCHED", 5, 0, 0)
    run_live_scenario("UAT-19B", "tests/fixtures/uat19/broker_xss_html_safe.csv", "tests/fixtures/uat19/ledger_xss_html_safe.csv", "MATCHED", 5, 0, 0)
    run_live_scenario("UAT-19C", "tests/fixtures/uat19/broker_quoted_multiline.csv", "tests/fixtures/uat19/ledger_quoted_multiline.csv", "MATCHED", 5, 0, 0)
    run_live_scenario("UAT-19D", "tests/fixtures/uat19/broker_oversized_field.csv", "tests/fixtures/uat19/ledger_oversized_field.csv", "MATCHED", 5, 0, 0)
    
    # UAT-20 (Regulatory Routing & Fail-Closed Unsupported Jurisdictions / Tax Years)
    run_live_regulatory_routing_boundary("UAT-20A-US2024", "US", 2024)
    run_live_regulatory_routing_boundary("UAT-20B-US2023", "US", 2023)
    run_live_regulatory_routing_boundary("UAT-20C-UK2025", "UK", 2025)
    run_live_regulatory_routing_boundary("UAT-20D-CA2025", "CA", 2025)

    # UAT-21 (Mixed Realistic Case)
    run_live_scenario("UAT-21", "tests/fixtures/uat21/broker_realistic.csv", "tests/fixtures/uat21/ledger_realistic.csv", "UNRESOLVED_DATA", 1, 6, 1)
    
    # UAT-22 (Professional Review Lifecycle & Invariants)
    run_live_professional_review_lifecycle()

    print("=== ALL SCENARIOS (UAT-05..22) QUALIFIED 100% GREEN ON PACKAGED CANDIDATE 7 RUNTIME ===")


if __name__ == "__main__":
    import os, sqlite3
    db_path = os.path.expanduser('~/Library/Application Support/VaultBasis/candidate7_qualification.db')
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        conn.cursor().execute('DELETE FROM cases WHERE case_kind != "BUNDLED_SAMPLE"')
        conn.commit()
    main()

