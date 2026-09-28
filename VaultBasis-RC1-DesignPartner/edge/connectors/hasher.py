"""
VaultBasis Edge — Source File Streaming Hasher
Conforms to PRD §15.5 and §17.1 (Source Hashing)
"""

import hashlib
from typing import Tuple


def hash_source_bytes(data: bytes) -> Tuple[str, int]:
    """
    Computes lowercase hex SHA-256 digest and byte size of raw input bytes.
    Returns: (sha256_hex, byte_length)
    """
    sha256 = hashlib.sha256(data).hexdigest().lower()
    return sha256, len(data)
