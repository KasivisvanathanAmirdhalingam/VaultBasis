from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum

class ProfileState(str, Enum):
    RECOGNIZED = "Recognized"
    UNSUPPORTED = "Unsupported"
    AMBIGUOUS = "Ambiguous"

class ReadinessState(str, Enum):
    READY = "READY"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    UNSUPPORTED = "UNSUPPORTED"

class RowStats(BaseModel):
    read: int = 0
    accepted: int = 0
    rejected: int = 0
    unresolved: int = 0

class BasisStateCounts(BaseModel):
    known_zero: int = 0
    not_provided: int = 0
    present: int = 0
    unresolved: int = 0

class DataConditions(BaseModel):
    missing_required_fields: int = 0
    malformed_values: int = 0
    duplicates_detected_exact: int = 0
    duplicates_detected_conflicting: int = 0
    timezone_ambiguity: int = 0
    basis_reporting_state_unspecified: int = 0

class PreflightReport(BaseModel):
    source_id: str
    detected_profile: str
    profile_version: str
    profile_state: ProfileState
    source_hash: str
    byte_size: int
    rows: RowStats = Field(default_factory=RowStats)
    data_conditions: DataConditions = Field(default_factory=DataConditions)
    basis_state: BasisStateCounts = Field(default_factory=BasisStateCounts)
    reason_codes: List[str] = Field(default_factory=list)
    readiness: ReadinessState = ReadinessState.READY
    
    def evaluate_readiness(self):
        if self.profile_state == ProfileState.UNSUPPORTED:
            self.readiness = ReadinessState.UNSUPPORTED
        elif self.profile_state == ProfileState.AMBIGUOUS:
            self.readiness = ReadinessState.REQUIRES_REVIEW
        elif self.rows.rejected > 0 or self.rows.unresolved > 0:
            self.readiness = ReadinessState.REQUIRES_REVIEW
        elif self.data_conditions.malformed_values > 0 or self.data_conditions.missing_required_fields > 0:
            self.readiness = ReadinessState.REQUIRES_REVIEW
        else:
            self.readiness = ReadinessState.READY
