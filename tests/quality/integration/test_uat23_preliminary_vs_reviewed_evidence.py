import io
import json
import zipfile
from pathlib import Path
from fastapi.testclient import TestClient

from edge.api.app import app
from apps.verifier.verify_receipt import verify_outcome_receipt


def test_uat23_preliminary_vs_reviewed_evidence_contracts():
    """
    Permanent regression test for UAT-23 (Preliminary vs Reviewed Evidence).
    
    Validates:
    1. Unmistakable Distinction Between Preliminary (Rev 1) and Reviewed (Rev 2/3) Evidence:
       - Both use the canonical Draft-07 compliant schema 'receipt-v0.1.json'.
       - Rev 1: revision=1, human_review_state='UNREVIEWED', prior_receipt_id=None.
       - Rev 2: revision=2, human_review_state='REVIEWED_ANNOTATED', prior_receipt_id points to Rev 1.
       - Rev 3: revision=3, human_review_state='REVIEWED_ANNOTATED', prior_receipt_id points to Rev 2.
    2. Deterministic Semantic Invariance (Rev 1 vs Rev 2 vs Rev 3):
       - Exact equality of source_hashes (SHA-256 digests).
       - Exact equality of ruleset_id ('VB_US_1099DA_2025_R1').
       - Exact equality of material_differences (values, difference_states, variances, locators).
       - Exact equality of unresolved_items (item IDs, reason codes, affected sources).
       - Exact equality of outcome_state ('UNRESOLVED_DATA') and assurance_level.
    3. Predecessor Receipt Retention & Cryptographic Validity:
       - Rev 2 does NOT overwrite or erase Rev 1.
       - Both Rev 1 and Rev 2 remain independently retrievable and cryptographically valid.
       - Verifier returns overall_status='PASS', signature_authenticity='PASS', tax_correctness='NOT_DETERMINED'.
    """
    client = TestClient(app)
    case_id = "CASE-UAT23-PRELIM-VS-REVIEWED"

    fixture_dir = Path("tests/fixtures/uat21")
    broker_bytes = (fixture_dir / "broker_realistic.csv").read_bytes()
    ledger_bytes = (fixture_dir / "ledger_realistic.csv").read_bytes()

    # 1. Create Case
    r_create = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "Client 2025 Tax Engagement - UAT-23 Evidence Lifecycle",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201

    # 2. Ingest Sources
    r_src_a = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_realistic.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_a.status_code == 200

    r_src_b = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_realistic.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_b.status_code == 200

    # 3. Reconcile -> Generates Rev 1 (Preliminary Receipt)
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
    assert rev1_receipt["outcome_state"] == "UNRESOLVED_DATA"
    assert len(rev1_receipt["material_differences"]) == 6
    assert len(rev1_receipt["unresolved_items"]) == 1

    # Verify Rev 1 independently
    v_rev1 = verify_outcome_receipt(rev1_receipt)
    assert v_rev1.is_valid is True
    assert v_rev1.signature_valid is True

    # 4. Practitioner Review & Finalize -> Generates Rev 2 (Reviewed Receipt)
    diff_eth = next(d for d in rev1_receipt["material_differences"] if d["asset"] == "ETH")
    diff_sol = next(d for d in rev1_receipt["material_differences"] if d["asset"] == "SOL")
    unres_ada = rev1_receipt["unresolved_items"][0]

    client.post(f"/api/cases/{case_id}/reviews", json={
        "finding_id": diff_eth["difference_id"],
        "disposition": "REVIEWED",
        "note": "Fee variance confirmed against broker statement.",
        "reviewer_reference": "CPA Reviewer"
    })
    client.post(f"/api/cases/{case_id}/reviews", json={
        "finding_id": diff_sol["difference_id"],
        "disposition": "FOLLOW_UP_REQUIRED",
        "note": "Staking reward lot documentation requested from client.",
        "reviewer_reference": "CPA Reviewer"
    })
    client.post(f"/api/cases/{case_id}/reviews", json={
        "finding_id": unres_ada["item_id"],
        "disposition": "LEFT_UNRESOLVED",
        "note": "Missing acquisition basis from defunct exchange.",
        "reviewer_reference": "CPA Reviewer"
    })

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
    assert rev2_receipt["receipt_id"] != rev1_receipt["receipt_id"]
    assert rev2_receipt["signature"] != rev1_receipt["signature"]

    # Verify Rev 2 independently
    v_rev2 = verify_outcome_receipt(rev2_receipt)
    assert v_rev2.is_valid is True
    assert v_rev2.signature_valid is True

    # 5. Deterministic Semantic Invariance Checks (Rev 1 vs Rev 2)
    # A. Source Hashes
    assert rev1_receipt["source_hashes"] == rev2_receipt["source_hashes"]
    assert rev1_receipt["source_ids"] == rev2_receipt["source_ids"]
    assert rev1_receipt["source_schema_ids"] == rev2_receipt["source_schema_ids"]

    # B. Ruleset & Engine Identity
    assert rev1_receipt["ruleset_id"] == rev2_receipt["ruleset_id"] == "VB_US_1099DA_2025_R1"
    assert rev1_receipt["engine_version"] == rev2_receipt["engine_version"]
    assert rev1_receipt["canonicalization_version"] == rev2_receipt["canonicalization_version"] == "v0.1"

    # C. Outcome & Assurance
    assert rev1_receipt["outcome_state"] == rev2_receipt["outcome_state"] == "UNRESOLVED_DATA"
    assert rev1_receipt["assurance_level"] == rev2_receipt["assurance_level"]

    # D. Itemized Material Differences
    assert len(rev1_receipt["material_differences"]) == len(rev2_receipt["material_differences"]) == 6
    for d1, d2 in zip(rev1_receipt["material_differences"], rev2_receipt["material_differences"]):
        assert d1["difference_id"] == d2["difference_id"]
        assert d1["difference_state"] == d2["difference_state"]
        assert d1["asset"] == d2["asset"]
        assert d1["source_a_value"] == d2["source_a_value"]
        assert d1["source_b_value"] == d2["source_b_value"]
        assert d1["variance"] == d2["variance"]
        assert d1["rule_reference"] == d2["rule_reference"]

    # E. Itemized Unresolved Items
    assert len(rev1_receipt["unresolved_items"]) == len(rev2_receipt["unresolved_items"]) == 1
    u1 = rev1_receipt["unresolved_items"][0]
    u2 = rev2_receipt["unresolved_items"][0]
    assert u1["item_id"] == u2["item_id"]
    assert u1["reason_code"] == u2["reason_code"] == "BASIS_UNAVAILABLE"
    assert u1["affected_source_id"] == u2["affected_source_id"]

    # 6. Predecessor Receipt Retention & Coexistence
    # Rev 1 must remain retrievable in case history and verifiable
    case_details = client.get(f"/api/cases/{case_id}").json()
    receipt_history = case_details["receipt_history"]
    assert len(receipt_history) == 2
    
    rev1_history_entry = next(r for r in receipt_history if r["revision"] == 1)
    rev2_history_entry = next(r for r in receipt_history if r["revision"] == 2)
    assert rev1_history_entry["receipt_id"] == rev1_receipt["receipt_id"]
    assert rev2_history_entry["receipt_id"] == rev2_receipt["receipt_id"]
    assert rev2_history_entry["prior_receipt_id"] == rev1_receipt["receipt_id"]

    # 7. Monotonic Evolution to Revision 3
    client.post(f"/api/cases/{case_id}/reviews", json={
        "finding_id": rev1_receipt["material_differences"][2]["difference_id"],
        "disposition": "REVIEWED",
        "note": "Client acknowledged missing ledger row."
    })
    r_rev3 = client.post(f"/api/cases/{case_id}/finalize-review")
    assert r_rev3.status_code == 200
    rev3_res = r_rev3.json()
    assert rev3_res["revision"] == 3
    assert rev3_res["prior_receipt_id"] == rev2_receipt["receipt_id"]

    rev3_receipt = rev3_res["receipt"]
    assert rev3_receipt["revision"] == 3
    assert rev3_receipt["prior_receipt_id"] == rev2_receipt["receipt_id"]
    assert rev3_receipt["source_hashes"] == rev1_receipt["source_hashes"]
    assert rev3_receipt["outcome_state"] == rev1_receipt["outcome_state"]
    assert len(rev3_receipt["material_differences"]) == 6

    v_rev3 = verify_outcome_receipt(rev3_receipt)
    assert v_rev3.is_valid is True
    assert v_rev3.signature_valid is True

    # 8. Export Bundle & Verification Response
    r_export = client.get(f"/api/cases/{case_id}/export")
    assert r_export.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_export.content)) as z:
        exported_receipt = json.loads(z.read("receipt-v0.1.json").decode("utf-8"))
        assert exported_receipt["revision"] == 3
        assert exported_receipt["prior_receipt_id"] == rev2_receipt["receipt_id"]
        assert exported_receipt["human_review_state"] == "REVIEWED_ANNOTATED"

        r_ver = client.post("/api/receipts/verify", files={"file": ("receipt-v0.1.json", z.read("receipt-v0.1.json"), "application/json")})
        assert r_ver.status_code == 200
        ver_data = r_ver.json()
        assert ver_data["overall_status"] == "PASS"
        assert ver_data["checks"]["signature_authenticity"] == "PASS"
        assert ver_data["checks"]["tax_correctness"] == "NOT_DETERMINED"
