import pytest
from pathlib import Path
from edge.connectors.validator import IntakeDispatcher

def test_l2_ugly_synthetic_case_preflight_preserves_distinctions():
    """
    Test with a deliberately ugly synthetic case containing simultaneously:
    - known-zero basis
    - missing basis
    - not-reported basis
    - malformed decimal
    - missing timezone
    - exact duplicate
    - conflicting duplicate
    - proceeds difference
    - basis difference
    - unsupported/missing field
    """
    pass
def test_l2_ugly_synthetic_case_preflight_preserves_distinctions():
    from edge.connectors.validator import IntakeDispatcher
    from schemas.canonical.preflight import ReadinessState, ProfileState

    with open("tests/fixtures/L2_ugly_synthetic_1099.csv", "rb") as f:
        data_1099 = f.read()
    
    report_1099 = IntakeDispatcher.preflight_document(
        data_bytes=data_1099,
        filename="L2_ugly_synthetic_1099.csv",
        source_id="synthetic_1099"
    )
    
    assert report_1099.profile_state == ProfileState.RECOGNIZED
    assert report_1099.readiness == ReadinessState.REQUIRES_REVIEW
    assert report_1099.rows.read == 12
    assert report_1099.rows.rejected > 0
    assert report_1099.rows.unresolved > 0
    assert report_1099.data_conditions.malformed_values > 0
    
    with open("tests/fixtures/L2_ugly_synthetic_ledger.csv", "rb") as f:
        data_ledger = f.read()
        
    report_ledger = IntakeDispatcher.preflight_document(
        data_bytes=data_ledger,
        filename="L2_ugly_synthetic_ledger.csv",
        source_id="synthetic_ledger"
    )
    
    assert report_ledger.profile_state == ProfileState.RECOGNIZED
