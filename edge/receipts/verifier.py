import json
from typing import Any, Dict
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

from edge.receipts.canonicalizer import compute_receipt_digest

KNOWN_OUTCOME_STATES = [
    "MATCHED", "UNRESOLVED_DATA", "EXACT_DUPLICATE", "CONFLICTING_DUPLICATE",
    "BASIS_DIFFERENCE", "PROCEEDS_DIFFERENCE", "QUANTITY_DIFFERENCE", "DATE_DIFFERENCE",
    "MULTIPLE_DIFFERENCES"
]

class ReceiptVerifier:
    """
    Independently verifies Outcome Receipts based on Evidence Contract v0.1.
    """

    @classmethod
    def verify(cls, receipt_dict: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            "schema_status": "VALID",
            "contract_status": "VALID",
            "canonicalization_status": "VALID",
            "signature_status": "VALID",
            "overall_status": "VALID"
        }

        # 1. Contract / Schema checks
        if "receipt_version" not in receipt_dict or receipt_dict["receipt_version"] != "v0.1":
            result["contract_status"] = "UNSUPPORTED_CONTRACT"
            result["overall_status"] = "UNSUPPORTED_CONTRACT"
            return result
            
        if "outcome_state" not in receipt_dict or receipt_dict["outcome_state"] not in KNOWN_OUTCOME_STATES:
            result["schema_status"] = "INVALID_SCHEMA"
            result["overall_status"] = "INVALID_SCHEMA"
            return result

        required_fields = ["case_id", "outcome_state", "signer_public_key", "signature"]
        for req in required_fields:
            if req not in receipt_dict:
                result["schema_status"] = "INVALID_SCHEMA"
                result["overall_status"] = "INVALID_SCHEMA"
                return result

        # 2. Signature verification
        pub_key_hex = receipt_dict["signer_public_key"]
        sig_hex = receipt_dict["signature"]
        
        try:
            pub_key_bytes = bytes.fromhex(pub_key_hex)
            if len(pub_key_bytes) != 32:
                raise ValueError("Invalid public key length")
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_key_bytes)
        except Exception:
            result["signature_status"] = "INVALID_SIGNATURE"
            result["overall_status"] = "INVALID_SIGNATURE"
            return result

        try:
            sig_bytes = bytes.fromhex(sig_hex)
        except Exception:
            result["signature_status"] = "INVALID_SIGNATURE"
            result["overall_status"] = "INVALID_SIGNATURE"
            return result

        digest = compute_receipt_digest(receipt_dict)

        try:
            pub_key.verify(sig_bytes, digest)
        except InvalidSignature:
            result["signature_status"] = "INVALID_SIGNATURE"
            result["overall_status"] = "INVALID_SIGNATURE"
            return result

        return result
