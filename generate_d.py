import os
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Make deterministic keypair
pk_bytes = bytes([1] * 32)
private_key = ed25519.Ed25519PrivateKey.from_private_bytes(pk_bytes)
pub_key = private_key.public_key()
pub_key_hex = pub_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex().lower()

BASE_DIR = Path("tests/quality/golden/layer-d-verifier")
BASE_DIR.mkdir(parents=True, exist_ok=True)

from edge.receipts.canonicalizer import compute_receipt_digest

def create_receipt(case_id="G001", outcome_state="MATCHED"):
    receipt = {
        "receipt_version": "v0.1",
        "canonicalization_version": "v0.1",
        "case_id": case_id,
        "outcome_state": outcome_state,
        "timestamp": "2026-01-01T00:00:00Z",
        "evidence_hash": "deadbeef",
        "signer_type": "INSTALLATION_KEY",
        "signer_key_id": "test_key",
        "signer_public_key": pub_key_hex
    }
    digest = compute_receipt_digest(receipt)
    sig = private_key.sign(digest).hex().lower()
    receipt["signature"] = sig
    return receipt

def write_fixture(f_id, receipt_json_str, expected_status):
    d = BASE_DIR / f_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "receipt.json").write_text(receipt_json_str)
    
    manifest = {
        "fixture_id": f_id,
        "layer": "D",
        "status": "ACTIVE",
        "semantic_spec_version": "0.1",
        "evidence_contract_version": "0.1",
        "description": f"Verifier test for {f_id}",
        "expected": {
            "overall_status": expected_status
        }
    }
    (d / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (d / "expected.json").write_text(json.dumps(manifest["expected"], indent=2))

# V001_valid_receipt
valid_rec = create_receipt()
write_fixture("V001_valid_receipt", json.dumps(valid_rec, indent=2), "VALID")

# V002_tampered_outcome
t2 = create_receipt()
t2["outcome_state"] = "BASIS_DIFFERENCE"
write_fixture("V002_tampered_outcome", json.dumps(t2, indent=2), "INVALID_SIGNATURE")

# V003_tampered_amount
t3 = create_receipt()
t3["financial_value"] = "99.99"
write_fixture("V003_tampered_amount", json.dumps(t3, indent=2), "INVALID_SIGNATURE")

# V004_tampered_evidence_hash
t4 = create_receipt()
t4["evidence_hash"] = "badbeef"
write_fixture("V004_tampered_evidence_hash", json.dumps(t4, indent=2), "INVALID_SIGNATURE")

# V005_wrong_public_key
t5 = create_receipt()
t5["signer_public_key"] = bytes([2]*32).hex().lower()
write_fixture("V005_wrong_public_key", json.dumps(t5, indent=2), "INVALID_SIGNATURE")

# V006_invalid_signature
t6 = create_receipt()
t6["signature"] = "a" * 128
write_fixture("V006_invalid_signature", json.dumps(t6, indent=2), "INVALID_SIGNATURE")

# V007_noncanonical_input (unordered/spaced JSON)
t7 = create_receipt()
# json string with extra spaces and weird key order
t7_str = '{ \n  "signature": "' + t7["signature"] + '",\n  "case_id": "' + t7["case_id"] + '",\n' + \
         '  "receipt_version": "v0.1", "canonicalization_version": "v0.1",\n' + \
         '  "outcome_state": "MATCHED", "timestamp": "2026-01-01T00:00:00Z",\n' + \
         '  "evidence_hash": "deadbeef", "signer_type": "INSTALLATION_KEY",\n' + \
         '  "signer_key_id": "test_key", "signer_public_key": "' + t7["signer_public_key"] + '"\n}'
write_fixture("V007_noncanonical_input", t7_str, "VALID")

# V008_unknown_contract_version
t8 = create_receipt()
t8["receipt_version"] = "v2.0"
write_fixture("V008_unknown_contract_version", json.dumps(t8, indent=2), "UNSUPPORTED_CONTRACT")

# V009_unresolved_receipt
t9 = create_receipt(outcome_state="UNRESOLVED_DATA")
write_fixture("V009_unresolved_receipt", json.dumps(t9, indent=2), "VALID")

# V010_unknown_outcome_state
t10 = create_receipt()
t10["outcome_state"] = "SUPER_MATCHED"
write_fixture("V010_unknown_outcome_state", json.dumps(t10, indent=2), "INVALID_SCHEMA")

# V011_missing_signed_field
t11 = create_receipt()
del t11["case_id"]
write_fixture("V011_missing_signed_field", json.dumps(t11, indent=2), "INVALID_SCHEMA")

# V012_extra_unsigned_semantic_field
t12 = create_receipt()
t12["extra_field"] = "bad"
write_fixture("V012_extra_unsigned_semantic_field", json.dumps(t12, indent=2), "INVALID_SIGNATURE")
