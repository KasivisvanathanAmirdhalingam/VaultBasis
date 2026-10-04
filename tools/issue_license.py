#!/usr/bin/env python3
"""
VaultBasis MMP-1.5 Commercial License Generator (Internal Operations Tool)
Conforms to MMP15-ADM-001.

SECURITY NOTE:
This tool is used by TecTixBase Commercial Operations to issue signed license tokens.
The Commercial License Signing Key (private key) MUST be kept isolated in air-gapped
or secure operations environments and NEVER bundled into client distributions.
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from cryptography.hazmat.primitives.asymmetric import ed25519

from edge.receipts.canonicalizer import canonical_json_bytes, compute_sha256_digest


def generate_commercial_keypair() -> Tuple[str, str]:
    """
    Generates a fresh Ed25519 keypair for commercial license signing.
    Returns (private_key_hex, public_key_hex).
    """
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()
    priv_bytes = priv.private_bytes_raw()
    pub_bytes = pub.public_bytes_raw()
    return priv_bytes.hex(), pub_bytes.hex()


def sign_license_payload(
    payload_dict: Dict[str, Any],
    private_key_hex: str,
) -> Dict[str, Any]:
    """
    Signs a license payload using the private key and returns the LicenseEnvelope dictionary.
    """
    priv_bytes = bytes.fromhex(private_key_hex)
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)

    # Compute canonical SHA-256 digest of payload
    canonical_bytes = canonical_json_bytes(payload_dict)
    digest = compute_sha256_digest(canonical_bytes)

    # Sign digest with Ed25519
    signature_bytes = private_key.sign(digest)
    signature_hex = signature_bytes.hex()

    envelope = {
        "payload": payload_dict,
        "signature": signature_hex,
        "key_id": payload_dict.get("key_id", "k1"),
    }
    return envelope


def build_license_payload(
    customer_id: str,
    tier: str,
    max_cases: int,
    valid_days: int = 365,
    grace_days: int = 30,
    license_id: Optional[str] = None,
    installation_id: Optional[str] = None,
    entitlements: Optional[List[str]] = None,
    key_id: str = "k1",
    not_before_dt: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Constructs a normalized license payload dictionary.
    """
    now = not_before_dt or datetime.now(timezone.utc)
    not_before = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    expires_at = (now + timedelta(days=valid_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    grace_until = (now + timedelta(days=valid_days + grace_days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    lic_id = license_id or f"LIC-{now.strftime('%Y')}-{os.urandom(4).hex().upper()}"
    default_entitlements = ["reconciliation", "offline_export", "reviewer_workflow"]
    if tier == "ENTERPRISE":
        default_entitlements.append("multi_office")

    payload = {
        "version": "v1.0",
        "license_id": lic_id,
        "customer_id": customer_id,
        "issued_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "not_before": not_before,
        "expires_at": expires_at,
        "grace_until": grace_until,
        "tier": tier,
        "max_cases_per_installation": max_cases,
        "entitlements": entitlements or default_entitlements,
        "installation_id": installation_id,
        "key_id": key_id,
    }
    return payload


def encode_token_base64(envelope_dict: Dict[str, Any]) -> str:
    """Encodes a LicenseEnvelope dictionary to URL-safe Base64 token string."""
    json_bytes = json.dumps(envelope_dict, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(json_bytes).decode("ascii").rstrip("=")


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue cryptographically signed VaultBasis commercial license tokens.")
    parser.add_argument("--customer-id", help="Customer account identifier (e.g. CUST-ACME-CPA)")
    parser.add_argument("--tier", choices=["TRIAL", "ESSENTIAL", "PRACTICE", "ENTERPRISE"], default="PRACTICE")
    parser.add_argument("--max-cases", type=int, default=100, help="Maximum cases per installation")
    parser.add_argument("--valid-days", type=int, default=365, help="Validity period in days")
    parser.add_argument("--grace-days", type=int, default=30, help="Grace period in days")
    parser.add_argument("--installation-id", help="Optional bound installation hash")
    parser.add_argument("--key-id", default="k1", help="Key identifier")
    parser.add_argument("--signing-key-hex", help="Private key in hex (defaults to env COMMERCIAL_LICENSE_SIGNING_KEY_HEX)")
    parser.add_argument("--generate-keypair", action="store_true", help="Generate fresh Ed25519 signing keypair and exit")
    parser.add_argument("--format", choices=["base64", "json"], default="base64", help="Output token format")

    args = parser.parse_args()

    if args.generate_keypair:
        priv_hex, pub_hex = generate_commercial_keypair()
        print("=== Fresh Commercial Signing Keypair ===")
        print(f"COMMERCIAL_LICENSE_SIGNING_KEY_HEX={priv_hex}")
        print(f"COMMERCIAL_LICENSE_VERIFICATION_PUBLIC_KEY_HEX={pub_hex}")
        print("========================================")
        return 0

    if not args.customer_id:
        print("Error: --customer-id is required to issue a license", file=sys.stderr)
        return 1

    priv_key_hex = args.signing_key_hex or os.environ.get("COMMERCIAL_LICENSE_SIGNING_KEY_HEX")
    if not priv_key_hex:
        print("Error: Signing key must be provided via --signing-key-hex or COMMERCIAL_LICENSE_SIGNING_KEY_HEX env var", file=sys.stderr)
        return 1

    payload = build_license_payload(
        customer_id=args.customer_id,
        tier=args.tier,
        max_cases=args.max_cases,
        valid_days=args.valid_days,
        grace_days=args.grace_days,
        installation_id=args.installation_id,
        key_id=args.key_id,
    )

    envelope = sign_license_payload(payload, priv_key_hex)

    if args.format == "json":
        print(json.dumps(envelope, indent=2))
    else:
        token = encode_token_base64(envelope)
        print(token)

    return 0


if __name__ == "__main__":
    sys.exit(main())
