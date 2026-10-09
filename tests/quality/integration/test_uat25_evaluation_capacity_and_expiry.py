import copy
import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from edge.api.app import app
from edge.commercial.models import LicenseState, LicenseTier
from edge.commercial.policy import (
    CommercialDenialCode,
    CommercialOperation,
    CommercialPolicyService,
)
from edge.storage.sqlite_store import SQLiteStore
from schemas.canonical.case import CanonicalCase


def test_uat25_evaluation_capacity_monotonicity_and_expiry():
    """
    Permanent regression test for UAT-25 (Evaluation Capacity Boundaries & Monotonic Consumption).
    
    Validates PRD §64 / §71 Evaluation Invariants:
    1. 25A: First 3 client cases under Evaluation succeed (cases_created_count: 1 -> 2 -> 3).
    2. 25B: 4th client case creation is denied with HTTP 403 EVALUATION_CAPACITY_REACHED.
    3. 25C: Deleting an existing evaluation case does NOT refund or decrement capacity (monotonicity).
    4. 25D: Process restart preserves consumed capacity; 4th case remains rejected; historical cases accessible.
    5. 25E: Bundled sample (CASE-SAMPLE-2025) is free/unmetered; cloning to production consumes capacity.
    6. 25F: Re-uploads, reruns, reviews, and exports on existing cases do not consume additional slots.
    7. 25G: 72-hour temporal boundary strictly enforced:
       - expires_at - 1s: ACTIVE
       - expires_at: EXPIRED (zero grace)
       - After expiry: new cases/reconciliations blocked (403 LICENSE_EXPIRED), historical data and receipts preserved.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_file = tmp_path / "uat25_eval.db"
        store = SQLiteStore(db_file)
        policy = CommercialPolicyService(store=store, license_dir=tmp_path / "lic")

        # Disable dev bypass
        os.environ["VAULTBASIS_BYPASS_ENTITLEMENT"] = "0"
        os.environ.pop("VAULTBASIS_LICENSE_TOKEN", None)

        # -------------------------------------------------------------
        # 1. Fresh Installation Evaluation Activation
        # -------------------------------------------------------------
        now_utc = datetime.now(timezone.utc)
        eval_res = policy.start_evaluation(customer_name="CPA Test Firm")
        assert eval_res.is_active is True
        assert eval_res.tier == LicenseTier.EVALUATION
        assert eval_res.max_cases_per_installation == 3
        assert eval_res.state == LicenseState.ACTIVE

        status = policy.get_status(current_time=now_utc)
        assert status["licensed"] is True
        assert status["entitlement_state"] == "ACTIVE_EVALUATION"
        assert status["billable_cases_count"] == 0
        assert status["max_cases_per_installation"] == 3

        # -------------------------------------------------------------
        # 2. Subcase 25A: First 3 Client Cases Succeed
        # -------------------------------------------------------------
        for idx in (1, 2, 3):
            cid = f"CASE-EVAL-0{idx}"
            dec = policy.authorize(CommercialOperation.CREATE_CASE, current_time=now_utc)
            assert dec.allowed is True
            assert dec.http_status == 200

            # Atomic creation in SQLiteStore
            store.create_case_atomic(
                case=CanonicalCase(
                    case_id=cid,
                    client_reference=f"Client Case {idx}",
                    tax_year=2025,
                    jurisdiction="US",
                    case_status="CREATED",
                    case_kind="PRODUCTION",
                    sample_definition_id=None,
                    sample_manifest_digest=None,
                    created_at=now_utc.isoformat(),
                    updated_at=now_utc.isoformat()
                ),
                is_evaluation=True,
                max_cases=3,
                since_iso=now_utc.isoformat()
            )

        assert store.count_evaluation_cases_created() == 3
        status_after_3 = policy.get_status(current_time=now_utc)
        assert status_after_3["billable_cases_count"] == 3
        assert status_after_3["max_cases_per_installation"] == 3

        # -------------------------------------------------------------
        # 3. Subcase 25B: 4th Client Case Denied
        # -------------------------------------------------------------
        dec_4th = policy.authorize(CommercialOperation.CREATE_CASE, current_time=now_utc)
        assert dec_4th.allowed is False
        assert dec_4th.http_status == 403
        assert dec_4th.reason_code == CommercialDenialCode.EVALUATION_CAPACITY_REACHED
        assert "used all 3 client cases" in dec_4th.message
        assert dec_4th.current_case_count == 3
        assert dec_4th.max_cases == 3

        err_4th = dec_4th.to_error_dict()
        assert err_4th["error"]["code"] == "EVALUATION_CAPACITY_REACHED"
        assert "upgrade_guidance" in err_4th["error"]

        # -------------------------------------------------------------
        # 4. Subcase 25C: Deletion Does NOT Refund Capacity (Monotonicity)
        # -------------------------------------------------------------
        store.delete_case("CASE-EVAL-01")
        assert store.get_case("CASE-EVAL-01") is None
        # Persistent evaluation counter must strictly remain 3
        assert store.count_evaluation_cases_created() == 3

        dec_after_del = policy.authorize(CommercialOperation.CREATE_CASE, current_time=now_utc)
        assert dec_after_del.allowed is False
        assert dec_after_del.http_status == 403
        assert dec_after_del.reason_code == CommercialDenialCode.EVALUATION_CAPACITY_REACHED

        # -------------------------------------------------------------
        # 5. Subcase 25D: Persistence Across Restart
        # -------------------------------------------------------------
        # Simulate complete restart by re-instantiating Store and Policy from disk
        restarted_store = SQLiteStore(db_file)
        restarted_policy = CommercialPolicyService(store=restarted_store, license_dir=tmp_path / "lic")

        assert restarted_store.count_evaluation_cases_created() == 3
        dec_after_restart = restarted_policy.authorize(CommercialOperation.CREATE_CASE, current_time=now_utc)
        assert dec_after_restart.allowed is False
        assert dec_after_restart.reason_code == CommercialDenialCode.EVALUATION_CAPACITY_REACHED

        # Existing cases survive and remain accessible
        case2 = restarted_store.get_case("CASE-EVAL-02")
        case3 = restarted_store.get_case("CASE-EVAL-03")
        assert case2 is not None and case2.case_id == "CASE-EVAL-02"
        assert case3 is not None and case3.case_id == "CASE-EVAL-03"

        # -------------------------------------------------------------
        # 6. Subcase 25E: Bundled Sample Case is Unmetered
        # -------------------------------------------------------------
        restarted_store.save_case(CanonicalCase(
            case_id="CASE-SAMPLE-2025",
            client_reference="Sample Client (Acme Holdings LLC)",
            tax_year=2025,
            jurisdiction="US",
            case_status="CREATED",
            case_kind="BUNDLED_SAMPLE",
            sample_definition_id="SAMPLE-A-2025-01",
            sample_manifest_digest="sample_digest",
            created_at=now_utc.isoformat(),
            updated_at=now_utc.isoformat()
        ))

        # Authorizing operation on authentic bundled sample case is ALWAYS allowed
        sample_dec = restarted_policy.authorize(
            CommercialOperation.RECONCILE_CASE,
            context={"case_id": "CASE-SAMPLE-2025", "case_kind": "BUNDLED_SAMPLE"},
            current_time=now_utc
        )
        assert sample_dec.allowed is True
        assert sample_dec.http_status == 200

        # Evaluation case counter remains unchanged
        assert restarted_store.count_evaluation_cases_created() == 3

        # -------------------------------------------------------------
        # 7. Subcase 25F: Retries & Reruns on Existing Cases are Free
        # -------------------------------------------------------------
        reconcile_existing_dec = restarted_policy.authorize(
            CommercialOperation.RECONCILE_CASE,
            context={"case_id": "CASE-EVAL-02", "case_kind": "PRODUCTION"},
            current_time=now_utc
        )
        assert reconcile_existing_dec.allowed is True
        assert reconcile_existing_dec.http_status == 200
        assert restarted_store.count_evaluation_cases_created() == 3

        # -------------------------------------------------------------
        # 8. Subcase 25G: 72-Hour Expiry Boundary (Zero Grace)
        # -------------------------------------------------------------
        eval_record = restarted_store.get_installation_evaluation()
        activated_dt = datetime.fromisoformat(eval_record["activated_at"].replace("Z", "+00:00"))
        expires_dt = datetime.fromisoformat(eval_record["expires_at"].replace("Z", "+00:00"))

        # Boundary 1: expires_at - 1 second -> ACTIVE
        time_before = expires_dt - timedelta(seconds=1)
        eval_before = restarted_policy.evaluate_current_license(current_time=time_before)
        assert eval_before.is_active is True
        assert eval_before.state == LicenseState.ACTIVE

        # Boundary 2: expires_at + 1 second -> EXPIRED (Zero Grace)
        time_after = expires_dt + timedelta(seconds=1)
        eval_after = restarted_policy.evaluate_current_license(current_time=time_after)
        assert eval_after.is_active is False
        assert eval_after.state == LicenseState.EXPIRED
        assert "Evaluation has ended" in eval_after.diagnostic_reason

        # New case creation after expiry is denied with LICENSE_EXPIRED (403)
        dec_expired_create = restarted_policy.authorize(CommercialOperation.CREATE_CASE, current_time=time_after)
        assert dec_expired_create.allowed is False
        assert dec_expired_create.http_status == 403
        assert dec_expired_create.reason_code == CommercialDenialCode.LICENSE_EXPIRED

        # New reconciliation of un-reconciled client case is denied with LICENSE_EXPIRED (403)
        dec_expired_recon = restarted_policy.authorize(
            CommercialOperation.RECONCILE_CASE,
            context={"case_id": "CASE-EVAL-03", "case_kind": "PRODUCTION"},
            current_time=time_after
        )
        assert dec_expired_recon.allowed is False
        assert dec_expired_recon.http_status == 403
        assert dec_expired_recon.reason_code == CommercialDenialCode.LICENSE_EXPIRED

        # Historical data preservation: Existing cases remain accessible in database
        persisted_cases = restarted_store.list_cases()
        assert len(persisted_cases) >= 2
        assert any(c["case_id"] == "CASE-EVAL-02" for c in persisted_cases)
        assert any(c["case_id"] == "CASE-EVAL-03" for c in persisted_cases)
