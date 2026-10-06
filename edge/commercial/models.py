"""
VaultBasis MMP-1.5 Commercial Entitlement Domain Models
Strict separation between LicenseTier and LicenseState, normative UTC chronology validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field, field_validator, model_validator


class LicenseTier(str, Enum):
    """Commercial product tiers."""
    TRIAL = "TRIAL"
    EVALUATION = "EVALUATION"
    SOLO = "SOLO"
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


class CommercialEntitlement(str, Enum):
    """Known capability identifiers granted by commercial licenses."""
    RECONCILIATION = "reconciliation"
    OFFLINE_EXPORT = "offline_export"
    REVIEWER_WORKFLOW = "reviewer_workflow"
    MULTI_OFFICE = "multi_office"


def parse_strict_utc_iso8601(dt_str: str) -> datetime:
    """
    Parses ISO 8601 timestamp string and ensures it has an explicit UTC timezone.
    Rejects naive timestamps without timezone information.
    """
    if not isinstance(dt_str, str):
        raise ValueError(f"Timestamp must be a string, got {type(dt_str).__name__}")
    
    clean_str = dt_str.strip()
    if not (clean_str.endswith("Z") or clean_str.endswith("+00:00") or clean_str.endswith("-00:00")):
        raise ValueError(f"Timestamp must explicitly indicate UTC ('Z' or '+00:00'), got: {dt_str}")
    
    try:
        dt = datetime.fromisoformat(clean_str.replace("Z", "+00:00"))
    except Exception as e:
        raise ValueError(f"Invalid ISO 8601 timestamp format '{dt_str}': {e}")
    
    if dt.tzinfo is None:
        raise ValueError(f"Naive timestamps are prohibited: {dt_str}")
    return dt


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
    revision: int = Field(1, ge=1, description="Monotonic license revision number")
    entitlements: List[str] = Field(default_factory=list, description="Explicit feature flags granted")
    installation_id: Optional[str] = Field(None, description="Optional bound installation hash")
    key_id: str = Field(..., description="Key identifier for the signing key")

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        if v != "v1.0":
            raise ValueError(f"Unsupported license version: {v}")
        return v

    @field_validator("issued_at", "not_before", "expires_at", "grace_until")
    @classmethod
    def validate_timestamp_format(cls, v: str) -> str:
        parse_strict_utc_iso8601(v)
        return v

    @model_validator(mode="after")
    def validate_chronology(self) -> "LicensePayload":
        dt_issued = parse_strict_utc_iso8601(self.issued_at)
        dt_not_before = parse_strict_utc_iso8601(self.not_before)
        dt_expires = parse_strict_utc_iso8601(self.expires_at)
        dt_grace = parse_strict_utc_iso8601(self.grace_until)

        if dt_issued > dt_expires:
            raise ValueError(f"Chronology violation: issued_at ({self.issued_at}) > expires_at ({self.expires_at})")
        if dt_not_before > dt_expires:
            raise ValueError(f"Chronology violation: not_before ({self.not_before}) > expires_at ({self.expires_at})")
        if dt_expires > dt_grace:
            raise ValueError(f"Chronology violation: expires_at ({self.expires_at}) > grace_until ({self.grace_until})")
        return self


class LicenseEnvelope(BaseModel):
    """
    Signed envelope containing payload, Ed25519 signature, and key identifier.
    """
    payload: Dict[str, Any] = Field(..., description="Raw dictionary of LicensePayload")
    signature: str = Field(..., description="Hex-encoded Ed25519 signature")
    key_id: str = Field(..., description="Key identifier matching payload.key_id")

    @model_validator(mode="after")
    def validate_key_id_synchronization(self) -> "LicenseEnvelope":
        payload_key_id = self.payload.get("key_id")
        if payload_key_id is not None and payload_key_id != self.key_id:
            raise ValueError(
                f"Key ID mismatch: envelope has key_id '{self.key_id}', "
                f"but payload has key_id '{payload_key_id}'"
            )
        return self


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
    revision: Optional[int] = Field(None, description="Monotonic license revision number")
    entitlements: List[str] = Field(default_factory=list, description="Granted feature list")
    days_remaining: Optional[int] = Field(None, description="Days until expiry (presentation helper only)")
    grace_days_remaining: Optional[int] = Field(None, description="Days until grace period ends (presentation helper only)")
    installation_bound: bool = Field(False, description="True if bound to specific installation_id")
    diagnostic_reason: str = Field(..., description="Human/audit readable explanation")

    def has_entitlement(self, capability: str) -> bool:
        """
        Determines whether a specific capability is granted.
        INVARIANT: Unknown capabilities or inactive license NEVER grant access.
        """
        if not self.is_active:
            return False
        return capability in self.entitlements

