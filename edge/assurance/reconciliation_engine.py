"""
VaultBasis Edge — Deterministic Assurance & Reconciliation Engine
Conforms to PRD §14.3 (13 Outcome States), §15.1 (Exact Decimal Arithmetic), §16.1 (Shallow Provenance)
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from schemas.canonical.case import CanonicalCase
from schemas.canonical.transaction import CanonicalTransaction


class DifferenceRecord:
    def __init__(
        self,
        difference_id: str,
        difference_state: str,
        asset: str,
        source_a_ref: str,
        source_a_value: Optional[str],
        source_b_ref: str,
        source_b_value: Optional[str],
        variance: Optional[str],
        description: str
    ):
        self.difference_id = difference_id
        self.difference_state = difference_state
        self.asset = asset
        self.source_a_ref = source_a_ref
        self.source_a_value = source_a_value
        self.source_b_ref = source_b_ref
        self.source_b_value = source_b_value
        self.variance = variance
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "difference_id": self.difference_id,
            "difference_state": self.difference_state,
            "asset": self.asset,
            "source_a_ref": self.source_a_ref,
            "source_a_value": self.source_a_value,
            "source_b_ref": self.source_b_ref,
            "source_b_value": self.source_b_value,
            "variance": self.variance,
            "description": self.description
        }


class ReconciliationResult:
    def __init__(self):
        self.outcome_state: str = "MATCHED"
        self.assurance_level: str = "L2_EVIDENCE_RECONCILED"
        self.material_differences: List[DifferenceRecord] = []
        self.unresolved_items: List[Dict[str, Any]] = []
        self.provenance_references: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome_state": self.outcome_state,
            "assurance_level": self.assurance_level,
            "material_differences": [d.to_dict() for d in self.material_differences],
            "unresolved_items": self.unresolved_items,
            "provenance_references": self.provenance_references
        }


class DeterministicReconciliationEngine:
    """
    Executes bounded, deterministic comparison between Form 1099-DA and tax system outputs.
    Adheres strictly to the 13 declared outcome states and invariants.
    """

    @classmethod
    def reconcile_case(cls, case: CanonicalCase) -> ReconciliationResult:
        result = ReconciliationResult()

        # Separate transactions by source document
        source_ids = list(case.sources.keys())
        if len(source_ids) < 2:
            # Cannot reconcile without at least 2 sources
            result.outcome_state = "UNRESOLVED_DATA"
            result.unresolved_items.append({
                "item_id": "unres_insufficient_sources",
                "reason_code": "AMBIGUOUS_SOURCE_DATA",
                "affected_source_id": source_ids[0] if source_ids else "none",
                "affected_row_ref": "Header",
                "description": "Reconciliation requires at least two source documents (e.g. 1099-DA + Tax Report)."
            })
            return result

        src_a_id = source_ids[0]
        src_b_id = source_ids[1]

        txs_a = [t for t in case.transactions if t.source_id == src_a_id]
        txs_b = [t for t in case.transactions if t.source_id == src_b_id]

        matched_b_indices = set()
        diff_counter = 1

        for tx_a in txs_a:
            # Provenance record for tx_a
            prov_a_id = f"PROV-{src_a_id}-{tx_a.source_row_reference}"
            result.provenance_references.append({
                "reference_id": prov_a_id,
                "source_id": src_a_id,
                "row_ref": tx_a.source_row_reference,
                "content_hash": tx_a.source_file_hash
            })

            # Check for unresolved state in tx_a
            if tx_a.is_unresolved and tx_a.basis_reported_to_irs != "NO":
                result.unresolved_items.append({
                    "item_id": f"unres_{tx_a.transaction_id}",
                    "reason_code": tx_a.unresolved_reason or "BASIS_UNAVAILABLE",
                    "affected_source_id": src_a_id,
                    "affected_row_ref": tx_a.source_row_reference,
                    "description": f"Missing required fact for asset {tx_a.asset} in {src_a_id}"
                })

            # Find candidate match in Source B by asset and disposition date
            candidate_match: Optional[Tuple[int, CanonicalTransaction]] = None
            for idx_b, tx_b in enumerate(txs_b):
                if idx_b in matched_b_indices:
                    continue
                
                # Check disposition date equality or ISO date equality
                dates_match = False
                if not tx_a.disposition_date or not tx_b.disposition_date:
                    dates_match = True
                elif tx_a.disposition_date == tx_b.disposition_date:
                    dates_match = True
                else:
                    try:
                        import dateutil.parser
                        dt_a = dateutil.parser.isoparse(tx_a.disposition_date)
                        dt_b = dateutil.parser.isoparse(tx_b.disposition_date)
                        
                        if dt_a.tzinfo is None and dt_b.tzinfo is not None:
                            result.unresolved_items.append({"item_id": "tz_miss_a", "reason_code": "TIMEZONE_CONTEXT_MISSING", "affected_source_id": src_a_id, "affected_row_ref": tx_a.source_row_reference, "description": ""})
                            dates_match = True # Treat as matched for grouping purposes to expose the unresolved item
                        elif dt_b.tzinfo is None and dt_a.tzinfo is not None:
                            result.unresolved_items.append({"item_id": "tz_miss_b", "reason_code": "TIMEZONE_CONTEXT_MISSING", "affected_source_id": src_b_id, "affected_row_ref": tx_b.source_row_reference, "description": ""})
                            dates_match = True
                        elif dt_a == dt_b:
                            dates_match = True
                    except ValueError:
                        pass
                
                if tx_b.asset == tx_a.asset and dates_match:
                    candidate_match = (idx_b, tx_b)
                    break

            if candidate_match is None:
                # Missing from Source B (Ledger)
                result.material_differences.append(DifferenceRecord(
                    difference_id=f"DIFF-{diff_counter:03d}",
                    difference_state="MISSING_FROM_LEDGER",
                    asset=tx_a.asset,
                    source_a_ref=f"{src_a_id}:{tx_a.source_row_reference}",
                    source_a_value=str(tx_a.proceeds) if tx_a.proceeds is not None else None,
                    source_b_ref="NOT_FOUND",
                    source_b_value=None,
                    variance=str(tx_a.proceeds) if tx_a.proceeds is not None else None,
                    description=f"Transaction present in {src_a_id} but missing from tax ledger {src_b_id}."
                ))
                diff_counter += 1
                continue

            idx_b, tx_b = candidate_match
            matched_b_indices.add(idx_b)

            # 0. Compare Quantity
            if tx_a.quantity is None or tx_b.quantity is None:
                result.unresolved_items.append({
                    "item_id": f"unres_qty_{tx_a.transaction_id}",
                    "reason_code": "QUANTITY_UNAVAILABLE",
                    "affected_source_id": src_a_id if tx_a.quantity is None else src_b_id,
                    "affected_row_ref": tx_a.source_row_reference if tx_a.quantity is None else tx_b.source_row_reference,
                    "description": "Missing required quantity prevents exact reconciliation."
                })

            # Provenance record for tx_b
            prov_b_id = f"PROV-{src_b_id}-{tx_b.source_row_reference}"
            result.provenance_references.append({
                "reference_id": prov_b_id,
                "source_id": src_b_id,
                "row_ref": tx_b.source_row_reference,
                "content_hash": tx_b.source_file_hash
            })

            # 1. Compare Proceeds
            if tx_a.proceeds is not None and tx_b.proceeds is not None:
                proceeds_diff = abs(tx_a.proceeds - tx_b.proceeds)
                if proceeds_diff > Decimal("0.01"):
                    result.material_differences.append(DifferenceRecord(
                        difference_id=f"DIFF-{diff_counter:03d}",
                        difference_state="PROCEEDS_DIFFERENCE",
                        asset=tx_a.asset,
                        source_a_ref=f"{src_a_id}:{tx_a.source_row_reference}",
                        source_a_value=str(tx_a.proceeds),
                        source_b_ref=f"{src_b_id}:{tx_b.source_row_reference}",
                        source_b_value=str(tx_b.proceeds),
                        variance=str(proceeds_diff),
                        description=f"Proceeds differ by ${proceeds_diff:.2f}."
                    ))
                    diff_counter += 1

            # 2. Compare Cost Basis & Reporting Scope
            # Check 2025 reporting scope: If 1099-DA Box 2 explicitly indicates not reported
            if tx_a.cost_basis is None and tx_a.basis_reported_to_irs == "NO":
                result.material_differences.append(DifferenceRecord(
                    difference_id=f"DIFF-{diff_counter:03d}",
                    difference_state="REPORTING_SCOPE_DIFFERENCE",
                    asset=tx_a.asset,
                    source_a_ref=f"{src_a_id}:{tx_a.source_row_reference}",
                    source_a_value="NOT_REPORTED (Box 2)",
                    source_b_ref=f"{src_b_id}:{tx_b.source_row_reference}",
                    source_b_value=str(tx_b.cost_basis) if tx_b.cost_basis is not None else None,
                    variance=str(tx_b.cost_basis) if tx_b.cost_basis is not None else None,
                    description="Reporting scope difference: Broker 1099-DA does not report basis for 2025 non-covered disposition."
                ))
                diff_counter += 1
            elif tx_a.cost_basis is not None and tx_b.cost_basis is not None:
                basis_diff = abs(tx_a.cost_basis - tx_b.cost_basis)
                if basis_diff > Decimal("0.01"):
                    result.material_differences.append(DifferenceRecord(
                        difference_id=f"DIFF-{diff_counter:03d}",
                        difference_state="BASIS_DIFFERENCE",
                        asset=tx_a.asset,
                        source_a_ref=f"{src_a_id}:{tx_a.source_row_reference}",
                        source_a_value=str(tx_a.cost_basis),
                        source_b_ref=f"{src_b_id}:{tx_b.source_row_reference}",
                        source_b_value=str(tx_b.cost_basis),
                        variance=str(basis_diff),
                        description=f"Difference detected: basis differs by ${basis_diff:.2f}. Review source acquisition records and reporting scope."
                    ))
                    diff_counter += 1

            # 3. Compare Dates
            if not tx_a.acquisition_date or not tx_b.acquisition_date:
                # If one is missing but not both, it is unresolved (missing fact)
                if tx_a.acquisition_date or tx_b.acquisition_date:
                    result.unresolved_items.append({
                        "item_id": f"unres_acq_date_{tx_a.transaction_id}",
                        "reason_code": "ACQUISITION_DATE_UNAVAILABLE",
                        "affected_source_id": src_a_id if not tx_a.acquisition_date else src_b_id,
                        "affected_row_ref": tx_a.source_row_reference if not tx_a.acquisition_date else tx_b.source_row_reference,
                        "description": "Missing required acquisition date."
                    })
            elif tx_a.acquisition_date != tx_b.acquisition_date:
                # Before checking string equality, attempt normalized parsing if they look like ISO timestamps
                import dateutil.parser
                match_dates = False
                try:
                    dt_a = dateutil.parser.isoparse(tx_a.acquisition_date)
                    dt_b = dateutil.parser.isoparse(tx_b.acquisition_date)
                    
                    if dt_a.tzinfo is None and dt_b.tzinfo is not None:
                        result.unresolved_items.append({"item_id": "tz_miss_a", "reason_code": "TIMEZONE_CONTEXT_MISSING", "affected_source_id": src_a_id, "affected_row_ref": tx_a.source_row_reference, "description": ""})
                        match_dates = True # Prevent ACQ_DATE_DIFF due to tz mismatch
                    elif dt_b.tzinfo is None and dt_a.tzinfo is not None:
                        result.unresolved_items.append({"item_id": "tz_miss_b", "reason_code": "TIMEZONE_CONTEXT_MISSING", "affected_source_id": src_b_id, "affected_row_ref": tx_b.source_row_reference, "description": ""})
                        match_dates = True
                    elif dt_a == dt_b:
                        match_dates = True
                except ValueError:
                    pass

                if not match_dates:
                    result.material_differences.append(DifferenceRecord(
                        difference_id=f"DIFF-{diff_counter:03d}",
                        difference_state="ACQUISITION_DATE_DIFFERENCE",
                        asset=tx_a.asset,
                        source_a_ref=f"{src_a_id}:{tx_a.source_row_reference}",
                        source_a_value=tx_a.acquisition_date,
                        source_b_ref=f"{src_b_id}:{tx_b.source_row_reference}",
                        source_b_value=tx_b.acquisition_date,
                        variance=None,
                        description=f"Acquisition date mismatch: {tx_a.acquisition_date} vs {tx_b.acquisition_date}."
                    ))
                    diff_counter += 1

        # Check for transactions in B missing from A
        for idx_b, tx_b in enumerate(txs_b):
            if idx_b not in matched_b_indices:
                result.material_differences.append(DifferenceRecord(
                    difference_id=f"DIFF-{diff_counter:03d}",
                    difference_state="MISSING_FROM_1099DA",
                    asset=tx_b.asset,
                    source_a_ref="NOT_FOUND",
                    source_a_value=None,
                    source_b_ref=f"{src_b_id}:{tx_b.source_row_reference}",
                    source_b_value=str(tx_b.proceeds) if tx_b.proceeds is not None else None,
                    variance=str(tx_b.proceeds) if tx_b.proceeds is not None else None,
                    description=f"Transaction present in tax ledger {src_b_id} but missing from broker Form 1099-DA."
                ))
                diff_counter += 1

        # Determine consolidated outcome_state
        diff_states = [d.difference_state for d in result.material_differences]
        if result.unresolved_items:
            result.outcome_state = "UNRESOLVED_DATA"
        elif "PROCEEDS_DIFFERENCE" in diff_states:
            result.outcome_state = "PROCEEDS_DIFFERENCE"
        elif "BASIS_DIFFERENCE" in diff_states:
            result.outcome_state = "BASIS_DIFFERENCE"
        elif "REPORTING_SCOPE_DIFFERENCE" in diff_states:
            result.outcome_state = "REPORTING_SCOPE_DIFFERENCE"
        elif "MISSING_FROM_1099DA" in diff_states:
            result.outcome_state = "MISSING_FROM_1099DA"
        elif "MISSING_FROM_LEDGER" in diff_states:
            result.outcome_state = "MISSING_FROM_LEDGER"
        elif "ACQUISITION_DATE_DIFFERENCE" in diff_states:
            result.outcome_state = "ACQUISITION_DATE_DIFFERENCE"
        else:
            result.outcome_state = "MATCHED"

        return result
