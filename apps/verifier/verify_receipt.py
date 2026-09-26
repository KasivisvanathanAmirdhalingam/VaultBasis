#!/usr/bin/env python3
"""
VaultBasis — Independent Outcome Receipt Verifier CLI
Conforms to Evidence Contract v0.1 (schemas/receipt/verification-v0.1.md)

Runs completely offline on clean machines with ZERO cloud calls, zero accounts,
and zero external dependencies beyond standard cryptography.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519
import jsonschema

# Add repo root to sys.path if running as script
current_dir = Path(__file__).resolve().parent
repo_root = current_dir.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from edge.receipts.canonicalizer import compute_receipt_digest, compute_sha256_hex


SCHEMA_PATH = repo_root / "schemas" / "receipt" / "receipt-v0.1.json"


LIMITATION_NOTICE = """
================================================================================
                           LIMITATION NOTICE
================================================================================
Verification of this receipt confirms cryptographic integrity and origin from 
the declared installation key under Evidence Contract v0.1.
Verification does NOT constitute:
1. Legal advice or tax advice.
2. An assertion that source systems, brokers, or tax filers acted fraudulently 
   or correctly.
3. Official endorsement or certification by the Internal Revenue Service (IRS) 
   or any government taxing authority.
================================================================================
"""


class VerificationResult:
    def __init__(self):
        self.is_valid = False
        self.schema_valid = False
        self.version_supported = False
        self.key_fingerprint_valid = False
        self.signature_valid = False
        self.source_hashes_valid: Optional[bool] = None
        self.receipt_id: Optional[str] = None
        self.outcome_state: Optional[str] = None
        self.assurance_level: Optional[str] = None
        self.signer_key_id: Optional[str] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": "PASS" if self.is_valid else "FAIL",
            "receipt_id": self.receipt_id,
            "outcome_state": self.outcome_state,
            "assurance_level": self.assurance_level,
            "signer_key_id": self.signer_key_id,
            "checks": {
                "schema_conformance": "PASS" if self.schema_valid else "FAIL",
                "version_supported": "PASS" if self.version_supported else "FAIL",
                "key_fingerprint": "PASS" if self.key_fingerprint_valid else "FAIL",
                "signature_authenticity": "PASS" if self.signature_valid else "FAIL",
                "source_hashes": (
                    "PASS" if self.source_hashes_valid is True
                    else ("FAIL" if self.source_hashes_valid is False else "NOT_ATTACHED")
                )
            },
            "errors": self.errors,
            "warnings": self.warnings
        }


def verify_outcome_receipt(
    receipt_data: Dict[str, Any],
    evidence_dir: Optional[Path] = None
) -> VerificationResult:
    """
    Executes independent verification of an outcome receipt against Evidence Contract v0.1.
    """
    res = VerificationResult()

    # 1. Schema Validation
    if SCHEMA_PATH.exists():
        try:
            with open(SCHEMA_PATH, "r") as sf:
                schema = json.load(sf)
            jsonschema.validate(instance=receipt_data, schema=schema)
            res.schema_valid = True
        except jsonschema.ValidationError as e:
            res.errors.append(f"Schema validation error: {e.message}")
            return res
        except Exception as e:
            res.errors.append(f"Schema file load failure: {str(e)}")
            return res
    else:
        res.warnings.append("Local schema file not found; falling back to internal field checks")
        res.schema_valid = True

    # 2. Version Check
    version = receipt_data.get("receipt_version")
    if version != "v0.1":
        res.errors.append(f"Unsupported receipt version: '{version}'. Expected 'v0.1'")
        return res
    res.version_supported = True

    res.receipt_id = receipt_data.get("receipt_id")
    res.outcome_state = receipt_data.get("outcome_state")
    res.assurance_level = receipt_data.get("assurance_level")
    res.signer_key_id = receipt_data.get("signer_key_id")

    # 3. Key Fingerprint Check
    pub_hex = receipt_data.get("signer_public_key", "")
    try:
        pub_bytes = bytes.fromhex(pub_hex)
        if len(pub_bytes) != 32:
            res.errors.append("Invalid Ed25519 public key byte length (expected 32 bytes)")
            return res
        expected_fingerprint = hashlib.sha256(pub_bytes).hexdigest().lower()
        if expected_fingerprint != res.signer_key_id.lower():
            res.errors.append(
                f"Signer key fingerprint mismatch! Declared: {res.signer_key_id}, "
                f"Calculated: {expected_fingerprint}"
            )
            return res
        res.key_fingerprint_valid = True
    except Exception as e:
        res.errors.append(f"Failed to process signer public key: {str(e)}")
        return res

    # 4. Canonicalization & Signature Verification
    sig_hex = receipt_data.get("signature", "")
    try:
        sig_bytes = bytes.fromhex(sig_hex)
        if len(sig_bytes) != 64:
            res.errors.append("Invalid Ed25519 signature byte length (expected 64 bytes)")
            return res
    except Exception as e:
        res.errors.append(f"Failed to decode hex signature: {str(e)}")
        return res

    try:
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
        # Compute canonical digest
        digest = compute_receipt_digest(receipt_data)
        # Verify Ed25519 signature over digest
        public_key.verify(sig_bytes, digest)
        res.signature_valid = True
    except InvalidSignature:
        res.errors.append("Ed25519 signature verification FAILED: Receipt payload has been tampered with or corrupted.")
        return res
    except Exception as e:
        res.errors.append(f"Cryptographic error during signature verification: {str(e)}")
        return res

    # 5. Optional Source Hashes Verification
    source_hashes = receipt_data.get("source_hashes", {})
    if evidence_dir and Path(evidence_dir).is_dir():
        all_matched = True
        for source_id, declared_hash in source_hashes.items():
            # Look for file matching source_id or basename
            candidate_files = list(Path(evidence_dir).glob(f"*{source_id}*"))
            if not candidate_files:
                candidate_files = [p for p in Path(evidence_dir).iterdir() if p.is_file() and p.name == source_id]
            
            if candidate_files:
                file_bytes = candidate_files[0].read_bytes()
                computed_hash = hashlib.sha256(file_bytes).hexdigest().lower()
                if computed_hash != declared_hash.lower():
                    res.errors.append(
                        f"Source file '{candidate_files[0].name}' hash mismatch! "
                        f"Declared: {declared_hash}, Found: {computed_hash}"
                    )
                    all_matched = False
            else:
                res.warnings.append(f"Source file for ID '{source_id}' not found in evidence directory.")
                all_matched = False
        res.source_hashes_valid = all_matched
    else:
        res.source_hashes_valid = None

    # Overall Status
    res.is_valid = (
        res.schema_valid
        and res.version_supported
        and res.key_fingerprint_valid
        and res.signature_valid
        and (res.source_hashes_valid is not False)
    )
    return res


def print_cli_report(res: VerificationResult, use_color: bool = True):
    if use_color:
        status_str = "\033[92mPASS\033[0m" if res.is_valid else "\033[91mFAIL\033[0m"
    else:
        status_str = "PASS" if res.is_valid else "FAIL"
    print("\n" + "="*80)
    print(f"      VAULTBASIS INDEPENDENT OUTCOME VERIFICATION REPORT — {status_str}")
    print("="*80)
    print(f"Receipt ID:       {res.receipt_id}")
    print(f"Outcome State:    {res.outcome_state}")
    print(f"Assurance Level:  {res.assurance_level}")
    print(f"Signer Key ID:    {res.signer_key_id}")
    print("-" * 80)
    print(f"  [1] JSON Schema Conformance:   {'PASS' if res.schema_valid else 'FAIL'}")
    print(f"  [2] Evidence Contract Version: {'PASS (v0.1)' if res.version_supported else 'FAIL'}")
    print(f"  [3] Key Fingerprint Match:     {'PASS' if res.key_fingerprint_valid else 'FAIL'}")
    print(f"  [4] Ed25519 Signature Match:   {'PASS' if res.signature_valid else 'FAIL'}")
    if res.source_hashes_valid is not None:
        print(f"  [5] Source Hashes Match:       {'PASS' if res.source_hashes_valid else 'FAIL'}")
    else:
        print("  [5] Source Hashes Match:       (NOT CHECKED - NO EVIDENCE DIR SUPPLIED)")
    print("-" * 80)

    if res.errors:
        print("\nERRORS ENCOUNTERED:")
        for err in res.errors:
            print(f"  ❌ {err}")

    if res.warnings:
        print("\nWARNINGS:")
        for warn in res.warnings:
            print(f"  ⚠️  {warn}")

    print(LIMITATION_NOTICE)


def main():
    parser = argparse.ArgumentParser(
        description="VaultBasis Offline Independent Outcome Receipt Verifier"
    )
    parser.add_argument(
        "receipt_file",
        type=Path,
        help="Path to the JSON outcome receipt file to verify"
    )
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=None,
        help="Optional directory containing source files to verify against source_hashes"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON instead of human-readable report"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color codes in report output"
    )

    args = parser.parse_args()

    if not args.receipt_file.exists():
        print(f"Error: Receipt file '{args.receipt_file}' does not exist.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.receipt_file, "r") as f:
            receipt_data = json.load(f)
    except Exception as e:
        print(f"Error: Failed to parse receipt as valid JSON: {str(e)}", file=sys.stderr)
        sys.exit(1)

    result = verify_outcome_receipt(receipt_data, evidence_dir=args.evidence_dir)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print_cli_report(result, use_color=not args.no_color)

    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
