"""
VaultBasis — Slice 1 Test Suite
Tests Evidence Contract v0.1, Canonicalization, Ed25519 Signing, and Independent Verification.
"""

import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from edge.receipts.canonicalizer import canonical_json_bytes, compute_receipt_digest
from edge.receipts.keygen import InstallationKeyManager
from edge.receipts.signer import ReceiptSigner
from apps.verifier.verify_receipt import verify_outcome_receipt, SCHEMA_PATH


@pytest.fixture
def temp_key_dir(tmp_path):
    key_dir = tmp_path / "keys"
    return key_dir


@pytest.mark.smoke
def test_key_generation_and_permissions(temp_key_dir):
    km = InstallationKeyManager(temp_key_dir)
    priv_key, pub_key = km.ensure_keypair()

    assert isinstance(priv_key, ed25519.Ed25519PrivateKey)
    assert isinstance(pub_key, ed25519.Ed25519PublicKey)
    assert km.private_key_path.exists()
    assert km.public_key_path.exists()

    # Verify POSIX permissions on private key: 0600 (owner read/write only)
    file_mode = stat.S_IMODE(os.stat(km.private_key_path).st_mode)
    assert file_mode == 0o600

    # Verify fingerprint calculation
    raw_pub = pub_key.public_bytes_raw()
    expected_fingerprint = hashlib.sha256(raw_pub).hexdigest()
    assert km.get_key_id(pub_key) == expected_fingerprint

    # Verify loading existing key yields same keypair
    km2 = InstallationKeyManager(temp_key_dir)
    priv2, pub2 = km2.ensure_keypair()
    assert km2.get_key_id(pub2) == expected_fingerprint


@pytest.mark.smoke
def test_canonicalization_determinism():
    dict1 = {"b": 2, "a": 1, "nested": {"z": 9, "y": 8}}
    dict2 = {"nested": {"y": 8, "z": 9}, "a": 1, "b": 2}

    b1 = canonical_json_bytes(dict1)
    b2 = canonical_json_bytes(dict2)

    assert b1 == b2
    assert b1 == b'{"a":1,"b":2,"nested":{"y":8,"z":9}}'


@pytest.mark.smoke
def test_slice1_end_to_end_receipt_flow(tmp_path):
    # 1. Setup Key Manager and Signer
    km = InstallationKeyManager(tmp_path / "keys")
    priv_key, pub_key = km.ensure_keypair()
    signer = ReceiptSigner(priv_key)

    # 2. Build Reference Reconciliation Payload (per PRD §59 Example)
    source_1099_content = b"Mock 1099-DA: Proceeds $18,400, Basis $12,100"
    source_koinly_content = b"Mock Koinly CSV: Proceeds $18,400, Basis $16,300"
    hash_1099 = hashlib.sha256(source_1099_content).hexdigest()
    hash_koinly = hashlib.sha256(source_koinly_content).hexdigest()

    receipt_payload = {
        "receipt_version": "v0.1",
        "receipt_id": "11111111-2222-3333-4444-555555555555",
        "case_id": "case_2026_demo_001",
        "claim_type": "DIGITAL_ASSET_TAX_RECONCILIATION",
        "claimant_type": "TAXPAYER",
        "producer_reference": "VaultBasis Edge v0.1.0-preview",
        "source_ids": ["src_1099da_coinbase", "src_koinly_gains"],
        "source_hashes": {
            "src_1099da_coinbase": hash_1099,
            "src_koinly_gains": hash_koinly
        },
        "source_schema_ids": {
            "src_1099da_coinbase": "IRS_1099DA_2025_PREVIEW",
            "src_koinly_gains": "KOINLY_CAPITAL_GAINS_CSV_V1"
        },
        "canonicalization_version": "v0.1",
        "ruleset_id": "US_IRC_1099DA_2025_2026_V1",
        "engine_version": "0.1.0",
        "policy_version": "0.1.0",
        "assurance_level": "L2_EVIDENCE_RECONCILED",
        "outcome_state": "BASIS_DIFFERENCE",
        "material_differences": [
            {
                "difference_id": "diff_001",
                "difference_state": "BASIS_DIFFERENCE",
                "asset": "BTC",
                "source_a_ref": "1099-DA:Box1g",
                "source_a_value": "12100.00",
                "source_b_ref": "Koinly:CostBasis",
                "source_b_value": "16300.00",
                "variance": "4200.00",
                "description": "Basis differs by $4,200. Review source acquisition records and reporting scope."
            }
        ],
        "unresolved_items": [],
        "provenance_references": [
            {
                "reference_id": "prov_001",
                "source_id": "src_1099da_coinbase",
                "row_ref": "Line:1",
                "content_hash": hash_1099
            }
        ],
        "human_review_state": "UNREVIEWED",
        "ai_involvement_level": "NONE",
        "created_at": "2026-09-26T12:00:00Z"
    }

    # 3. Sign Receipt
    signed_receipt = signer.sign_receipt(receipt_payload)

    assert "signature" in signed_receipt
    assert signed_receipt["signer_type"] == "INSTALLATION_KEY"
    assert signed_receipt["signer_key_id"] == signer.key_id
    assert signed_receipt["signer_public_key"] == signer.public_key_hex

    # 4. Independent Verification
    # Setup evidence dir with source files
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "src_1099da_coinbase.txt").write_bytes(source_1099_content)
    (evidence_dir / "src_koinly_gains.txt").write_bytes(source_koinly_content)

    res = verify_outcome_receipt(signed_receipt, evidence_dir=evidence_dir)

    assert res.is_valid is True
    assert res.schema_valid is True
    assert res.version_supported is True
    assert res.key_fingerprint_valid is True
    assert res.signature_valid is True
    assert res.source_hashes_valid is True
    assert res.outcome_state == "BASIS_DIFFERENCE"


@pytest.mark.regression
def test_tamper_detection_financial_value(tmp_path):
    km = InstallationKeyManager(tmp_path / "keys")
    priv_key, _ = km.ensure_keypair()
    signer = ReceiptSigner(priv_key)

    receipt_payload = {
        "receipt_version": "v0.1",
        "receipt_id": "22222222-3333-4444-5555-666666666666",
        "case_id": "case_tamper_test",
        "claim_type": "DIGITAL_ASSET_TAX_RECONCILIATION",
        "claimant_type": "TAXPAYER",
        "producer_reference": "VaultBasis Edge v0.1.0-preview",
        "source_ids": ["src_1"],
        "source_hashes": {"src_1": hashlib.sha256(b"raw").hexdigest()},
        "source_schema_ids": {"src_1": "GENERIC"},
        "canonicalization_version": "v0.1",
        "ruleset_id": "TEST_RULES",
        "engine_version": "0.1.0",
        "policy_version": "0.1.0",
        "assurance_level": "L1_CANONICAL_CONSISTENCY",
        "outcome_state": "PROCEEDS_DIFFERENCE",
        "material_differences": [
            {
                "difference_id": "diff_001",
                "difference_state": "PROCEEDS_DIFFERENCE",
                "asset": "ETH",
                "source_a_ref": "A:1",
                "source_a_value": "100.00",
                "source_b_ref": "B:1",
                "source_b_value": "110.00",
                "variance": "10.00",
                "description": "Proceeds variance"
            }
        ],
        "unresolved_items": [],
        "provenance_references": [
            {
                "reference_id": "ref_1",
                "source_id": "src_1",
                "row_ref": "Row 1",
                "content_hash": hashlib.sha256(b"raw").hexdigest()
            }
        ],
        "human_review_state": "UNREVIEWED",
        "ai_involvement_level": "NONE",
        "created_at": "2026-09-26T12:00:00Z"
    }

    signed_receipt = signer.sign_receipt(receipt_payload)

    # TAMPER: Modify variance by $0.01 (e.g. fraudulent alteration)
    tampered_receipt = dict(signed_receipt)
    tampered_receipt["material_differences"] = [
        dict(signed_receipt["material_differences"][0])
    ]
    tampered_receipt["material_differences"][0]["variance"] = "10.01"

    res = verify_outcome_receipt(tampered_receipt)
    assert res.is_valid is False
    assert res.signature_valid is False
    assert any("signature verification FAILED" in e for e in res.errors)


@pytest.mark.regression
def test_tamper_detection_outcome_state(tmp_path):
    km = InstallationKeyManager(tmp_path / "keys")
    priv_key, _ = km.ensure_keypair()
    signer = ReceiptSigner(priv_key)

    receipt_payload = {
        "receipt_version": "v0.1",
        "receipt_id": "33333333-4444-5555-6666-777777777777",
        "case_id": "case_state_tamper",
        "claim_type": "DIGITAL_ASSET_TAX_RECONCILIATION",
        "claimant_type": "TAXPAYER",
        "producer_reference": "VaultBasis Edge v0.1.0-preview",
        "source_ids": ["src_1"],
        "source_hashes": {"src_1": hashlib.sha256(b"src").hexdigest()},
        "source_schema_ids": {"src_1": "GENERIC"},
        "canonicalization_version": "v0.1",
        "ruleset_id": "TEST_RULES",
        "engine_version": "0.1.0",
        "policy_version": "0.1.0",
        "assurance_level": "L1_CANONICAL_CONSISTENCY",
        "outcome_state": "UNRESOLVED_DATA",
        "material_differences": [],
        "unresolved_items": [
            {
                "item_id": "unres_1",
                "reason_code": "PRICE_UNAVAILABLE",
                "affected_source_id": "src_1",
                "affected_row_ref": "Row 5",
                "description": "Missing valuation"
            }
        ],
        "provenance_references": [],
        "human_review_state": "UNREVIEWED",
        "ai_involvement_level": "NONE",
        "created_at": "2026-09-26T12:00:00Z"
    }

    signed_receipt = signer.sign_receipt(receipt_payload)

    # TAMPER: Falsify outcome_state from UNRESOLVED_DATA to MATCHED
    tampered_receipt = dict(signed_receipt)
    tampered_receipt["outcome_state"] = "MATCHED"

    res = verify_outcome_receipt(tampered_receipt)
    assert res.is_valid is False
    assert res.signature_valid is False


@pytest.mark.smoke
def test_cli_verifier_execution(tmp_path):
    km = InstallationKeyManager(tmp_path / "keys")
    priv_key, _ = km.ensure_keypair()
    signer = ReceiptSigner(priv_key)

    receipt_payload = {
        "receipt_version": "v0.1",
        "receipt_id": "44444444-5555-6666-7777-888888888888",
        "case_id": "case_cli_test",
        "claim_type": "DIGITAL_ASSET_TAX_RECONCILIATION",
        "claimant_type": "CPA_FIRM",
        "producer_reference": "VaultBasis Edge v0.1.0-preview",
        "source_ids": ["src_1"],
        "source_hashes": {"src_1": hashlib.sha256(b"payload").hexdigest()},
        "source_schema_ids": {"src_1": "GENERIC"},
        "canonicalization_version": "v0.1",
        "ruleset_id": "TEST_RULES",
        "engine_version": "0.1.0",
        "policy_version": "0.1.0",
        "assurance_level": "L2_EVIDENCE_RECONCILED",
        "outcome_state": "MATCHED",
        "material_differences": [],
        "unresolved_items": [],
        "provenance_references": [],
        "human_review_state": "REVIEWED_ACCEPTED",
        "ai_involvement_level": "NONE",
        "created_at": "2026-09-26T12:00:00Z"
    }

    signed = signer.sign_receipt(receipt_payload)
    receipt_file = tmp_path / "test_receipt.json"
    receipt_file.write_text(json.dumps(signed, indent=2))

    # Invoke CLI verifier directly via python with --no-color
    cli_script = repo_root / "apps" / "verifier" / "verify_receipt.py"
    proc = subprocess.run(
        [sys.executable, str(cli_script), str(receipt_file), "--no-color"],
        capture_output=True,
        text=True
    )

    assert proc.returncode == 0
    assert "VAULTBASIS INDEPENDENT OUTCOME VERIFICATION REPORT" in proc.stdout
    assert "PAYLOAD & SIGNATURE VERIFIED" in proc.stdout
    assert "[1] PAYLOAD INTEGRITY:       VALID" in proc.stdout
    assert "[2] SIGNATURE AUTHENTICITY:  VALID" in proc.stdout
    assert "[3] CONTRACT COMPATIBILITY:  COMPATIBLE" in proc.stdout
    assert "[4] TAX CORRECTNESS:         NOT DETERMINED BY VAULTBASIS" in proc.stdout
    assert "LIMITATION NOTICE" in proc.stdout
