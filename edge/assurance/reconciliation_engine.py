import hashlib
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from dateutil import parser as dateutil_parser

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
        description: str,
        rule_reference: str = "VB_US_1099DA_2025_V1",
        provenance_references: Optional[List[Dict[str, Any]]] = None
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
        self.rule_reference = rule_reference
        self.provenance_references = provenance_references or []

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
            "description": self.description,
            "rule_reference": self.rule_reference,
            "provenance_references": self.provenance_references
        }


class ReconciliationResult:
    def __init__(self):
        self.outcome_state: str = "MATCHED"
        self.assurance_level: str = "L2_EVIDENCE_RECONCILED"
        self.material_differences: List[DifferenceRecord] = []
        self.unresolved_items: List[Dict[str, Any]] = []
        self.agreed_records: List[Dict[str, Any]] = []
        self.source_a_row_count: int = 0
        self.source_b_row_count: int = 0
        self.comparison_group_count: int = 0
        self.matched_group_count: int = 0
        self.difference_finding_count: int = 0
        self.unresolved_finding_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome_state": self.outcome_state,
            "assurance_level": self.assurance_level,
            "material_differences": [d.to_dict() for d in self.material_differences],
            "unresolved_items": self.unresolved_items,
            "agreed_records": self.agreed_records,
            "source_a_row_count": self.source_a_row_count,
            "source_b_row_count": self.source_b_row_count,
            "comparison_group_count": self.comparison_group_count,
            "matched_group_count": self.matched_group_count,
            "difference_finding_count": len(self.material_differences),
            "unresolved_finding_count": len(self.unresolved_items),
            "total_evaluated_count": self.comparison_group_count
        }


def compute_record_content_hash(tx: CanonicalTransaction) -> str:
    raw = f"{tx.source_id}|{tx.source_row_reference}|{tx.asset}|{tx.quantity}|{tx.proceeds}|{tx.cost_basis}|{tx.acquisition_date}|{tx.disposition_date}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class DeterministicReconciliationEngine:
    """
    Executes bounded, deterministic comparison between Form 1099-DA broker reports and tax ledger records.
    Adheres strictly to the declared outcome states, exact schema reason codes, and provenance invariants.
    """

    @classmethod
    def reconcile_case(cls, case: CanonicalCase) -> ReconciliationResult:
        result = ReconciliationResult()

        if len(case.sources) < 2:
            result.outcome_state = "UNRESOLVED_DATA"
            first_src = list(case.sources.keys())[0] if case.sources else "none"
            result.unresolved_items.append({
                "item_id": "unres_insufficient_sources",
                "reason_code": "AMBIGUOUS_SOURCE_DATA",
                "affected_source_id": first_src,
                "affected_row_ref": "Header",
                "description": "Deterministic reconciliation requires at least two distinct source documents.",
                "rule_reference": "VB_US_1099DA_2025_V1",
                "provenance_references": []
            })
            return result

        # Bind source roles explicitly by schema / naming convention rather than insertion order
        broker_sources = [sid for sid, meta in case.sources.items() if "1099" in (meta.schema_id or "").upper() or "BROKER" in (meta.schema_id or "").upper() or "1099" in sid.upper()]
        ledger_sources = [sid for sid, meta in case.sources.items() if "KOINLY" in (meta.schema_id or "").upper() or "LEDGER" in (meta.schema_id or "").upper() or "TAX" in sid.upper() or "COINTRACKER" in (meta.schema_id or "").upper()]

        if broker_sources and ledger_sources:
            src_a_id = broker_sources[0]
            src_b_id = ledger_sources[0]
        else:
            all_sids = list(case.sources.keys())
            src_a_id = all_sids[0]
            src_b_id = all_sids[1]

        txs_a = [t for t in case.transactions if t.source_id == src_a_id]
        txs_b = [t for t in case.transactions if t.source_id == src_b_id]

        result.source_a_row_count = len(txs_a)
        result.source_b_row_count = len(txs_b)

        matched_b_indices = set()
        diff_counter = 1
        comparison_groups = 0

        def build_prov(tx, src_id):
            if not tx:
                return []
            return [{
                "source_id": src_id,
                "source_sha256": tx.source_file_hash,
                "record_locator": tx.source_row_reference,
                "record_content_hash": compute_record_content_hash(tx),
                "field_names_evaluated": ["asset", "proceeds", "cost_basis", "acquisition_date", "disposition_date"]
            }]

        for tx_a in txs_a:
            comparison_groups += 1
            prov_a = build_prov(tx_a, src_a_id)
            start_diff_count = len(result.material_differences)
            start_unres_count = len(result.unresolved_items)

            if tx_a.is_unresolved and tx_a.basis_reported_to_irs != "NO":
                reason = "BASIS_UNAVAILABLE" if "BASIS" in (tx_a.unresolved_reason or "") else "DATE_UNAVAILABLE" if "DATE" in (tx_a.unresolved_reason or "") else "AMBIGUOUS_SOURCE_DATA"
                result.unresolved_items.append({
                    "item_id": f"unres_{tx_a.transaction_id}",
                    "reason_code": reason,
                    "affected_source_id": src_a_id,
                    "affected_row_ref": tx_a.source_row_reference,
                    "description": f"Missing required fact for asset {tx_a.asset} in {src_a_id}",
                    "rule_reference": "VB_US_1099DA_2025_V1",
                    "provenance_references": prov_a
                })

            # Find all potential matches on asset and date
            candidate_matches: List[Tuple[int, CanonicalTransaction]] = []
            for idx_b, tx_b in enumerate(txs_b):
                if idx_b in matched_b_indices:
                    continue

                dates_match = False
                if not tx_a.disposition_date or not tx_b.disposition_date:
                    dates_match = True
                elif tx_a.disposition_date == tx_b.disposition_date:
                    dates_match = True
                else:
                    try:
                        dt_a = dateutil_parser.isoparse(tx_a.disposition_date)
                        dt_b = dateutil_parser.isoparse(tx_b.disposition_date)
                        if dt_a.tzinfo is None and dt_b.tzinfo is not None:
                            result.unresolved_items.append({
                                "item_id": f"tz_miss_a_{tx_a.transaction_id}",
                                "reason_code": "TIMEZONE_CONTEXT_MISSING",
                                "affected_source_id": src_a_id,
                                "affected_row_ref": tx_a.source_row_reference,
                                "description": "Timezone context missing in broker disposition date",
                                "rule_reference": "VB_US_1099DA_2025_V1",
                                "provenance_references": prov_a
                            })
                            dates_match = True
                        elif dt_b.tzinfo is None and dt_a.tzinfo is not None:
                            result.unresolved_items.append({
                                "item_id": f"tz_miss_b_{tx_a.transaction_id}",
                                "reason_code": "TIMEZONE_CONTEXT_MISSING",
                                "affected_source_id": src_b_id,
                                "affected_row_ref": tx_b.source_row_reference,
                                "description": "Timezone context missing in ledger disposition date",
                                "rule_reference": "VB_US_1099DA_2025_V1",
                                "provenance_references": build_prov(tx_b, src_b_id)
                            })
                            dates_match = True
                        elif dt_a == dt_b or dt_a.date() == dt_b.date():
                            dates_match = True
                    except (ValueError, TypeError):
                        pass

                if tx_b.asset == tx_a.asset and dates_match:
                    candidate_matches.append((idx_b, tx_b))

            if len(candidate_matches) == 0:
                result.material_differences.append(DifferenceRecord(
                    difference_id=f"DIFF-{diff_counter:03d}",
                    difference_state="MISSING_FROM_LEDGER",
                    asset=tx_a.asset,
                    source_a_ref=f"{src_a_id}:{tx_a.source_row_reference}",
                    source_a_value=str(tx_a.proceeds) if tx_a.proceeds is not None else None,
                    source_b_ref="NOT_FOUND",
                    source_b_value=None,
                    variance=str(tx_a.proceeds) if tx_a.proceeds is not None else None,
                    description=f"Transaction for {tx_a.asset} present in broker Form 1099-DA ({tx_a.source_row_reference}) but missing from tax ledger. Next step: Review source records to confirm if this transaction belongs in the tax year ledger.",
                    rule_reference="VB_US_1099DA_2025_V1",
                    provenance_references=prov_a
                ))
                diff_counter += 1
                continue

            idx_b, tx_b = candidate_matches[0]
            matched_b_indices.add(idx_b)
            prov_b = build_prov(tx_b, src_b_id)
            prov_both = prov_a + prov_b

            # Proceeds comparison
            if tx_a.proceeds is not None and tx_b.proceeds is not None:
                proceeds_diff = abs(tx_a.proceeds - tx_b.proceeds)
                if proceeds_diff > Decimal("0"):
                    result.material_differences.append(DifferenceRecord(
                        difference_id=f"DIFF-{diff_counter:03d}",
                        difference_state="PROCEEDS_DIFFERENCE",
                        asset=tx_a.asset,
                        source_a_ref=f"{src_a_id}:{tx_a.source_row_reference}",
                        source_a_value=str(tx_a.proceeds),
                        source_b_ref=f"{src_b_id}:{tx_b.source_row_reference}",
                        source_b_value=str(tx_b.proceeds),
                        variance=str(proceeds_diff),
                        description=f"Proceeds differ by ${proceeds_diff}. Broker: ${tx_a.proceeds}, Client ledger: ${tx_b.proceeds}. Next step: Review the underlying transaction records and determine which amount, if either, should be used for the engagement.",
                        rule_reference="VB_US_1099DA_2025_V1",
                        provenance_references=prov_both
                    ))
                    diff_counter += 1

            # Cost basis & Reporting Scope comparison
            if tx_a.cost_basis is None and tx_a.basis_reported_to_irs == "NO":
                result.material_differences.append(DifferenceRecord(
                    difference_id=f"DIFF-{diff_counter:03d}",
                    difference_state="REPORTING_SCOPE_DIFFERENCE",
                    asset=tx_a.asset,
                    source_a_ref=f"{src_a_id}:{tx_a.source_row_reference}",
                    source_a_value="NOT_REPORTED (Box 2)",
                    source_b_ref=f"{src_b_id}:{tx_b.source_row_reference}",
                    source_b_value=str(tx_b.cost_basis) if tx_b.cost_basis is not None else "Not reported",
                    variance=None,
                    description=f"Broker did not report basis (Box 2 = NO). Client ledger reports basis of ${tx_b.cost_basis if tx_b.cost_basis is not None else '0.00'}. Next step: Review supporting basis documentation before relying on the ledger amount.",
                    rule_reference="VB_US_1099DA_2025_V1",
                    provenance_references=prov_both
                ))
                diff_counter += 1
            elif tx_a.cost_basis is not None and tx_b.cost_basis is not None:
                basis_diff = abs(tx_a.cost_basis - tx_b.cost_basis)
                if basis_diff > Decimal("0"):
                    result.material_differences.append(DifferenceRecord(
                        difference_id=f"DIFF-{diff_counter:03d}",
                        difference_state="BASIS_DIFFERENCE",
                        asset=tx_a.asset,
                        source_a_ref=f"{src_a_id}:{tx_a.source_row_reference}",
                        source_a_value=str(tx_a.cost_basis),
                        source_b_ref=f"{src_b_id}:{tx_b.source_row_reference}",
                        source_b_value=str(tx_b.cost_basis),
                        variance=str(basis_diff),
                        description=f"Cost basis differs by ${basis_diff}. Broker: ${tx_a.cost_basis}, Client ledger: ${tx_b.cost_basis}. Next step: Review supporting basis documentation and resolve the difference using professional judgment.",
                        rule_reference="VB_US_1099DA_2025_V1",
                        provenance_references=prov_both
                    ))
                    diff_counter += 1

            # Acquisition Date comparison
            if not tx_a.acquisition_date or not tx_b.acquisition_date:
                if tx_a.acquisition_date or tx_b.acquisition_date:
                    result.unresolved_items.append({
                        "item_id": f"unres_acq_{tx_a.transaction_id}",
                        "reason_code": "DATE_UNAVAILABLE",
                        "affected_source_id": src_a_id if not tx_a.acquisition_date else src_b_id,
                        "affected_row_ref": tx_a.source_row_reference if not tx_a.acquisition_date else tx_b.source_row_reference,
                        "description": "Acquisition date unavailable in source record.",
                        "rule_reference": "VB_US_1099DA_2025_V1",
                        "provenance_references": prov_both
                    })
            elif tx_a.acquisition_date != tx_b.acquisition_date:
                match_dates = False
                try:
                    dt_a = dateutil_parser.isoparse(tx_a.acquisition_date)
                    dt_b = dateutil_parser.isoparse(tx_b.acquisition_date)
                    if dt_a.tzinfo is None and dt_b.tzinfo is not None:
                        result.unresolved_items.append({
                            "item_id": f"tz_miss_a_acq_{tx_a.transaction_id}",
                            "reason_code": "TIMEZONE_CONTEXT_MISSING",
                            "affected_source_id": src_a_id,
                            "affected_row_ref": tx_a.source_row_reference,
                            "description": "Timezone missing in acquisition date",
                            "rule_reference": "VB_US_1099DA_2025_V1",
                            "provenance_references": prov_a
                        })
                        match_dates = True
                    elif dt_b.tzinfo is None and dt_a.tzinfo is not None:
                        result.unresolved_items.append({
                            "item_id": f"tz_miss_b_acq_{tx_a.transaction_id}",
                            "reason_code": "TIMEZONE_CONTEXT_MISSING",
                            "affected_source_id": src_b_id,
                            "affected_row_ref": tx_b.source_row_reference,
                            "description": "Timezone missing in acquisition date",
                            "rule_reference": "VB_US_1099DA_2025_V1",
                            "provenance_references": build_prov(tx_b, src_b_id)
                        })
                        match_dates = True
                    elif dt_a == dt_b or dt_a.date() == dt_b.date():
                        match_dates = True
                except (ValueError, TypeError):
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
                        description=f"Acquisition date differs: Broker reports {tx_a.acquisition_date} vs Client ledger reports {tx_b.acquisition_date}. Next step: Verify date from primary acquisition records.",
                        rule_reference="VB_US_1099DA_2025_V1",
                        provenance_references=prov_both
                    ))
                    diff_counter += 1

            if len(result.material_differences) == start_diff_count and len(result.unresolved_items) == start_unres_count:
                result.matched_group_count += 1
                agr_counter = len(result.agreed_records) + 1
                result.agreed_records.append({
                    "record_id": f"AGR-{agr_counter:03d}",
                    "classification": "MATCHED",
                    "asset": tx_a.asset,
                    "source_a_ref": f"{src_a_id}:{tx_a.source_row_reference}",
                    "source_a_value": str(tx_a.proceeds) if tx_a.proceeds is not None else "-",
                    "source_b_ref": f"{src_b_id}:{tx_b.source_row_reference}",
                    "source_b_value": str(tx_b.proceeds) if tx_b.proceeds is not None else "-",
                    "variance": "0.00",
                    "description": "Supported information agrees (gross proceeds, cost basis, and acquisition dates match identically)."
                })

        # Unmatched Ledger Rows (MISSING_FROM_1099DA)
        for idx_b, tx_b in enumerate(txs_b):
            if idx_b not in matched_b_indices:
                comparison_groups += 1
                prov_b = build_prov(tx_b, src_b_id)
                result.material_differences.append(DifferenceRecord(
                    difference_id=f"DIFF-{diff_counter:03d}",
                    difference_state="MISSING_FROM_1099DA",
                    asset=tx_b.asset,
                    source_a_ref="NOT_FOUND",
                    source_a_value=None,
                    source_b_ref=f"{src_b_id}:{tx_b.source_row_reference}",
                    source_b_value=str(tx_b.proceeds) if tx_b.proceeds is not None else None,
                    variance=str(tx_b.proceeds) if tx_b.proceeds is not None else None,
                    description=f"Transaction for {tx_b.asset} present in client tax ledger ({tx_b.source_row_reference}) but not reported on broker Form 1099-DA. Next step: Review source documentation to determine reporting requirements.",
                    rule_reference="VB_US_1099DA_2025_V1",
                    provenance_references=prov_b
                ))
                diff_counter += 1

        result.comparison_group_count = comparison_groups

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
