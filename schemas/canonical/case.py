"""
VaultBasis — Canonical Case Model
Conforms to PRD §17.2 (Customer Case Schema)
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from schemas.canonical.transaction import CanonicalTransaction


class SourceDocumentMetadata(BaseModel):
    """Metadata tracking ingested source documents and their cryptographic integrity."""
    source_id: str = Field(..., description="Unique source document identifier")
    filename: str = Field(..., description="Original filename uploaded by user")
    sha256_hash: str = Field(..., pattern=r"^[a-fA-F0-9]{64}$", description="SHA-256 hash of the raw uploaded file")
    byte_size: int = Field(..., description="Size of file in bytes")
    schema_id: str = Field(..., description="Adapter schema identifier (e.g. KOINLY_CAPITAL_GAINS_CSV_V1)")
    row_count: int = Field(0, description="Number of parsed transaction rows")
    ingested_at: str = Field(..., description="ISO 8601 UTC timestamp")


class CanonicalCase(BaseModel):
    """
    Local customer case holding all ingested sources, parsed canonical transactions,
    reconciliation outcomes, and signed receipt reference.
    """
    case_id: str = Field(..., description="Unique case identifier (e.g. CASE-2026-US-001)")
    client_reference: Optional[str] = Field("Sample Client", description="Local practitioner client or engagement reference")
    tax_year: int = Field(2025, description="Target tax year for review")
    jurisdiction: str = Field("US", description="Regulatory jurisdiction")
    case_status: str = Field(
        "CREATED",
        description="Case lifecycle status: CREATED, SOURCES_INGESTED, RECONCILED, RECEIPT_ISSUED"
    )
    
    sources: Dict[str, SourceDocumentMetadata] = Field(
        default_factory=dict,
        description="Map of source_id to SourceDocumentMetadata"
    )
    transactions: List[CanonicalTransaction] = Field(
        default_factory=list,
        description="Consolidated list of canonical transactions across all sources"
    )
    
    outcome_state: Optional[str] = Field(None, description="Reconciliation outcome state (one of 13 enums)")
    assurance_level: Optional[str] = Field(None, description="Assurance level (L1 - L5)")
    receipt_id: Optional[str] = Field(None, description="ID of signed outcome receipt once generated")
    
    created_at: str = Field(..., description="ISO 8601 UTC creation timestamp")
    updated_at: str = Field(..., description="ISO 8601 UTC last modified timestamp")
