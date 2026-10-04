"""
VaultBasis MMP-1.5 Firm & Workspace Identity Domain Model
Conforms to docs/mmp15_task_ledger.md (MMP15-ORG-001) and PRD §62.1.

Architectural Invariants:
1. Professional Provenance: Binds case workpapers to organization and practitioner identity.
2. Regulated Identifier Isolation: PTIN and EFIN are strictly local and NEVER exported in portable receipts.
3. Deterministic Redaction: Public projections drop regulated IDs; diagnostic projections mask them.
4. Offline / Air-Gap: Complete local persistence with zero network egress.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from edge.storage.sqlite_store import SQLiteStore


# PTIN: IRS Preparer Tax Identification Number (P followed by 8 digits)
_PTIN_REGEX = re.compile(r"^P\d{8}$")
# EFIN: IRS Electronic Filing Identification Number (6 digits)
_EFIN_REGEX = re.compile(r"^\d{6}$")


class FirmIdentity(BaseModel):
    """
    Firm, workspace, practitioner, and regulated identifier profile.
    """
    organization_id: str = Field(..., min_length=2, max_length=64, description="Firm account identifier, e.g. ORG-ACME-TAX")
    firm_name: str = Field(..., min_length=2, max_length=128, description="Legal or trade name of the accounting practice")
    office_id: Optional[str] = Field(None, max_length=64, description="Optional office or branch location identifier")
    workspace_id: str = Field(default="WS-DEFAULT", min_length=2, max_length=64, description="Active workspace identifier")
    preparer_id: str = Field(..., min_length=2, max_length=64, description="Practitioner identifier, e.g. PREP-JSMITH")
    display_name: str = Field(..., min_length=2, max_length=128, description="Practitioner display name, e.g. Jane Smith, CPA")
    ptin: Optional[str] = Field(None, description="IRS Preparer Tax Identification Number (PXXXXXXXX)")
    efin: Optional[str] = Field(None, description="IRS Electronic Filing Identification Number (XXXXXX)")
    created_at: Optional[str] = Field(None, description="ISO 8601 UTC creation timestamp")
    updated_at: Optional[str] = Field(None, description="ISO 8601 UTC update timestamp")

    @field_validator("ptin")
    @classmethod
    def validate_ptin(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        cleaned = v.strip().upper()
        if not _PTIN_REGEX.match(cleaned):
            raise ValueError(f"Invalid PTIN format '{v}'. Expected 'P' followed by 8 digits (e.g. P01234567)")
        return cleaned

    @field_validator("efin")
    @classmethod
    def validate_efin(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        cleaned = v.strip()
        if not _EFIN_REGEX.match(cleaned):
            raise ValueError(f"Invalid EFIN format '{v}'. Expected exactly 6 digits (e.g. 123456)")
        return cleaned

    @model_validator(mode="after")
    def set_timestamps(self) -> "FirmIdentity":
        now_utc = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now_utc
        if not self.updated_at:
            self.updated_at = now_utc
        return self

    def to_public_metadata(self) -> Dict[str, Any]:
        """
        Public / portable projection.
        STRICT SECURITY INVARIANT: Regulated identifiers (PTIN, EFIN) are 100% stripped.
        """
        return {
            "organization_id": self.organization_id,
            "firm_name": self.firm_name,
            "office_id": self.office_id,
            "workspace_id": self.workspace_id,
            "preparer_id": self.preparer_id,
            "display_name": self.display_name,
            "has_ptin_configured": bool(self.ptin),
            "has_efin_configured": bool(self.efin),
            "updated_at": self.updated_at,
        }

    def to_redacted_diagnostic(self) -> Dict[str, Any]:
        """
        Diagnostic / support bundle projection.
        Regulated identifiers are masked to prevent PII/tax credentials leakage.
        """
        masked_ptin = f"P*****{self.ptin[-3:]}" if self.ptin else None
        masked_efin = f"***{self.efin[-3:]}" if self.efin else None
        return {
            "organization_id": self.organization_id,
            "firm_name": self.firm_name,
            "office_id": self.office_id,
            "workspace_id": self.workspace_id,
            "preparer_id": self.preparer_id,
            "display_name": self.display_name,
            "ptin_masked": masked_ptin,
            "efin_masked": masked_efin,
            "updated_at": self.updated_at,
        }

    def to_internal_dict(self) -> Dict[str, Any]:
        """Full internal local storage dictionary."""
        return self.model_dump()


class FirmIdentityService:
    """
    Manages local firm and workspace identity profiles via SQLite persistence.
    """

    def __init__(self, store: SQLiteStore):
        self.store = store

    def get_identity(self) -> Optional[FirmIdentity]:
        """Retrieves and parses current firm identity from local persistence."""
        raw = self.store.get_firm_identity()
        if not raw:
            return None
        return FirmIdentity.model_validate(raw)

    def save_identity(self, identity: FirmIdentity) -> FirmIdentity:
        """Saves firm identity to local persistence."""
        now_utc = datetime.now(timezone.utc).isoformat()
        identity.updated_at = now_utc
        self.store.save_firm_identity(identity.to_internal_dict())
        return identity

    def get_public_identity(self) -> Optional[Dict[str, Any]]:
        """Returns public metadata safe for UI presentation and export headers."""
        ident = self.get_identity()
        if not ident:
            return None
        return ident.to_public_metadata()

    def get_diagnostic_identity(self) -> Optional[Dict[str, Any]]:
        """Returns redacted identity safe for support diagnostics."""
        ident = self.get_identity()
        if not ident:
            return None
        return ident.to_redacted_diagnostic()

    def clear_identity(self):
        """Clears stored firm identity profile."""
        self.store.delete_firm_identity()
