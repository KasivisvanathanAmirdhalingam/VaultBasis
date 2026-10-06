#!/usr/bin/env python3
"""
VaultBasis Design Partner License Provisioning Tool
Generates authentic, cryptographically signed 1-year complimentary Practitioner licenses
bound to specific CPA/EA installation fingerprints.

Conforms to:
- MMP15-WIN-INSTALL-LICENSE-001: Bound 1-year annual license with monotonic revision
- MMP15-PRODUCTIZATION-001: Design Partner tier with promotional metadata
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.asymmetric import ed25519

# Ensure repository root is on PYTHONPATH
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from edge.receipts.canonicalizer import canonical_json_bytes, compute_sha256_digest


def issue_design_partner_license(
    customer_name: str,
    installation_id: str,
    private_key_path: Optional[str] = None,
    output_file: Optional[str] = None,
    max_cases: int = 15,
    key_id: str = "prod-commercial-2026-v1",
) -> str:
    """
    Issues a cryptographically signed 1-year Design Partner license bound to the practitioner's machine.
    """
    # 1. Resolve Ed25519 Private Key
    priv_path = Path(private_key_path) if private_key_path else REPO_ROOT / "keys" / "commercial_private_v1.pem"
    
    if not priv_path.is_file():
        # Look for local keyfile or create a temporary air-gap key for development
        dev_key_path = REPO_ROOT / "keys" / "dev_commercial_private.key"
        if dev_key_path.is_file():
            priv_path = dev_key_path
        else:
            raise FileNotFoundError(
                f"Commercial signing private key not found at {priv_path}. "
                f"Design Partner licenses must be issued from an authorized signing environment."
            )

    key_bytes = priv_path.read_bytes()
    if b"BEGIN PRIVATE KEY" in key_bytes:
        from cryptography.hazmat.primitives import serialization
        private_key = serialization.load_pem_private_key(key_bytes, password=None)
    else:
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)

    # 2. Chronological Boundaries: 1-Year (365 Days) Term
    now = datetime.now(timezone.utc)
    not_before = now
    expires_at = now + timedelta(days=365)
    grace_until = expires_at

    inst_hash = installation_id.strip().upper()
    license_id = f"LIC-DP-{now.strftime('%Y%m%d')}-{inst_hash[:8]}"

    # 3. Canonical Signed License Payload
    payload = {
        "version": "v1.0",
        "license_id": license_id,
        "customer_id": customer_name.strip(),
        "tier": "PRACTITIONER",
        "max_cases_per_installation": max_cases,
        "revision": 1,
        "entitlements": ["reconciliation", "offline_export", "reviewer_workflow"],
        "installation_id": inst_hash,
        "key_id": key_id,
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "not_before": not_before.isoformat().replace("+00:00", "Z"),
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
        "grace_until": grace_until.isoformat().replace("+00:00", "Z"),
        "promotional_program": "DESIGN_PARTNER_2026",
        "commercial_price_cents": 0,
    }

    # 4. Canonical RFC 8785 Digest & Signature
    canonical_bytes = canonical_json_bytes(payload)
    digest = compute_sha256_digest(canonical_bytes)
    signature_bytes = private_key.sign(digest)
    signature_hex = signature_bytes.hex()

    envelope = {
        "payload": payload,
        "signature": signature_hex,
        "key_id": key_id,
    }

    token_str = base64.b64encode(json.dumps(envelope).encode("utf-8")).decode("utf-8")

    if output_file:
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(token_str, encoding="utf-8")
        print(f"✓ Saved 1-Year Design Partner License to: {out_path}")

    return token_str


def main():
    parser = argparse.ArgumentParser(description="Issue VaultBasis 1-Year Design Partner License")
    parser.add_argument("--customer", required=True, help="Practitioner or Firm Name (e.g. 'Redwood Tax Advisory LLC')")
    parser.add_argument("--installation-id", required=True, help="Target Installation ID (e.g. 'INST-A1B2-C3D4')")
    parser.add_argument("--cases", type=int, default=15, help="Case capacity (default: 15)")
    parser.add_argument("--key", help="Path to Ed25519 private key file")
    parser.add_argument("--out", help="Output .license filepath")

    args = parser.parse_args()

    token = issue_design_partner_license(
        customer_name=args.customer,
        installation_id=args.installation_id,
        private_key_path=args.key,
        output_file=args.out,
        max_cases=args.cases,
    )

    print("\n--- VAULTBASIS 1-YEAR DESIGN PARTNER LICENSE TOKEN ---")
    print(token)
    print("------------------------------------------------------\n")


if __name__ == "__main__":
    main()
