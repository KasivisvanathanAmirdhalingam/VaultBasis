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
