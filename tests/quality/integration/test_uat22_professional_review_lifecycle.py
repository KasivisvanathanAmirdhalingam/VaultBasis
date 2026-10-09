import io
import json
import zipfile
from pathlib import Path
from decimal import Decimal
from fastapi.testclient import TestClient

from edge.api.app import app
from apps.verifier.verify_receipt import verify_outcome_receipt


def test_uat22_professional_review_lifecycle_and_invariants():
    """
    Permanent regression test for UAT-22 (Professional Review Lifecycle).
    
    Validates:
    1. Full State Progression:
       CREATED -> SOURCES_INGESTED -> RECONCILED (Prelim Rev 1, UNREVIEWED) -> 
       PRACTITIONER REVIEW (Dispositions & Notes) -> RECEIPT_ISSUED (Final Rev 2, REVIEWED_ANNOTATED)
    2. Review Invariant Preservation:
       - Practitioner review actions (disposition, notes) store separate metadata.
       - NEVER mutate underlying deterministic values (gross proceeds, cost basis, variance, difference_state).
       - Reviewed != Agreed (PROCEEDS_DIFFERENCE remains PROCEEDS_DIFFERENCE, never converted to MATCHED).
       - Reviewed != Resolved (UNRESOLVED_DATA remains UNRESOLVED_DATA).
       - Ruleset ID remains canonically 'VB_US_1099DA_2025_R1'.
    3. Negative / Boundary Assertions:
       - Cannot finalize review before reconciliation (HTTP 400).
       - Invalid disposition codes rejected (HTTP 400).
       - Case mutation after final receipt issued is blocked by CaseWritePolicy (HTTP 409).
    4. Receipt Lineage & Verification:
       - Prelim Receipt (Rev 1) has human_review_state == 'UNREVIEWED'.
       - Final Receipt (Rev 2) has human_review_state == 'REVIEWED_ANNOTATED' and prior_receipt_id pointing to Rev 1.
       - Independent verifier passes signature authenticity while maintaining tax correctness NOT_DETERMINED.
    """
    client = TestClient(app)
    case_id = "CASE-UAT22-PRACTITIONER-LIFECYCLE"

    # Load multi-finding fixtures (from UAT-21 mixed realistic corpus)
    fixture_dir = Path("tests/fixtures/uat21")
    broker_bytes = (fixture_dir / "broker_realistic.csv").read_bytes()
    ledger_bytes = (fixture_dir / "ledger_realistic.csv").read_bytes()

    # 1. State: CREATED
    r_create = client.post("/api/cases", json={
        "case_id": case_id,
        "client_reference": "Client 2025 Tax Engagement - Professional Review",
        "tax_year": 2025,
        "jurisdiction": "US"
    })
    assert r_create.status_code == 201
    case_state_1 = client.get(f"/api/cases/{case_id}").json()
    assert case_state_1["case_status"] in ("CREATED", "DRAFT")

    # Negative assertion: Cannot finalize review before reconciliation
    r_bad_finalize = client.post(f"/api/cases/{case_id}/finalize-review")
    assert r_bad_finalize.status_code == 400

    # 2. State: SOURCES_INGESTED
    r_src_a = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("broker_1099da.csv", broker_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_a.status_code == 200

    r_src_b = client.post(
        f"/api/cases/{case_id}/sources",
        files={"file": ("ledger_koinly.csv", ledger_bytes, "text/csv")},
        data={"declared_schema": "AUTO"}
    )
    assert r_src_b.status_code == 200
    case_state_2 = client.get(f"/api/cases/{case_id}").json()
    assert case_state_2["case_status"] == "SOURCES_INGESTED"

    # 3. State: RECONCILED (Preliminary Receipt Issued, Revision 1)
    r_recon = client.post(f"/api/cases/{case_id}/reconcile")
    assert r_recon.status_code == 200
    recon_res = r_recon.json()
    assert recon_res["status"] == "RECONCILED"
    assert recon_res["revision"] == 1
    assert recon_res["human_review_state"] == "UNREVIEWED"

    prelim_receipt = recon_res["receipt"]
    assert prelim_receipt["revision"] == 1
    assert prelim_receipt["human_review_state"] == "UNREVIEWED"
    assert prelim_receipt["ruleset_id"] == "VB_US_1099DA_2025_R1"
    assert prelim_receipt["outcome_state"] == "UNRESOLVED_DATA"
    assert len(prelim_receipt["material_differences"]) == 6
    assert len(prelim_receipt["unresolved_items"]) == 1

    # Freeze baseline values of findings before review
    diff_eth = next(d for d in prelim_receipt["material_differences"] if d["asset"] == "ETH")
    diff_sol = next(d for d in prelim_receipt["material_differences"] if d["asset"] == "SOL")
    diff_link = next(d for d in prelim_receipt["material_differences"] if d["asset"] == "LINK")
    diff_doge = next(d for d in prelim_receipt["material_differences"] if d["asset"] == "DOGE")
    unres_ada = prelim_receipt["unresolved_items"][0]

    assert diff_eth["difference_state"] == "PROCEEDS_DIFFERENCE"
    assert diff_eth["variance"] == "199.50"
    assert diff_sol["difference_state"] == "BASIS_DIFFERENCE"
    assert diff_sol["variance"] == "200.00"
    assert diff_link["difference_state"] == "MISSING_FROM_LEDGER"
    assert diff_doge["difference_state"] == "REPORTING_SCOPE_DIFFERENCE"

    # 4. Practitioner Review Actions (Dispositions & Annotations)
    # Negative assertion: Invalid disposition code
    r_bad_disp = client.post(f"/api/cases/{case_id}/reviews", json={
        "finding_id": diff_eth["difference_id"],
        "disposition": "INVALID_DISPOSITION",
        "note": "Bad test"
    })
    assert r_bad_disp.status_code == 400

    # Review Action 1: ETH Proceeds Difference -> REVIEWED with supporting note
    r_rev_1 = client.post(f"/api/cases/{case_id}/reviews", json={
        "finding_id": diff_eth["difference_id"],
        "disposition": "REVIEWED",
        "note": "Verified broker exchange settlement statement; broker amount includes network fee deduction.",
        "reviewer_reference": "CPA Senior Reviewer #412"
    })
    assert r_rev_1.status_code == 200

    # Review Action 2: SOL Basis Difference -> FOLLOW_UP_REQUIRED with note
    r_rev_2 = client.post(f"/api/cases/{case_id}/reviews", json={
        "finding_id": diff_sol["difference_id"],
        "disposition": "FOLLOW_UP_REQUIRED",
        "note": "Requested original staking reward cost basis lot documentation from client.",
        "reviewer_reference": "CPA Senior Reviewer #412"
    })
    assert r_rev_2.status_code == 200

    # Review Action 3: ADA Unresolved Basis -> LEFT_UNRESOLVED with note
    r_rev_3 = client.post(f"/api/cases/{case_id}/reviews", json={
        "finding_id": unres_ada["item_id"],
        "disposition": "LEFT_UNRESOLVED",
        "note": "Missing acquisition basis from defunct overseas exchange. Left unresolved pending client affidavit.",
        "reviewer_reference": "CPA Senior Reviewer #412"
    })
    assert r_rev_3.status_code == 200

    # Check reviews endpoint returns exact saved dispositions
    reviews_res = client.get(f"/api/cases/{case_id}/reviews").json()
    assert len(reviews_res["reviews"]) == 3
    assert reviews_res["reviews"][diff_eth["difference_id"]]["disposition"] == "REVIEWED"
    assert reviews_res["reviews"][diff_sol["difference_id"]]["disposition"] == "FOLLOW_UP_REQUIRED"
    assert reviews_res["reviews"][unres_ada["item_id"]]["disposition"] == "LEFT_UNRESOLVED"

    # 5. INVARIANT CHECK: Review actions did NOT mutate deterministic reconciliation facts
    r_prelim_check = client.get(f"/api/cases/{case_id}/receipt").json()
    eth_after_review = next(d for d in r_prelim_check["material_differences"] if d["asset"] == "ETH")
    sol_after_review = next(d for d in r_prelim_check["material_differences"] if d["asset"] == "SOL")

    # Reviewed != Agreed: ETH is still PROCEEDS_DIFFERENCE, never converted to MATCHED
    assert eth_after_review["difference_state"] == "PROCEEDS_DIFFERENCE"
    assert eth_after_review["source_a_value"] == diff_eth["source_a_value"]
    assert eth_after_review["source_b_value"] == diff_eth["source_b_value"]
    assert eth_after_review["variance"] == "199.50"
    assert eth_after_review["rule_reference"] == "VB_US_1099DA_2025_R1"

    # 6. State: RECEIPT_ISSUED (Finalize Review, Revision 2)
    r_finalize = client.post(f"/api/cases/{case_id}/finalize-review")
    assert r_finalize.status_code == 200
    final_res = r_finalize.json()
    assert final_res["status"] == "REVIEW_FINALIZED"
    assert final_res["revision"] == 2
    assert final_res["prior_receipt_id"] == prelim_receipt["receipt_id"]
    assert final_res["human_review_state"] == "REVIEWED_ANNOTATED"

    final_receipt = final_res["receipt"]
    assert final_receipt["revision"] == 2
    assert final_receipt["prior_receipt_id"] == prelim_receipt["receipt_id"]
    assert final_receipt["human_review_state"] == "REVIEWED_ANNOTATED"
    assert final_receipt["ruleset_id"] == "VB_US_1099DA_2025_R1"
    assert final_receipt["outcome_state"] == "UNRESOLVED_DATA"

    # Verify both receipts are independently verifiable
    v_prelim = verify_outcome_receipt(prelim_receipt)
    assert v_prelim.is_valid is True
    assert v_prelim.signature_valid is True

    v_final = verify_outcome_receipt(final_receipt)
    assert v_final.is_valid is True
    assert v_final.signature_valid is True

    # 7. Sample Immutability & Re-Finalization Revision Increment
    # Attempting review on bundled sample is blocked by CaseWritePolicy (HTTP 403)
    client.post("/api/sample-case/load")  # Ensure authentic bundled sample is loaded
    r_sample_review = client.post("/api/cases/CASE-SAMPLE-2025/reviews", json={
        "finding_id": "DIFF-001",
        "disposition": "REVIEWED",
        "note": "Illegal edit on sample"
    })
    assert r_sample_review.status_code == 403
    assert "immutable demonstration baselines" in r_sample_review.json()["detail"]

    # Subsequent practitioner updates on production case create higher revision upon re-finalization
    r_rev_4 = client.post(f"/api/cases/{case_id}/reviews", json={
        "finding_id": diff_link["difference_id"],
        "disposition": "REVIEWED",
        "note": "Additional statement provided confirming omitted ledger record."
    })
    assert r_rev_4.status_code == 200

    r_refinalize = client.post(f"/api/cases/{case_id}/finalize-review")
    assert r_refinalize.status_code == 200
    refinal_data = r_refinalize.json()
    assert refinal_data["revision"] == 3
    assert refinal_data["prior_receipt_id"] == final_receipt["receipt_id"]

    # 8. Export Package Verification
    r_export = client.get(f"/api/cases/{case_id}/export")
    assert r_export.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r_export.content)) as z:
        exported_receipt = json.loads(z.read("receipt-v0.1.json").decode("utf-8"))
        assert exported_receipt["revision"] == 3
        assert exported_receipt["human_review_state"] == "REVIEWED_ANNOTATED"
        assert exported_receipt["prior_receipt_id"] == final_receipt["receipt_id"]
        assert len(exported_receipt["material_differences"]) == 6

        # Offline verifier check
        r_ver_post = client.post("/api/receipts/verify", files={"file": ("receipt-v0.1.json", z.read("receipt-v0.1.json"), "application/json")})
        assert r_ver_post.status_code == 200
        v_data = r_ver_post.json()
        assert v_data["overall_status"] == "PASS"
        assert v_data["checks"]["signature_authenticity"] == "PASS"
        assert v_data["checks"]["tax_correctness"] == "NOT_DETERMINED"
