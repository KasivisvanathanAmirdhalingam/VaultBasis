"""
VaultBasis MMP-1.5 Commercial Entitlement Domain Models
Strict separation between LicenseTier and LicenseState.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class LicenseTier(str, Enum):
    """Commercial product tiers."""
    TRIAL = "TRIAL"
    ESSENTIAL = "ESSENTIAL"
    PRACTICE = "PRACTICE"
    ENTERPRISE = "ENTERPRISE"


class LicenseState(str, Enum):
    """
    Deterministic evaluation states for local entitlement.
    Separated strictly from LicenseTier.
    """
    ACTIVE = "ACTIVE"
    GRACE = "GRACE"
    EXPIRED = "EXPIRED"
    NOT_YET_VALID = "NOT_YET_VALID"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    MALFORMED = "MALFORMED"
    UNSUPPORTED_VERSION = "UNSUPPORTED_VERSION"
    INSTALLATION_MISMATCH = "INSTALLATION_MISMATCH"


class LicensePayload(BaseModel):
    """
    Normative payload for an Ed25519-signed offline commercial license.
    """
    version: str = Field("v1.0", description="Schema version of the license token")
    license_id: str = Field(..., description="Unique license identifier, e.g. LIC-2026-XXXX")
    customer_id: str = Field(..., description="Customer / Firm account reference")
    issued_at: str = Field(..., description="ISO 8601 UTC timestamp of issuance")
    not_before: str = Field(..., description="ISO 8601 UTC timestamp before which license is invalid")
    expires_at: str = Field(..., description="ISO 8601 UTC timestamp when active tier expires")
    grace_until: str = Field(..., description="ISO 8601 UTC timestamp when grace period terminates")
    tier: LicenseTier = Field(..., description="Commercial plan tier")
    max_cases_per_installation: int = Field(..., gt=0, description="Strict local installation case limit")
    entitlements: List[str] = Field(default_factory=list, description="Explicit feature flags granted")
    installation_id: Optional[str] = Field(None, description="Optional bound installation hash")
    key_id: str = Field(..., description="Key identifier for the signing key")

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        if v != "v1.0":
            raise ValueError(f"Unsupported license version: {v}")
        return v


class LicenseEnvelope(BaseModel):
    """
    Signed envelope containing payload, Ed25519 signature, and key identifier.
    """
    payload: Dict[str, Any] = Field(..., description="Raw dictionary of LicensePayload")
    signature: str = Field(..., description="Hex-encoded Ed25519 signature")
    key_id: str = Field(..., description="Key identifier matching payload.key_id")


class LicenseEvaluationResult(BaseModel):
    """
    Deterministic result of evaluating an offline commercial license token.
    """
    state: LicenseState = Field(..., description="Evaluated entitlement state")
    is_active: bool = Field(..., description="True if state in (ACTIVE, GRACE)")
    tier: Optional[LicenseTier] = Field(None, description="Active tier if valid")
    license_id: Optional[str] = Field(None, description="License ID if parsable")
    customer_id: Optional[str] = Field(None, description="Customer ID if parsable")
    max_cases_per_installation: Optional[int] = Field(None, description="Enforceable case limit")
    entitlements: List[str] = Field(default_factory=list, description="Granted feature list")
    days_remaining: Optional[int] = Field(None, description="Days until expiry (negative if expired)")
    grace_days_remaining: Optional[int] = Field(None, description="Days until grace period ends")
    installation_bound: bool = Field(False, description="True if bound to specific installation_id")
    diagnostic_reason: str = Field(..., description="Human/audit readable explanation")
