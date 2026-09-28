from typing import Any, Dict, List, Optional
from edge.assurance.reconciliation_engine import DifferenceRecord, ReconciliationResult

class FindingFacts:
    def __init__(self, finding_code: str, source_a_id: str, source_b_id: str, 
                 source_a_val: Optional[str] = None, source_b_val: Optional[str] = None,
                 variance: Optional[str] = None, match_semantics: str = "Asset symbol and disposition date"):
        self.finding_code = finding_code
        self.source_a_id = source_a_id
        self.source_b_id = source_b_id
        self.source_a_val = source_a_val
        self.source_b_val = source_b_val
        self.variance = variance
        self.match_semantics = match_semantics


def render_explanation(facts: FindingFacts) -> str:
    """
    Renders a fixed, deterministic explanation for a finding.
    Must answer: what was compared, what each source supplied, observed difference, 
    how records matched, why finding occurred, and boundary.
    """
    if facts.finding_code == "BASIS_DIFFERENCE":
        return f"""What was compared
Cost basis for the matched disposal.

Broker source
{facts.source_a_val}

Tax-ledger source
{facts.source_b_val}

Observed difference
{facts.variance}

Matched using
{facts.match_semantics}

Why this finding occurred
Both supported sources supplied basis information for the matched record, and the values were different under the declared comparison semantics.

VaultBasis determination
BASIS_DIFFERENCE

Boundary
VaultBasis identifies the difference. It does not determine which basis amount is tax-correct."""

    elif facts.finding_code == "PROCEEDS_DIFFERENCE":
        return f"""What was compared
Gross proceeds for the matched disposal.

Broker source
{facts.source_a_val}

Tax-ledger source
{facts.source_b_val}

Observed difference
{facts.variance}

Matched using
{facts.match_semantics}

Why this finding occurred
Both supported sources supplied proceeds information for the matched record, and the values were different under the declared comparison semantics.

VaultBasis determination
PROCEEDS_DIFFERENCE

Boundary
VaultBasis identifies the difference. It does not determine which proceeds amount is tax-correct."""

    elif facts.finding_code == "UNRESOLVED_DATA":
        return f"""What was compared
Required evidence for deterministic evaluation.

Broker source
{facts.source_a_val if facts.source_a_val else 'Unavailable or ambiguous'}

Tax-ledger source
{facts.source_b_val if facts.source_b_val else 'Unavailable or ambiguous'}

Observed difference
Required fact missing or fundamentally ambiguous.

Matched using
{facts.match_semantics}

Why this finding occurred
The evidence required for deterministic evaluation was not available or sufficiently specified in the supported source information.

VaultBasis determination
UNRESOLVED_DATA

Boundary
VaultBasis did not infer, substitute, or default the missing information. Practitioner review is required."""

    elif facts.finding_code == "MATCHED":
        return f"""What was compared
Required fields (Proceeds, Basis, Dates) for the disposal.

Broker source
Values matched

Tax-ledger source
Values matched

Observed difference
None

Matched using
{facts.match_semantics}

Why this finding occurred
Both supported sources supplied information for the matched record, and the values were identical under the declared comparison semantics.

VaultBasis determination
MATCHED

Boundary
VaultBasis confirms identical values exist in both artifacts. It does not certify that the underlying source data is legally correct."""

    elif facts.finding_code == "MISSING_FROM_LEDGER":
        return f"""What was compared
Record presence across artifacts.

Broker source
Record present

Tax-ledger source
Record missing

Observed difference
Transaction present in broker source but missing from tax ledger.

Matched using
{facts.match_semantics}

Why this finding occurred
The broker source provided a transaction for which no corresponding matching record could be found in the tax ledger.

VaultBasis determination
MISSING_FROM_LEDGER

Boundary
VaultBasis identifies the missing record. It does not determine whether the ledger is incomplete or if the broker reported a duplicate/phantom transaction."""

    elif facts.finding_code == "MISSING_FROM_1099DA":
        return f"""What was compared
Record presence across artifacts.

Broker source
Record missing

Tax-ledger source
Record present

Observed difference
Transaction present in tax ledger but missing from broker source.

Matched using
{facts.match_semantics}

Why this finding occurred
The tax ledger provided a transaction for which no corresponding matching record could be found in the broker source.

VaultBasis determination
MISSING_FROM_1099DA

Boundary
VaultBasis identifies the missing record. It does not determine whether the ledger is over-reporting or if the broker omitted a transaction."""

    elif facts.finding_code == "ACQUISITION_DATE_DIFFERENCE":
        return f"""What was compared
Acquisition date for the matched disposal.

Broker source
{facts.source_a_val}

Tax-ledger source
{facts.source_b_val}

Observed difference
Acquisition dates mismatch

Matched using
{facts.match_semantics}

Why this finding occurred
Both supported sources supplied an acquisition date for the matched record, but the dates were not identical under the declared comparison semantics.

VaultBasis determination
ACQUISITION_DATE_DIFFERENCE

Boundary
VaultBasis identifies the difference. It does not determine which acquisition date is tax-correct."""

    elif facts.finding_code == "REPORTING_SCOPE_DIFFERENCE":
        return f"""What was compared
Cost basis reporting scope (e.g. Covered vs Non-Covered).

Broker source
{facts.source_a_val}

Tax-ledger source
{facts.source_b_val}

Observed difference
Broker indicates basis not reported to IRS.

Matched using
{facts.match_semantics}

Why this finding occurred
The broker explicitly indicates the transaction is non-covered or basis is not reported to the IRS, while the tax ledger provides a calculated basis value.

VaultBasis determination
REPORTING_SCOPE_DIFFERENCE

Boundary
VaultBasis identifies the scope difference. It does not verify whether the asset legally qualifies as a non-covered security."""

    else:
        # Fails visibly for unknown codes
        raise ValueError(f"Unknown FindingCode: {facts.finding_code}")


def explain_reconciliation(result: ReconciliationResult) -> List[Dict[str, Any]]:
    explanations = []
    
    # Process material differences
    for diff in result.material_differences:
        src_a, src_b = _parse_refs(diff.source_a_ref, diff.source_b_ref)
        facts = FindingFacts(
            finding_code=diff.difference_state,
            source_a_id=src_a,
            source_b_id=src_b,
            source_a_val=diff.source_a_value,
            source_b_val=diff.source_b_value,
            variance=diff.variance
        )
        explanation = render_explanation(facts)
        explanations.append({
            "item_id": diff.difference_id,
            "finding_code": diff.difference_state,
            "explanation": explanation
        })
        
    # Process unresolved items
    for unres in result.unresolved_items:
        facts = FindingFacts(
            finding_code="UNRESOLVED_DATA",
            source_a_id=unres.get("affected_source_id", "Unknown"),
            source_b_id="Unknown",
            source_a_val=unres.get("reason_code"),
            source_b_val="N/A",
            variance="Missing or ambiguous fact"
        )
        explanation = render_explanation(facts)
        explanations.append({
            "item_id": unres["item_id"],
            "finding_code": "UNRESOLVED_DATA",
            "reason_code": unres["reason_code"],
            "explanation": explanation
        })
        
    # Process matched items (this would require full record list, but we can return the global MATCHED state if applicable)
    if not result.material_differences and not result.unresolved_items and result.outcome_state == "MATCHED":
        facts = FindingFacts(
            finding_code="MATCHED",
            source_a_id="All Sources",
            source_b_id="All Sources"
        )
        explanation = render_explanation(facts)
        explanations.append({
            "item_id": "GLOBAL_MATCH",
            "finding_code": "MATCHED",
            "explanation": explanation
        })
        
    return explanations

def _parse_refs(ref_a: str, ref_b: str):
    src_a = ref_a.split(":")[0] if ":" in ref_a else ref_a
    src_b = ref_b.split(":")[0] if ":" in ref_b else ref_b
    return src_a, src_b
