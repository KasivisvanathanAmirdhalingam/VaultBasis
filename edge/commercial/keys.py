"""
VaultBasis MMP-1.5 Commercial License Verification Key Configuration

SECURITY INVARIANT:
This module contains ONLY the public keys used to verify commercial license signatures.
The corresponding Commercial License Signing Key (private key) is air-gapped and
MUST NEVER be committed to Git, packaged into releases, or distributed to edge clients.
"""

from typing import Dict, Optional

# Primary Commercial Verification Public Key (Ed25519 32-byte hex)
# Corresponds to key_id "k1"
COMMERCIAL_LICENSE_VERIFICATION_PUBLIC_KEY_HEX = (
    "a8f793b216c59d6e4b83f0812e176b6d5423f0a1c890123456789abcdef01234"
)

# Immutable Trusted Keyring mapping key_id -> public_key_hex
# Supports seamless, controlled key rotation with overlapping validity
COMMERCIAL_KEYRING: Dict[str, str] = {
    "k1": COMMERCIAL_LICENSE_VERIFICATION_PUBLIC_KEY_HEX,
}


def resolve_verification_key(
    key_id: str,
    keyring_override: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """
    Resolves the public verification key hex for a given key_id.
    Returns None if key_id is not in the trusted keyring.
    """
    keyring = keyring_override if keyring_override is not None else COMMERCIAL_KEYRING
    return keyring.get(key_id)

