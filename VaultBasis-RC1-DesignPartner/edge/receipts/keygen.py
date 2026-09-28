"""
VaultBasis Edge — Installation Key Management (Ed25519)
Conforms to Evidence Contract v0.1 (schemas/receipt/signing-v0.1.md)
"""

import hashlib
import os
from pathlib import Path
from typing import Tuple

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


class InstallationKeyManager:
    """
    Manages local per-installation Ed25519 signing keys.
    Private keys are stored locally with 0600 permissions and are never transmitted.
    """

    def __init__(self, key_dir: Path):
        self.key_dir = Path(key_dir)
        self.private_key_path = self.key_dir / "installation_ed25519.key"
        self.public_key_path = self.key_dir / "installation_ed25519.pub"

    def ensure_keypair(self) -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        """
        Loads existing keypair or generates a fresh Ed25519 keypair if none exists.
        Ensures strict 0600 POSIX permissions on the private key file.
        """
        self.key_dir.mkdir(parents=True, exist_ok=True)

        if self.private_key_path.exists():
            with open(self.private_key_path, "rb") as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
                if not isinstance(private_key, ed25519.Ed25519PrivateKey):
                    raise ValueError("Stored key is not a valid Ed25519 private key")
            public_key = private_key.public_key()
            return private_key, public_key

        # Generate fresh Ed25519 keypair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Serialize private key to PEM
        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Write private key with atomic 0600 permissions
        fd = os.open(
            str(self.private_key_path),
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            0o600
        )
        with open(fd, "wb") as f:
            f.write(pem_private)

        # Serialize public key to hex / raw bytes
        raw_public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        with open(self.public_key_path, "w") as f:
            f.write(raw_public_bytes.hex())

        return private_key, public_key

    @staticmethod
    def get_public_key_hex(public_key: ed25519.Ed25519PublicKey) -> str:
        """Returns 64-character lowercase hex representation of the 32-byte public key."""
        raw_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return raw_bytes.hex().lower()

    @staticmethod
    def get_key_id(public_key: ed25519.Ed25519PublicKey) -> str:
        """
        Computes the SHA-256 fingerprint (hex) of the raw 32-byte public key.
        This corresponds to 'signer_key_id' in Evidence Contract v0.1.
        """
        raw_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return hashlib.sha256(raw_bytes).hexdigest().lower()
