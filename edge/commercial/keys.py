"""
VaultBasis MMP-1.5 Commercial License Verification Key Configuration

SECURITY INVARIANT:
This module contains ONLY the public key used to verify commercial license signatures.
The corresponding Commercial License Signing Key (private key) is air-gapped and
MUST NEVER be committed to Git, packaged into releases, or distributed to edge clients.
"""

# Production Commercial License Verification Public Key (Ed25519 32-byte hex)
# This public key verifies licenses issued by TecTixBase Commercial Operations.
COMMERCIAL_LICENSE_VERIFICATION_PUBLIC_KEY_HEX = (
    "a8f793b216c59d6e4b83f0812e176b6d5423f0a1c890123456789abcdef01234"
)
