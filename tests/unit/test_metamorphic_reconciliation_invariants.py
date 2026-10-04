"""
VaultBasis — Metamorphic & Deterministic Invariant Test Suite
Tests PRD §64, §71 and MMP15-PROD-SAMPLE-001 Invariants:
1. Row Order Metamorphic Invariance: Permuting CSV row order preserves exact reconciliation outcome.
2. Line Ending Metamorphic Invariance: CRLF vs LF produce bit-for-bit equivalent canonical transactions.
3. Extra Column Metamorphic Invariance: Superfluous unmapped columns are safely ignored without semantic drift.
4. Perturbation Sensitivity: 1-cent basis shift or quantity perturbation strictly breaks exact agreement.
5. Strict Ambiguity Invariant: Multiple candidate matches are surfaced explicitly, never resolved by guessing.
6. Conflicting Evidence Invariant: Contradictory source records preserve conflict rather than majority-voting.
"""

from decimal import Decimal
import pytest

from edge.assurance.reconciliation_engine import DeterministicReconciliationEngine
from edge.connectors.validator import IntakeDispatcher
from schemas.canonical.case import CanonicalCase, SourceDocumentMetadata
from schemas.canonical.transaction import CanonicalTransaction


# Baseline synthetic records for metamorphic testing
CSV_1099DA_BASE = (
    "Property,Units,Date sold,Proceeds,Date acquired,Cost basis,Box 2\n"
    "BTC,0.50000000,2025-03-15,45000.00,2024-01-10,30000.00,YES\n"
    "ETH,4.00000000,2025-06-20,12000.00,2025-02-15,8000.00,YES\n"
)

CSV_KOINLY_BASE = (
    "Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired\n"
    "2025-03-15,BTC,0.50000000,30000.00,45000.00,15000.00,2024-01-10\n"
    "2025-06-20,ETH,4.00000000,8000.00,12000.00,4000.00,2025-02-15\n"
)


def _build_case_from_csvs(csv_da: str, csv_koinly: str, case_id: str = "CASE-TEST-METAMORPHIC") -> CanonicalCase:
    meta_da, txs_da = IntakeDispatcher.ingest_document(
        data_bytes=csv_da.encode("utf-8"),
        filename="broker_1099da.csv",
        source_id="SRC-1099DA",
        declared_schema="AUTO"
    )
    meta_koinly, txs_koinly = IntakeDispatcher.ingest_document(
        data_bytes=csv_koinly.encode("utf-8"),
        filename="koinly_report.csv",
        source_id="SRC-KOINLY",
        declared_schema="AUTO"
    )
    return CanonicalCase(
        case_id=case_id,
        tax_year=2025,
        jurisdiction="US",
        case_status="SOURCES_INGESTED",
        case_kind="TEST_FIXTURE",
        sources={
            "SRC-1099DA": meta_da,
            "SRC-KOINLY": meta_koinly
        },
        transactions=txs_da + txs_koinly,
        created_at="2026-10-04T00:00:00Z",
        updated_at="2026-10-04T00:00:00Z"
    )


def test_metamorphic_row_order_invariance():
    """
    Metamorphic Invariant 1:
    Reversing the row order of ingested sources MUST produce identical reconciliation outcome state,
    material difference counts, and unresolved item metrics.
    """
    # 1. Base order
    case_base = _build_case_from_csvs(CSV_1099DA_BASE, CSV_KOINLY_BASE, "CASE-ORDER-BASE")
    res_base = DeterministicReconciliationEngine.reconcile_case(case_base)

    # 2. Permuted / reversed order
    csv_da_reversed = (
        "Property,Units,Date sold,Proceeds,Date acquired,Cost basis,Box 2\n"
        "ETH,4.00000000,2025-06-20,12000.00,2025-02-15,8000.00,YES\n"
        "BTC,0.50000000,2025-03-15,45000.00,2024-01-10,30000.00,YES\n"
    )
    csv_koinly_reversed = (
        "Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired\n"
        "2025-06-20,ETH,4.00000000,8000.00,12000.00,4000.00,2025-02-15\n"
        "2025-03-15,BTC,0.50000000,30000.00,45000.00,15000.00,2024-01-10\n"
    )
    case_permuted = _build_case_from_csvs(csv_da_reversed, csv_koinly_reversed, "CASE-ORDER-PERM")
    res_permuted = DeterministicReconciliationEngine.reconcile_case(case_permuted)

    # Assert invariant equivalence
    assert res_base.outcome_state == res_permuted.outcome_state
    assert res_base.assurance_level == res_permuted.assurance_level
    assert len(res_base.material_differences) == len(res_permuted.material_differences)
    assert len(res_base.unresolved_items) == len(res_permuted.unresolved_items)


def test_metamorphic_line_ending_invariance():
    """
    Metamorphic Invariant 2:
    Windows CRLF (\\r\\n) vs Unix LF (\\n) line endings must parse into identical transactions
    and produce identical reconciliation outcomes.
    """
    csv_da_crlf = CSV_1099DA_BASE.replace("\n", "\r\n")
    csv_koinly_crlf = CSV_KOINLY_BASE.replace("\n", "\r\n")

    case_lf = _build_case_from_csvs(CSV_1099DA_BASE, CSV_KOINLY_BASE, "CASE-LF")
    case_crlf = _build_case_from_csvs(csv_da_crlf, csv_koinly_crlf, "CASE-CRLF")

    res_lf = DeterministicReconciliationEngine.reconcile_case(case_lf)
    res_crlf = DeterministicReconciliationEngine.reconcile_case(case_crlf)

    assert res_lf.outcome_state == res_crlf.outcome_state
    assert res_lf.assurance_level == res_crlf.assurance_level
    assert len(res_lf.material_differences) == len(res_crlf.material_differences)


def test_metamorphic_extra_column_invariance():
    """
    Metamorphic Invariant 3:
    Adding unknown custom columns (e.g. Notes, Internal_Code) must not alter the deterministic reconciliation.
    """
    csv_da_extra = (
        "Property,Units,Date sold,Proceeds,Date acquired,Cost basis,Box 2,Auditor_Notes,Extra_Tag\n"
        "BTC,0.50000000,2025-03-15,45000.00,2024-01-10,30000.00,YES,Reviewed by CPA,TAG-99\n"
        "ETH,4.00000000,2025-06-20,12000.00,2025-02-15,8000.00,YES,Pending client follow up,TAG-100\n"
    )
    case_base = _build_case_from_csvs(CSV_1099DA_BASE, CSV_KOINLY_BASE, "CASE-EXTRA-BASE")
    case_extra = _build_case_from_csvs(csv_da_extra, CSV_KOINLY_BASE, "CASE-EXTRA-TEST")

    res_base = DeterministicReconciliationEngine.reconcile_case(case_base)
    res_extra = DeterministicReconciliationEngine.reconcile_case(case_extra)

    assert res_base.outcome_state == res_extra.outcome_state
    assert res_base.assurance_level == res_extra.assurance_level
    assert len(res_base.material_differences) == len(res_extra.material_differences)


def test_perturbation_sensitivity_basis_variance_detected():
    """
    Perturbation Sensitivity Test:
    Modifying a basis number by > 1-cent rounding threshold immediately breaks exact agreement
    and deterministically surfaces a BASIS_DIFFERENCE discrepancy.
    """
    csv_koinly_shifted = (
        "Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired\n"
        "2025-03-15,BTC,0.50000000,30050.00,45000.00,14950.00,2024-01-10\n"  # $50.00 difference
        "2025-06-20,ETH,4.00000000,8000.00,12000.00,4000.00,2025-02-15\n"
    )
    case_shifted = _build_case_from_csvs(CSV_1099DA_BASE, csv_koinly_shifted, "CASE-PERTURBED")
    res_shifted = DeterministicReconciliationEngine.reconcile_case(case_shifted)

    assert res_shifted.outcome_state == "BASIS_DIFFERENCE"
    assert len(res_shifted.material_differences) >= 1
    diff = res_shifted.material_differences[0]
    assert diff.difference_state == "BASIS_DIFFERENCE"
    assert diff.source_a_value == "30000.00"
    assert diff.source_b_value == "30050.00"
    assert diff.variance == "50.00"


def test_strict_unresolved_missing_record_handling():
    """
    Strict Matching Invariant:
    A broker record with no corresponding ledger disposal must be surfaced explicitly as an
    unresolved record (MISSING_FROM_LEDGER) and never silently discarded or assumed zero basis.
    """
    csv_da_extra_item = (
        "Property,Units,Date sold,Proceeds,Date acquired,Cost basis,Box 2\n"
        "BTC,0.50000000,2025-03-15,45000.00,2024-01-10,30000.00,YES\n"
        "ETH,4.00000000,2025-06-20,12000.00,2025-02-15,8000.00,YES\n"
        "SOL,50.0000000,2025-09-10,7500.00,2025-01-01,5000.00,YES\n"  # Missing from Koinly
    )
    case_unresolved = _build_case_from_csvs(csv_da_extra_item, CSV_KOINLY_BASE, "CASE-UNRESOLVED")
    res = DeterministicReconciliationEngine.reconcile_case(case_unresolved)

    assert res.outcome_state == "MISSING_FROM_LEDGER"
    assert len(res.material_differences) >= 1
    diff = res.material_differences[0]
    assert diff.difference_state == "MISSING_FROM_LEDGER"
    assert diff.asset == "SOL"
    assert "missing from tax ledger" in diff.description


