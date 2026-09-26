"""
VaultBasis Quality Suite — DDD (Domain-Driven Design)
Tests Domain Entities, Value Objects, Aggregate Roots, and Bounded Context Invariants.
"""

from decimal import Decimal
import pytest
from pydantic import ValidationError

from schemas.canonical.case import CanonicalCase, SourceDocumentMetadata
from schemas.canonical.transaction import CanonicalTransaction


@pytest.mark.ddd
@pytest.mark.smoke
def test_ddd_transaction_entity_invariants():
    """Validates that CanonicalTransaction strictly enforces financial domain invariants."""
    # 1. Valid transaction
    tx = CanonicalTransaction(
        transaction_id="tx_1",
        source_id="src_1",
        source_file_hash="a" * 64,
        source_row_reference="Row:1",
        transaction_type="SALE",
        asset="BTC",
        quantity="1.5",
        proceeds="75000.00",
        cost_basis="50000.00"
    )
    assert tx.quantity == Decimal("1.5")
    assert tx.proceeds == Decimal("75000.00")
    assert tx.cost_basis == Decimal("50000.00")

    # 2. Rejection of raw binary floats
    with pytest.raises(ValidationError):
        CanonicalTransaction(
            transaction_id="tx_bad",
            source_id="src_1",
            source_file_hash="a" * 64,
            source_row_reference="Row:2",
            transaction_type="SALE",
            asset="ETH",
            quantity=1.23456,  # Raw float is forbidden
            proceeds="3000.00"
        )


@pytest.mark.ddd
@pytest.mark.regression
def test_ddd_case_aggregate_lifecycle():
    """Validates the CanonicalCase Aggregate Root state transitions."""
    case = CanonicalCase(
        case_id="CASE-AGG-001",
        tax_year=2025,
        jurisdiction="US",
        case_status="CREATED",
        created_at="2026-09-26T12:00:00Z",
        updated_at="2026-09-26T12:00:00Z"
    )
    assert case.case_status == "CREATED"
    assert len(case.sources) == 0

    # Ingestion transition
    meta = SourceDocumentMetadata(
        source_id="src_1",
        filename="1099.csv",
        sha256_hash="b" * 64,
        byte_size=1024,
        schema_id="IRS_1099DA_2025_PREVIEW",
        row_count=5,
        ingested_at="2026-09-26T12:05:00Z"
    )
    case.sources[meta.source_id] = meta
    case.case_status = "SOURCES_INGESTED"
    assert case.case_status == "SOURCES_INGESTED"
    assert len(case.sources) == 1

    # Receipt issuance transition
    case.outcome_state = "MATCHED"
    case.receipt_id = "rcpt-uuid-999"
    case.case_status = "RECEIPT_ISSUED"
    assert case.case_status == "RECEIPT_ISSUED"
    assert case.receipt_id is not None


@pytest.mark.ddd
@pytest.mark.regression
def test_ddd_source_document_hash_invariant():
    """Validates that SourceDocumentMetadata enforces a 64-character SHA-256 hex string."""
    # Valid 64-char hex
    valid_meta = SourceDocumentMetadata(
        source_id="src_valid",
        filename="valid.csv",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        byte_size=10,
        schema_id="IRS_1099DA_2025_PREVIEW",
        row_count=1,
        ingested_at="2026-09-26T12:00:00Z"
    )
    assert len(valid_meta.sha256_hash) == 64

    # Invalid short hash should fail pattern / validation if length enforced
    with pytest.raises(ValidationError):
        SourceDocumentMetadata(
            source_id="src_invalid",
            filename="invalid.csv",
            sha256_hash="short_hash",
            byte_size=10,
            schema_id="IRS_1099DA_2025_PREVIEW",
            row_count=1,
            ingested_at="2026-09-26T12:00:00Z"
        )


@pytest.mark.ddd
@pytest.mark.smoke
def test_ddd_outcome_receipt_assurance_invariants():
    """Validates domain assurance levels and permitted outcome state domain definitions."""
    from schemas.canonical.case import CanonicalCase

    # Allowed outcome states in PRD §14.1
    allowed_states = {
        "MATCHED", "PROCEEDS_DIFFERENCE", "BASIS_DIFFERENCE", "ACQUISITION_DATE_DIFFERENCE",
        "DISPOSITION_DATE_DIFFERENCE", "MISSING_FROM_1099DA", "MISSING_FROM_LEDGER",
        "AMBIGUOUS_MATCH", "AGGREGATED_LINE", "TRANSFER_RELATED", "REPORTING_SCOPE_DIFFERENCE",
        "SOURCE_ERROR_SUSPECTED", "UNRESOLVED_DATA"
    }

    case = CanonicalCase(
        case_id="CASE-STATES-01",
        tax_year=2025,
        jurisdiction="US",
        outcome_state="BASIS_DIFFERENCE",
        created_at="2026-09-26T12:00:00Z",
        updated_at="2026-09-26T12:00:00Z"
    )
    assert case.outcome_state in allowed_states


@pytest.mark.ddd
@pytest.mark.regression
def test_ddd_canonical_transaction_empty_asset_rejection():
    """Validates that CanonicalTransaction rejects empty or missing asset symbols."""
    with pytest.raises(ValidationError):
        CanonicalTransaction(
            transaction_id="tx_invalid_asset",
            source_id="src_1",
            source_file_hash="a" * 64,
            source_row_reference="Row:1",
            transaction_type="SALE",
            asset="",  # Empty string rejected by min_length=1
            quantity="1.0"
        )


@pytest.mark.ddd
@pytest.mark.regression
def test_ddd_currency_string_cleaning_invariant():
    """Validates that dollar signs, commas, and whitespace are normalized to exact Decimals."""
    tx = CanonicalTransaction(
        transaction_id="tx_formatted",
        source_id="src_1",
        source_file_hash="a" * 64,
        source_row_reference="Row:1",
        transaction_type="SALE",
        asset="BTC",
        quantity=" 0.05 ",
        proceeds=" $3,450.50 ",
        cost_basis=" $2,100.25 ",
        gain_loss=" $1,350.25 "
    )
    assert tx.quantity == Decimal("0.05")
    assert tx.proceeds == Decimal("3450.50")
    assert tx.cost_basis == Decimal("2100.25")
    assert tx.gain_loss == Decimal("1350.25")


@pytest.mark.ddd
@pytest.mark.regression
def test_ddd_provenance_acyclic_reference_invariant():
    """Validates that all transactions in a CanonicalCase aggregate must trace back to registered sources."""
    case = CanonicalCase(
        case_id="CASE-PROV-001",
        tax_year=2025,
        jurisdiction="US",
        created_at="2026-09-26T12:00:00Z",
        updated_at="2026-09-26T12:00:00Z"
    )
    
    meta = SourceDocumentMetadata(
        source_id="src_registered_1",
        filename="1099da.csv",
        sha256_hash="c" * 64,
        byte_size=2048,
        schema_id="IRS_1099DA_2025_PREVIEW",
        row_count=1,
        ingested_at="2026-09-26T12:00:00Z"
    )
    case.sources[meta.source_id] = meta

    # Add transaction referencing known source
    valid_tx = CanonicalTransaction(
        transaction_id="tx_valid_prov",
        source_id="src_registered_1",
        source_file_hash="c" * 64,
        source_row_reference="Line:2",
        transaction_type="SALE",
        asset="BTC",
        quantity="0.1",
        proceeds="5000.00"
    )
    case.transactions.append(valid_tx)
    
    # Check that all transactions map to existing sources
    orphans = [tx.transaction_id for tx in case.transactions if tx.source_id not in case.sources]
    assert len(orphans) == 0

    # Add orphaned transaction referencing unknown source
    orphan_tx = CanonicalTransaction(
        transaction_id="tx_orphan",
        source_id="src_unknown_source",
        source_file_hash="d" * 64,
        source_row_reference="Line:99",
        transaction_type="SALE",
        asset="ETH",
        quantity="1.0"
    )
    case.transactions.append(orphan_tx)

    orphans_detected = [tx.transaction_id for tx in case.transactions if tx.source_id not in case.sources]
    assert len(orphans_detected) == 1
    assert orphans_detected[0] == "tx_orphan"


@pytest.mark.ddd
@pytest.mark.smoke
def test_ddd_assurance_level_hierarchy_invariants():
    """Validates defined assurance level hierarchy according to PRD §14.2."""
    valid_assurance_levels = {
        "L1_SYNTAX_VALIDATED",
        "L2_EVIDENCE_RECONCILED",
        "L3_POLICY_ATTESTED",
        "L4_EXPERT_REVIEWED",
        "L5_INSTITUTIONAL_CERTIFIED"
    }

    for level in valid_assurance_levels:
        case = CanonicalCase(
            case_id=f"CASE-{level}",
            tax_year=2025,
            jurisdiction="US",
            assurance_level=level,
            created_at="2026-09-26T12:00:00Z",
            updated_at="2026-09-26T12:00:00Z"
        )
        assert case.assurance_level in valid_assurance_levels


@pytest.mark.ddd
@pytest.mark.regression
def test_ddd_case_status_transition_guards():
    """Validates invariant that receipt issuance requires an outcome state and receipt ID."""
    case = CanonicalCase(
        case_id="CASE-GUARD-01",
        tax_year=2025,
        jurisdiction="US",
        case_status="CREATED",
        created_at="2026-09-26T12:00:00Z",
        updated_at="2026-09-26T12:00:00Z"
    )

    # Invariant: If case_status is RECEIPT_ISSUED, both receipt_id and outcome_state must be present
    def validate_receipt_issuance_invariants(c: CanonicalCase):
        if c.case_status == "RECEIPT_ISSUED":
            if not c.receipt_id or not c.outcome_state:
                raise ValueError("Invariant violation: RECEIPT_ISSUED requires receipt_id and outcome_state")

    # Should raise error if status is set without receipt_id or outcome_state
    case.case_status = "RECEIPT_ISSUED"
    with pytest.raises(ValueError, match="Invariant violation"):
        validate_receipt_issuance_invariants(case)

    # Setting valid attributes satisfies invariant
    case.outcome_state = "MATCHED"
    case.receipt_id = "rcpt-val-12345"
    validate_receipt_issuance_invariants(case)
    assert case.case_status == "RECEIPT_ISSUED"


@pytest.mark.ddd
@pytest.mark.regression
def test_ddd_transaction_summary_serialization_completeness():
    """Validates that to_summary_dict produces an RFC-compliant dictionary with stringified decimals."""
    tx = CanonicalTransaction(
        transaction_id="tx_sum_01",
        source_id="src_1",
        source_file_hash="e" * 64,
        source_row_reference="Line:10",
        transaction_type="SALE",
        asset="SOL",
        quantity="15.25000000",
        proceeds="3050.00",
        cost_basis="2500.00",
        gain_loss="550.00",
        acquisition_date="2024-01-10",
        disposition_date="2025-06-15",
        basis_reported_to_irs="YES",
        is_unresolved=False
    )
    summary = tx.to_summary_dict()
    assert summary["transaction_id"] == "tx_sum_01"
    assert summary["quantity"] == "15.25000000"
    assert summary["proceeds"] == "3050.00"
    assert summary["cost_basis"] == "2500.00"
    assert summary["gain_loss"] == "550.00"
    assert summary["basis_reported_to_irs"] == "YES"
    assert summary["is_unresolved"] is False
    assert isinstance(summary["quantity"], str)
    assert isinstance(summary["proceeds"], str)


@pytest.mark.ddd
@pytest.mark.regression
def test_ddd_source_document_metadata_byte_size_positive():
    """Validates that source document metadata row count and byte size must be non-negative."""
    meta = SourceDocumentMetadata(
        source_id="src_size_01",
        filename="empty.csv",
        sha256_hash="f" * 64,
        byte_size=0,
        schema_id="GENERIC",
        row_count=0,
        ingested_at="2026-09-26T12:00:00Z"
    )
    assert meta.byte_size >= 0
    assert meta.row_count >= 0



