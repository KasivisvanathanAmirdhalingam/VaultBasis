import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ed25519
from edge.receipts.signer import ReceiptSigner
from apps.verifier.verify_receipt import verify_outcome_receipt, compute_receipt_digest


def create_candidate7_test_receipts():
    """
    Generates authentic Candidate 7 Rev 1 (preliminary) and Rev 2 (reviewed) receipts
    signed with a valid Ed25519 installation key for UAT-24 standalone verification tests.
    """
    priv_key = ed25519.Ed25519PrivateKey.generate()
    signer = ReceiptSigner(priv_key)
    fixture_dir = Path("tests/fixtures/uat21")
    broker_bytes = (fixture_dir / "broker_realistic.csv").read_bytes()
    ledger_bytes = (fixture_dir / "ledger_realistic.csv").read_bytes()
    
    import hashlib
    b_hash = hashlib.sha256(broker_bytes).hexdigest()
    l_hash = hashlib.sha256(ledger_bytes).hexdigest()

    # Base Deterministic Reconciliation Findings
    material_diffs = [
        {
            "difference_id": "DIFF-ETH-001",
            "difference_state": "PROCEEDS_DIFFERENCE",
            "asset": "ETH",
            "source_a_ref": "broker_realistic.csv:Row 2",
            "source_a_value": "3100.50",
            "source_b_ref": "ledger_realistic.csv:Row 2",
            "source_b_value": "3300.00",
            "variance": "199.50",
            "description": "Proceeds differ by $199.50."
        },
        {
            "difference_id": "DIFF-SOL-001",
            "difference_state": "BASIS_DIFFERENCE",
            "asset": "SOL",
            "source_a_ref": "broker_realistic.csv:Row 3",
            "source_a_value": "1200.00",
            "source_b_ref": "ledger_realistic.csv:Row 3",
            "source_b_value": "1400.00",
            "variance": "200.00",
            "description": "Basis differs by $200.00."
        }
    ]
    unresolved_items = [
        {
            "item_id": "UNRES-ADA-001",
            "reason_code": "BASIS_UNAVAILABLE",
            "affected_source_id": "SRC-BROKER-01",
            "affected_row_ref": "broker_realistic.csv:Row 4",
            "description": "Cost basis unavailable in source data."
        }
    ]

    # Rev 1 (Preliminary Receipt)
    rev1_payload = {
        "receipt_version": "v0.1",
        "receipt_id": "550e8400-e29b-41d4-a716-446655440001",
        "case_id": "CASE-UAT24-ISOLATED-TEST",
        "revision": 1,
        "claim_type": "DIGITAL_ASSET_TAX_RECONCILIATION",
        "claimant_type": "TAXPAYER",
        "producer_reference": "VaultBasis Edge v1.5.0-rc3",
        "source_ids": ["SRC-BROKER-01", "SRC-LEDGER-01"],
        "source_hashes": {
            "SRC-BROKER-01": b_hash,
            "SRC-LEDGER-01": l_hash
        },
        "source_schema_ids": {
            "SRC-BROKER-01": "IRS_1099DA_2025",
            "SRC-LEDGER-01": "KOINLY_CAPITAL_GAINS_CSV_V1"
        },
        "canonicalization_version": "v0.1",
        "ruleset_id": "VB_US_1099DA_2025_R1",
        "engine_version": "1.5.0-rc3",
        "policy_version": "1.5.0",
        "assurance_level": "L2_EVIDENCE_RECONCILED",
        "outcome_state": "UNRESOLVED_DATA",
        "material_differences": material_diffs,
        "unresolved_items": unresolved_items,
        "human_review_state": "UNREVIEWED",
        "ai_involvement_level": "NONE",
        "created_at": "2026-10-09T12:00:00Z"
    }
    signed_rev1 = signer.sign_receipt(rev1_payload)

    # Rev 2 (Reviewed Receipt)
    rev2_payload = copy.deepcopy(rev1_payload)
    rev2_payload["receipt_id"] = "550e8400-e29b-41d4-a716-446655440002"
    rev2_payload["revision"] = 2
    rev2_payload["prior_receipt_id"] = signed_rev1["receipt_id"]
    rev2_payload["human_review_state"] = "REVIEWED_ANNOTATED"
    rev2_payload["created_at"] = "2026-10-09T12:30:00Z"
    signed_rev2 = signer.sign_receipt(rev2_payload)

    return signed_rev1, signed_rev2


def test_uat24_standalone_offline_verifier_in_isolated_environment():
    """
    Permanent regression test for UAT-24 (Standalone Offline Verifier & Tamper Detection).
    
    Verifies that the standalone verifier runs completely independently from a clean isolated
    directory with ZERO network calls, zero accounts, zero licenses, and zero running Edge daemons.
    """
    signed_rev1, signed_rev2 = create_candidate7_test_receipts()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Copy standalone verifier script and schema to clean isolated temp directory
        verifier_script = Path("apps/verifier/verify_receipt.py")
        schema_file = Path("schemas/receipt/receipt-v0.1.json")
        
        target_verifier = tmp_path / "verify_receipt.py"
        target_schema = tmp_path / "receipt-v0.1.json"
        
        shutil.copy(verifier_script, target_verifier)
        shutil.copy(schema_file, target_schema)

        # -------------------------------------------------------------
        # Subcase 24A: Authentic Preliminary Rev 1 Receipt
        # -------------------------------------------------------------
        p_rev1 = tmp_path / "receipt_rev1.json"
        p_rev1.write_text(json.dumps(signed_rev1, indent=2))

        cmd_rev1 = [sys.executable, str(target_verifier), str(p_rev1), "--json"]
        proc_rev1 = subprocess.run(cmd_rev1, cwd=str(tmp_path), capture_output=True, text=True)
        assert proc_rev1.returncode == 0
        res_rev1 = json.loads(proc_rev1.stdout)
        
        assert res_rev1["overall_status"] == "PASS"
        assert res_rev1["is_valid"] is True
        assert res_rev1["checks"]["signature_authenticity"] == "PASS"
        assert res_rev1["checks"]["schema_conformance"] == "PASS"
        assert res_rev1["checks"]["key_fingerprint"] == "PASS"
        assert res_rev1["checks"]["installation_identity"] == "NOT_AUTHENTICATED"
        assert res_rev1["checks"]["tax_correctness"] == "NOT_DETERMINED"
        assert res_rev1["checks"]["source_hashes"] == "NOT_PERFORMED"

        # -------------------------------------------------------------
        # Subcase 24B: Authentic Reviewed Rev 2 Receipt
        # -------------------------------------------------------------
        p_rev2 = tmp_path / "receipt_rev2.json"
        p_rev2.write_text(json.dumps(signed_rev2, indent=2))

        cmd_rev2 = [sys.executable, str(target_verifier), str(p_rev2), "--json"]
        proc_rev2 = subprocess.run(cmd_rev2, cwd=str(tmp_path), capture_output=True, text=True)
        assert proc_rev2.returncode == 0
        res_rev2 = json.loads(proc_rev2.stdout)
        
        assert res_rev2["overall_status"] == "PASS"
        assert res_rev2["is_valid"] is True
        assert res_rev2["checks"]["signature_authenticity"] == "PASS"
        assert res_rev2["checks"]["schema_conformance"] == "PASS"
        assert res_rev2["checks"]["tax_correctness"] == "NOT_DETERMINED"

        # -------------------------------------------------------------
        # Subcase 24C: Semantically Tampered Signed Payloads (Valid JSON)
        # -------------------------------------------------------------
        # Tamper 1: Modify variance from "199.50" to "0.00"
        tampered_1 = copy.deepcopy(signed_rev2)
        tampered_1["material_differences"][0]["variance"] = "0.00"
        p_tamper1 = tmp_path / "receipt_tampered_variance.json"
        p_tamper1.write_text(json.dumps(tampered_1, indent=2))

        cmd_t1 = [sys.executable, str(target_verifier), str(p_tamper1), "--json"]
        proc_t1 = subprocess.run(cmd_t1, cwd=str(tmp_path), capture_output=True, text=True)
        assert proc_t1.returncode == 1
        res_t1 = json.loads(proc_t1.stdout)
        assert res_t1["overall_status"] == "FAIL"
        assert res_t1["is_valid"] is False
        assert res_t1["checks"]["signature_authenticity"] == "FAIL"
        assert any("Ed25519 signature verification FAILED" in err for err in res_t1["errors"])

        # Tamper 2: Modify human_review_state from "REVIEWED_ANNOTATED" to "UNREVIEWED"
        tampered_2 = copy.deepcopy(signed_rev2)
        tampered_2["human_review_state"] = "UNREVIEWED"
        p_tamper2 = tmp_path / "receipt_tampered_review_state.json"
        p_tamper2.write_text(json.dumps(tampered_2, indent=2))

        proc_t2 = subprocess.run([sys.executable, str(target_verifier), str(p_tamper2), "--json"], cwd=str(tmp_path), capture_output=True, text=True)
        assert proc_t2.returncode == 1
        res_t2 = json.loads(proc_t2.stdout)
        assert res_t2["overall_status"] == "FAIL"
        assert res_t2["checks"]["signature_authenticity"] == "FAIL"

        # Tamper 3: Modify outcome_state from "UNRESOLVED_DATA" to "MATCHED"
        tampered_3 = copy.deepcopy(signed_rev2)
        tampered_3["outcome_state"] = "MATCHED"
        p_tamper3 = tmp_path / "receipt_tampered_outcome.json"
        p_tamper3.write_text(json.dumps(tampered_3, indent=2))

        proc_t3 = subprocess.run([sys.executable, str(target_verifier), str(p_tamper3), "--json"], cwd=str(tmp_path), capture_output=True, text=True)
        assert proc_t3.returncode == 1
        res_t3 = json.loads(proc_t3.stdout)
        assert res_t3["overall_status"] == "FAIL"
        assert res_t3["checks"]["signature_authenticity"] == "FAIL"

        # -------------------------------------------------------------
        # Subcase 24D: Structurally Malformed / Invalid Receipts
        # -------------------------------------------------------------
        # Malformed 1: Missing signature field
        bad_struct_1 = copy.deepcopy(signed_rev1)
        bad_struct_1.pop("signature")
        p_bad1 = tmp_path / "receipt_bad_missing_sig.json"
        p_bad1.write_text(json.dumps(bad_struct_1, indent=2))

        proc_b1 = subprocess.run([sys.executable, str(target_verifier), str(p_bad1), "--json"], cwd=str(tmp_path), capture_output=True, text=True)
        assert proc_b1.returncode == 1
        res_b1 = json.loads(proc_b1.stdout)
        assert res_b1["overall_status"] == "FAIL"
        assert res_b1["checks"]["schema_conformance"] == "FAIL"
        assert any("Schema validation error" in err for err in res_b1["errors"])

        # Malformed 2: Unsupported receipt version
        bad_struct_2 = copy.deepcopy(signed_rev1)
        bad_struct_2["receipt_version"] = "v9.9"
        p_bad2 = tmp_path / "receipt_bad_version.json"
        p_bad2.write_text(json.dumps(bad_struct_2, indent=2))

        proc_b2 = subprocess.run([sys.executable, str(target_verifier), str(p_bad2), "--json"], cwd=str(tmp_path), capture_output=True, text=True)
        assert proc_b2.returncode == 1
        res_b2 = json.loads(proc_b2.stdout)
        assert res_b2["overall_status"] == "FAIL"

        # Malformed 3: Corrupt public key length
        bad_struct_3 = copy.deepcopy(signed_rev1)
        bad_struct_3["signer_public_key"] = "DEADBEEF"
        p_bad3 = tmp_path / "receipt_bad_pubkey.json"
        p_bad3.write_text(json.dumps(bad_struct_3, indent=2))

        proc_b3 = subprocess.run([sys.executable, str(target_verifier), str(p_bad3), "--json"], cwd=str(tmp_path), capture_output=True, text=True)
        assert proc_b3.returncode == 1
        res_b3 = json.loads(proc_b3.stdout)
        assert res_b3["overall_status"] == "FAIL"

        # -------------------------------------------------------------
        # Subcase 24E: Receipt-Only Verification (Source Files Absent)
        # -------------------------------------------------------------
        # In this clean tmp_path, NO broker or ledger CSV files exist.
        cmd_receipt_only = [sys.executable, str(target_verifier), str(p_rev1), "--no-color"]
        proc_ro = subprocess.run(cmd_receipt_only, cwd=str(tmp_path), capture_output=True, text=True)
        assert proc_ro.returncode == 0
        output_ro = proc_ro.stdout
        
        assert "PAYLOAD & SIGNATURE VERIFIED" in output_ro
        assert "PAYLOAD INTEGRITY:       VALID" in output_ro
        assert "SIGNATURE AUTHENTICITY:  VALID" in output_ro
        assert "TAX CORRECTNESS:         NOT DETERMINED BY VAULTBASIS" in output_ro
        # Source file hashes check is NOT present in stdout because --evidence-dir was not passed
        assert "[5] SOURCE FILE HASHES" not in output_ro


def test_uat24_standalone_verifier_with_evidence_directory():
    """
    Verifies that when source files are present in an evidence directory,
    the standalone verifier accurately re-hashes the files against source_hashes.
    """
    signed_rev1, _ = create_candidate7_test_receipts()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()

        # Place matching source files in evidence_dir
        fixture_dir = Path("tests/fixtures/uat21")
        (evidence_dir / "SRC-BROKER-01.csv").write_bytes((fixture_dir / "broker_realistic.csv").read_bytes())
        (evidence_dir / "SRC-LEDGER-01.csv").write_bytes((fixture_dir / "ledger_realistic.csv").read_bytes())

        # 1. Matching Evidence Directory -> source_hashes: PASS
        res_matching = verify_outcome_receipt(signed_rev1, evidence_dir=evidence_dir)
        assert res_matching.is_valid is True
        assert res_matching.source_hashes_valid is True
        assert res_matching.to_dict()["checks"]["source_hashes"] == "PASS"

        # 2. Corrupted Source File -> source_hashes: FAIL
        (evidence_dir / "SRC-BROKER-01.csv").write_bytes(b"corrupted broker bytes")
        res_corrupt = verify_outcome_receipt(signed_rev1, evidence_dir=evidence_dir)
        assert res_corrupt.is_valid is False
        assert res_corrupt.source_hashes_valid is False
        assert res_corrupt.to_dict()["checks"]["source_hashes"] == "FAIL"
        assert any("hash mismatch" in err for err in res_corrupt.errors)
