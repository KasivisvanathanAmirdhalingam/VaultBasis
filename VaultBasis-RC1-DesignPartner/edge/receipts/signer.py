"""
VaultBasis Edge — Outcome Receipt Signer
Conforms to Evidence Contract v0.1 (schemas/receipt/signing-v0.1.md)
"""

from typing import Any, Dict
from cryptography.hazmat.primitives.asymmetric import ed25519

from edge.receipts.canonicalizer import compute_receipt_digest
from edge.receipts.keygen import InstallationKeyManager


class ReceiptSigner:
    """
    Signs canonical outcome receipts using local Ed25519 installation keys.
    """

    def __init__(self, private_key: ed25519.Ed25519PrivateKey):
        self.private_key = private_key
        self.public_key = private_key.public_key()
        self.public_key_hex = InstallationKeyManager.get_public_key_hex(self.public_key)
        self.key_id = InstallationKeyManager.get_key_id(self.public_key)

    def sign_receipt(self, receipt_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Signs a receipt payload conforming to Evidence Contract v0.1.
        
        Steps:
        1. Ensures signer_type, signer_key_id, and signer_public_key match this installation.
        2. Excludes signature field and computes SHA-256 digest of canonical UTF-8 bytes.
        3. Signs the 32-byte digest using Ed25519.
        4. Injects lowercase hex signature into the final receipt dictionary.
        """
        receipt = dict(receipt_payload)

        # Set mandatory signing metadata
        receipt["signer_type"] = "INSTALLATION_KEY"
        receipt["signer_key_id"] = self.key_id
        receipt["signer_public_key"] = self.public_key_hex

        # Ensure receipt_version is explicitly v0.1
        receipt["receipt_version"] = "v0.1"
        receipt["canonicalization_version"] = "v0.1"

        # Compute 32-byte canonical digest (excluding signature)
        digest = compute_receipt_digest(receipt)

        # Ed25519 signature over the 32-byte digest
        signature_bytes = self.private_key.sign(digest)
        receipt["signature"] = signature_bytes.hex().lower()

        return receipt
