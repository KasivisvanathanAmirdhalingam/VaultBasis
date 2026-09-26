"""
VaultBasis — Canonical Transaction Model
Conforms to PRD §15.1 (Exact Decimal Arithmetic) and §17.1 (Canonical Data Model)
"""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CanonicalTransaction(BaseModel):
    """
    Standardized, normalized transaction representation across all input adapters.
    Strictly forbids binary floating point values. All monetary values are Decimals or strings.
    """
    transaction_id: str = Field(..., min_length=1, description="Unique deterministic transaction identifier")
    source_id: str = Field(..., min_length=1, description="ID of the ingested source document")
    source_file_hash: str = Field(..., description="SHA-256 hash of the parent source document")
    source_row_reference: str = Field(..., min_length=1, description="Source file row/line identifier (e.g. 'Line:5')")
    
    transaction_type: str = Field(..., min_length=1, description="Classification: SALE, DISPOSITION, TRANSFER, ACQUISITION")
    asset: str = Field(..., min_length=1, description="Normalized asset symbol (e.g. 'BTC', 'ETH')")
    quantity: Decimal = Field(..., description="Exact asset quantity")
    
    proceeds: Optional[Decimal] = Field(None, description="Exact gross proceeds in USD")
    cost_basis: Optional[Decimal] = Field(None, description="Exact cost or other basis in USD")
    gain_loss: Optional[Decimal] = Field(None, description="Exact realized gain or loss in USD")
    
    acquisition_date: Optional[str] = Field(None, description="Normalized ISO date (YYYY-MM-DD) or None if unknown")
    disposition_date: Optional[str] = Field(None, description="Normalized ISO date (YYYY-MM-DD)")
    
    basis_reported_to_irs: Optional[str] = Field(
        "UNSPECIFIED",
        description="Form 1099-DA Box 2 indicator: 'YES', 'NO', or 'UNSPECIFIED'"
    )
    
    is_unresolved: bool = Field(False, description="Flag indicating if a required fact could not be resolved")
    unresolved_reason: Optional[str] = Field(None, description="Reason code if unresolved (e.g. BASIS_UNAVAILABLE)")

    @field_validator("quantity", "proceeds", "cost_basis", "gain_loss", mode="before")
    @classmethod
    def parse_strict_decimal(cls, val):
        if val is None or val == "":
            return None
        if isinstance(val, (int, str)):
            # Strip dollar signs, commas, and whitespace
            clean = str(val).replace("$", "").replace(",", "").strip()
            return Decimal(clean)
        if isinstance(val, Decimal):
            return val
        raise ValueError(f"Floating-point values strictly prohibited for financial fields: got {type(val)}")

    def to_summary_dict(self):
        """Converts to dictionary with stringified Decimals for JSON serialization."""
        return {
            "transaction_id": self.transaction_id,
            "source_id": self.source_id,
            "source_row_reference": self.source_row_reference,
            "transaction_type": self.transaction_type,
            "asset": self.asset,
            "quantity": str(self.quantity),
            "proceeds": str(self.proceeds) if self.proceeds is not None else None,
            "cost_basis": str(self.cost_basis) if self.cost_basis is not None else None,
            "gain_loss": str(self.gain_loss) if self.gain_loss is not None else None,
            "acquisition_date": self.acquisition_date,
            "disposition_date": self.disposition_date,
            "basis_reported_to_irs": self.basis_reported_to_irs,
            "is_unresolved": self.is_unresolved,
            "unresolved_reason": self.unresolved_reason
        }
