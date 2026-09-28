import pytest
from edge.core.explanations import FindingFacts, render_explanation

def test_golden_explanations_are_immutable():
    """
    RC2-L2.2: Finding Why Golden Explanations
    Ensures that the rendered explanations perfectly match the approved linguistic
    boundaries and do not invent facts, point fingers, or use unsafe terminology.
    """
    
    # BASIS_DIFFERENCE
    basis_facts = FindingFacts(
        finding_code="BASIS_DIFFERENCE",
        source_a_id="Broker",
        source_b_id="Ledger",
        source_a_val="2104.93",
        source_b_val="1842.17",
        variance="262.76"
    )
    
    basis_explanation = render_explanation(basis_facts)
    
    expected_basis_explanation = """What was compared
Cost basis for the matched disposal.

Broker source
2104.93

Tax-ledger source
1842.17

Observed difference
262.76

Matched using
Asset symbol and disposition date

Why this finding occurred
Both supported sources supplied basis information for the matched record, and the values were different under the declared comparison semantics.

VaultBasis determination
BASIS_DIFFERENCE

Boundary
VaultBasis identifies the difference. It does not determine which basis amount is tax-correct."""

    assert basis_explanation == expected_basis_explanation, "BASIS_DIFFERENCE explanation mutated!"
    
    # UNRESOLVED_DATA
    unresolved_facts = FindingFacts(
        finding_code="UNRESOLVED_DATA",
        source_a_id="Broker",
        source_b_id="Ledger",
        source_a_val="TIMEZONE_CONTEXT_MISSING",
        source_b_val="N/A",
        variance="Missing or ambiguous fact"
    )
    
    unresolved_explanation = render_explanation(unresolved_facts)
    
    expected_unresolved_explanation = """What was compared
Required evidence for deterministic evaluation.

Broker source
TIMEZONE_CONTEXT_MISSING

Tax-ledger source
N/A

Observed difference
Required fact missing or fundamentally ambiguous.

Matched using
Asset symbol and disposition date

Why this finding occurred
The evidence required for deterministic evaluation was not available or sufficiently specified in the supported source information.

VaultBasis determination
UNRESOLVED_DATA

Boundary
VaultBasis did not infer, substitute, or default the missing information. Practitioner review is required."""

    assert unresolved_explanation == expected_unresolved_explanation, "UNRESOLVED_DATA explanation mutated!"
    
    # MISSING_FROM_LEDGER
    missing_ledger_facts = FindingFacts(
        finding_code="MISSING_FROM_LEDGER",
        source_a_id="Broker",
        source_b_id="Ledger",
        source_a_val="Record present",
        source_b_val="Record missing"
    )
    missing_ledger_explanation = render_explanation(missing_ledger_facts)
    assert "MISSING_FROM_LEDGER" in missing_ledger_explanation
    assert "VaultBasis identifies the missing record. It does not determine whether the ledger is incomplete or if the broker reported a duplicate/phantom transaction." in missing_ledger_explanation

    # Unknown code fails visibly
    with pytest.raises(ValueError, match="Unknown FindingCode: UNKNOWN_CODE_123"):
        render_explanation(FindingFacts(finding_code="UNKNOWN_CODE_123", source_a_id="A", source_b_id="B"))

def test_explanations_neutral_language():
    """
    Ensures that words like 'wrong', 'correct' (without 'not determine which is'),
    'compliant', 'IRS-approved' do not exist in the output of any standard finding.
    """
    codes = [
        "BASIS_DIFFERENCE", "PROCEEDS_DIFFERENCE", "UNRESOLVED_DATA", 
        "MATCHED", "MISSING_FROM_LEDGER", "MISSING_FROM_1099DA", 
        "ACQUISITION_DATE_DIFFERENCE", "REPORTING_SCOPE_DIFFERENCE"
    ]
    
    for code in codes:
        facts = FindingFacts(
            finding_code=code,
            source_a_id="Broker",
            source_b_id="Ledger",
            source_a_val="ValA",
            source_b_val="ValB",
            variance="Var"
        )
        explanation = render_explanation(facts).lower()
        
        # Invariants
        assert "wrong" not in explanation
        assert "compliant" not in explanation
        assert "irs-approved" not in explanation
        assert "audit-proof" not in explanation
        
        # 'correct' is only allowed in the boundary statement 
        # e.g., "does not determine which basis amount is tax-correct"
        if "correct" in explanation:
            assert "does not determine" in explanation or "does not certify" in explanation
