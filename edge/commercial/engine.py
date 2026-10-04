"""
VaultBasis MMP-1.5 Commercial Entitlement Evaluation Engine
Evaluates offline Ed25519-signed license tokens with deterministic state transitions.
"""

import base64
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519

from edge.commercial.keys import COMMERCIAL_LICENSE_VERIFICATION_PUBLIC_KEY_HEX
from edge.commercial.models import (
    LicenseEnvelope,
    LicenseEvaluationResult,
    LicensePayload,
    LicenseState,
    LicenseTier,
)
from edge.receipts.canonicalizer import canonical_json_bytes, compute_sha256_digest


def _parse_iso8601(dt_str: str) -> Optional[datetime]:
    """Parses ISO 8601 UTC timestamp string safely."""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def evaluate_license_envelope(
    envelope_dict: Dict[str, Any],
    public_key_hex: Optional[str] = None,
    current_time: Optional[datetime] = None,
    current_installation_id: Optional[str] = None,
) -> LicenseEvaluationResult:
    """
    Evaluates a parsed LicenseEnvelope dictionary against the trusted verification public key.
    """
    pub_key_hex = public_key_hex or COMMERCIAL_LICENSE_VERIFICATION_PUBLIC_KEY_HEX
    eval_time = current_time or datetime.now(timezone.utc)
    if eval_time.tzinfo is None:
        eval_time = eval_time.replace(tzinfo=timezone.utc)

    # 1. Structural Validation of Envelope
    try:
        envelope = LicenseEnvelope.model_validate(envelope_dict)
    except Exception as e:
        return LicenseEvaluationResult(
            state=LicenseState.MALFORMED,
            is_active=False,
            diagnostic_reason=f"Envelope structure validation failed: {e}",
        )

    payload_dict = envelope.payload

    # 2. Version Check
    version = payload_dict.get("version")
    if version != "v1.0":
        return LicenseEvaluationResult(
            state=LicenseState.UNSUPPORTED_VERSION,
            is_active=False,
            diagnostic_reason=f"Unsupported license version '{version}', expected 'v1.0'",
        )

    # 3. Payload Schema Validation
    try:
        payload = LicensePayload.model_validate(payload_dict)
    except Exception as e:
        return LicenseEvaluationResult(
            state=LicenseState.MALFORMED,
            is_active=False,
            diagnostic_reason=f"License payload structure malformed: {e}",
        )

    # 4. Cryptographic Signature Verification
    try:
        pub_key_bytes = bytes.fromhex(pub_key_hex)
        if len(pub_key_bytes) != 32:
            raise ValueError("Public key must be 32 bytes")
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_key_bytes)
    except Exception as e:
        return LicenseEvaluationResult(
            state=LicenseState.INVALID_SIGNATURE,
            is_active=False,
            license_id=payload.license_id,
            customer_id=payload.customer_id,
            diagnostic_reason=f"Invalid verification public key configuration: {e}",
        )

    try:
        sig_bytes = bytes.fromhex(envelope.signature)
        if len(sig_bytes) != 64:
            raise ValueError("Ed25519 signature must be 64 bytes")
    except Exception as e:
        return LicenseEvaluationResult(
            state=LicenseState.INVALID_SIGNATURE,
            is_active=False,
            license_id=payload.license_id,
            customer_id=payload.customer_id,
            diagnostic_reason=f"Malformed signature hex: {e}",
        )

    # Compute canonical payload SHA-256 digest
    canonical_bytes = canonical_json_bytes(payload_dict)
    digest = compute_sha256_digest(canonical_bytes)

    try:
        public_key.verify(sig_bytes, digest)
    except InvalidSignature:
        return LicenseEvaluationResult(
            state=LicenseState.INVALID_SIGNATURE,
            is_active=False,
            license_id=payload.license_id,
            customer_id=payload.customer_id,
            diagnostic_reason="Cryptographic signature verification failed — payload or signature modified",
        )

    # 5. Installation ID Binding Verification (Optional Bound Field)
    installation_bound = payload.installation_id is not None
    if installation_bound:
        if not current_installation_id or current_installation_id != payload.installation_id:
            return LicenseEvaluationResult(
                state=LicenseState.INSTALLATION_MISMATCH,
                is_active=False,
                tier=payload.tier,
                license_id=payload.license_id,
                customer_id=payload.customer_id,
                max_cases_per_installation=payload.max_cases_per_installation,
                entitlements=payload.entitlements,
                installation_bound=True,
                diagnostic_reason=(
                    f"Installation binding mismatch: license bound to '{payload.installation_id}', "
                    f"current environment is '{current_installation_id}'"
                ),
            )

    # 6. Temporal Validity & Grace Window Evaluation
    dt_not_before = _parse_iso8601(payload.not_before)
    dt_expires_at = _parse_iso8601(payload.expires_at)
    dt_grace_until = _parse_iso8601(payload.grace_until)

    if not dt_not_before or not dt_expires_at or not dt_grace_until:
        return LicenseEvaluationResult(
            state=LicenseState.MALFORMED,
            is_active=False,
            license_id=payload.license_id,
            customer_id=payload.customer_id,
            diagnostic_reason="Invalid ISO 8601 timestamps in license payload",
        )

    if dt_expires_at < dt_not_before or dt_grace_until < dt_expires_at:
        return LicenseEvaluationResult(
            state=LicenseState.MALFORMED,
            is_active=False,
            license_id=payload.license_id,
            customer_id=payload.customer_id,
            diagnostic_reason="Invalid date chronology: not_before <= expires_at <= grace_until violated",
        )

    # Calculate remaining time
    seconds_to_expiry = (dt_expires_at - eval_time).total_seconds()
    seconds_to_grace = (dt_grace_until - eval_time).total_seconds()
    days_remaining = int(seconds_to_expiry // 86400)
    grace_days_remaining = int(seconds_to_grace // 86400)

    # Check temporal state
    if eval_time < dt_not_before:
        return LicenseEvaluationResult(
            state=LicenseState.NOT_YET_VALID,
            is_active=False,
            tier=payload.tier,
            license_id=payload.license_id,
            customer_id=payload.customer_id,
            max_cases_per_installation=payload.max_cases_per_installation,
            entitlements=payload.entitlements,
            days_remaining=days_remaining,
            grace_days_remaining=grace_days_remaining,
            installation_bound=installation_bound,
            diagnostic_reason=f"License not yet active (valid starting {payload.not_before})",
        )

    if eval_time <= dt_expires_at:
        return LicenseEvaluationResult(
            state=LicenseState.ACTIVE,
            is_active=True,
            tier=payload.tier,
            license_id=payload.license_id,
            customer_id=payload.customer_id,
            max_cases_per_installation=payload.max_cases_per_installation,
            entitlements=payload.entitlements,
            days_remaining=days_remaining,
            grace_days_remaining=grace_days_remaining,
            installation_bound=installation_bound,
            diagnostic_reason=f"License active under tier '{payload.tier.value}' ({days_remaining} days remaining)",
        )

    if eval_time <= dt_grace_until:
        return LicenseEvaluationResult(
            state=LicenseState.GRACE,
            is_active=True,
            tier=payload.tier,
            license_id=payload.license_id,
            customer_id=payload.customer_id,
            max_cases_per_installation=payload.max_cases_per_installation,
            entitlements=payload.entitlements,
            days_remaining=days_remaining,
            grace_days_remaining=grace_days_remaining,
            installation_bound=installation_bound,
            diagnostic_reason=(
                f"License in administrative grace period until {payload.grace_until} "
                f"({grace_days_remaining} grace days remaining)"
            ),
        )

    # Past grace termination
    return LicenseEvaluationResult(
        state=LicenseState.EXPIRED,
        is_active=False,
        tier=payload.tier,
        license_id=payload.license_id,
        customer_id=payload.customer_id,
        max_cases_per_installation=payload.max_cases_per_installation,
        entitlements=payload.entitlements,
        days_remaining=days_remaining,
        grace_days_remaining=grace_days_remaining,
        installation_bound=installation_bound,
        diagnostic_reason=f"License expired on {payload.expires_at} (grace ended {payload.grace_until})",
    )


def evaluate_license_token(
    token_str: str,
    public_key_hex: Optional[str] = None,
    current_time: Optional[datetime] = None,
    current_installation_id: Optional[str] = None,
) -> LicenseEvaluationResult:
    """
    Decodes and evaluates a raw license token string.
    Accepts Base64-encoded envelope, URL-safe Base64 envelope, or raw JSON envelope string.
    """
    if not token_str or not token_str.strip():
        return LicenseEvaluationResult(
            state=LicenseState.MALFORMED,
            is_active=False,
            diagnostic_reason="Empty or whitespace license token",
        )

    cleaned = token_str.strip()
    raw_json: Optional[str] = None

    # Try 1: Direct JSON parsing
    if cleaned.startswith("{") and cleaned.endswith("}"):
        raw_json = cleaned
    else:
        # Try 2: Base64 / URL-safe Base64 decode
        try:
            # Add padding if needed
            padded = cleaned + "=" * ((4 - len(cleaned) % 4) % 4)
            # Try urlsafe first then standard
            try:
                decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
            except Exception:
                decoded = base64.b64decode(padded.encode("ascii")).decode("utf-8")
            if decoded.strip().startswith("{"):
                raw_json = decoded
        except Exception:
            pass

    if not raw_json:
        return LicenseEvaluationResult(
            state=LicenseState.MALFORMED,
            is_active=False,
            diagnostic_reason="License token is neither valid JSON nor valid Base64 JSON payload",
        )

    try:
        envelope_dict = json.loads(raw_json)
    except Exception as e:
        return LicenseEvaluationResult(
            state=LicenseState.MALFORMED,
            is_active=False,
            diagnostic_reason=f"Failed to parse license JSON: {e}",
        )

    if not isinstance(envelope_dict, dict):
        return LicenseEvaluationResult(
            state=LicenseState.MALFORMED,
            is_active=False,
            diagnostic_reason="License envelope must be a JSON object",
        )

    return evaluate_license_envelope(
        envelope_dict=envelope_dict,
        public_key_hex=public_key_hex,
        current_time=current_time,
        current_installation_id=current_installation_id,
    )
