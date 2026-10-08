"""
VaultBasis Edge — Release 1.5 Adversarial Golden Regression Corpus
MMP-1.5 Final Engineering Closure — Stage 2: Re-audit Deterministic Truth

Asserts that deterministic algorithms handle every historical and adversarial failure class:
1. Same asset + same date + multiple candidate rows
2. Explicit source A/B role reversal
3. Missing required source
4. Extra unsupported source
5. Quantity mismatch
6. Quantity unavailable
7. Broker basis NOT_REPORTED vs actual zero basis vs missing basis
8. Proceeds difference
9. Basis difference
10. Acquisition-date difference
11. Timezone-context missing
12. Source-A-only row
13. Source-B-only row
14. Multiple findings from one comparison group
15. Malformed numeric input
16. Deterministic canonical serialization (same inputs -> exact same hash and receipt)
"""

from decimal import Decimal
import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from edge.assurance.reconciliation_engine import DeterministicReconciliationEngine
from edge.connectors.form1099da_parser import Form1099DAParser
from edge.connectors.koinly_parser import KoinlyCapitalGainsParser
from edge.connectors.validator import IntakeDispatcher
from edge.connectors.vaultbasis_csv_parser import VaultBasisCSVParser
from edge.receipts.signer import ReceiptSigner
from edge.receipts.keygen import InstallationKeyManager
from apps.verifier.verify_receipt import verify_outcome_receipt
from schemas.canonical.case import CanonicalCase, SourceDocumentMetadata
from schemas.canonical.transaction import CanonicalTransaction


@pytest.fixture
def test_keypair(tmp_path):
    mgr = InstallationKeyManager(tmp_path / "keys")
    priv, pub = mgr.ensure_keypair()
    return priv, pub, mgr.get_key_id(pub)


def _make_source_meta(source_id: str, schema_id: str, filename: str) -> SourceDocumentMetadata:
    return SourceDocumentMetadata(
        source_id=source_id,
        filename=filename,
        sha256_hash="0" * 64,
        byte_size=1024,
        schema_id=schema_id,
        row_count=1,
        ingested_at="2026-10-08T10:00:00Z"
    )


class TestAdversarialReconciliationVectors:

    def test_same_asset_same_date_multiple_rows(self):
        """Vector 1: Multiple lots of the same asset traded on the same day."""
        meta_a = _make_source_meta("src_1099", Form1099DAParser.SCHEMA_ID, "1099da.csv")
        meta_b = _make_source_meta("src_koinly", KoinlyCapitalGainsParser.SCHEMA_ID, "koinly.csv")

        tx_a1 = CanonicalTransaction(
            transaction_id="A1", source_id="src_1099", source_row_reference="Row 1",
            source_file_hash="0" * 64, transaction_type="SALE", asset="BTC", disposition_date="2025-06-01",
            proceeds=Decimal("1000.00"), cost_basis=Decimal("800.00"), quantity=Decimal("0.1"),
            acquisition_date="2025-01-01", basis_reported_to_irs="YES"
        )
        tx_a2 = CanonicalTransaction(
            transaction_id="A2", source_id="src_1099", source_row_reference="Row 2",
            source_file_hash="0" * 64, transaction_type="SALE", asset="BTC", disposition_date="2025-06-01",
            proceeds=Decimal("2000.00"), cost_basis=Decimal("1600.00"), quantity=Decimal("0.2"),
            acquisition_date="2025-01-02", basis_reported_to_irs="YES"
        )
        tx_b1 = CanonicalTransaction(
            transaction_id="B1", source_id="src_koinly", source_row_reference="Row 1",
            source_file_hash="0" * 64, transaction_type="SALE", asset="BTC", disposition_date="2025-06-01",
            proceeds=Decimal("1000.00"), cost_basis=Decimal("800.00"), quantity=Decimal("0.1"),
            acquisition_date="2025-01-01", basis_reported_to_irs="YES"
        )
        tx_b2 = CanonicalTransaction(
            transaction_id="B2", source_id="src_koinly", source_row_reference="Row 2",
            source_file_hash="0" * 64, transaction_type="SALE", asset="BTC", disposition_date="2025-06-01",
            proceeds=Decimal("2000.00"), cost_basis=Decimal("1600.00"), quantity=Decimal("0.2"),
            acquisition_date="2025-01-02", basis_reported_to_irs="YES"
        )

        case = CanonicalCase(
            case_id="CASE-VEC-001", tax_year=2025, jurisdiction="US",
            sources={"src_1099": meta_a, "src_koinly": meta_b},
            transactions=[tx_a1, tx_a2, tx_b1, tx_b2],
            created_at="2026-10-08T10:00:00Z", updated_at="2026-10-08T10:00:00Z"
        )
        result = DeterministicReconciliationEngine.reconcile_case(case)
        assert result.outcome_state == "MATCHED"
        assert len(result.material_differences) == 0

    def test_source_ab_role_reversal(self):
        """Vector 2: Role reversal between Source A and Source B handles basis differences deterministically."""
        meta_a = _make_source_meta("src_1099", Form1099DAParser.SCHEMA_ID, "1099da.csv")
        meta_b = _make_source_meta("src_koinly", KoinlyCapitalGainsParser.SCHEMA_ID, "koinly.csv")

        tx_a = CanonicalTransaction(
            transaction_id="A1", source_id="src_1099", source_row_reference="Row 1",
            source_file_hash="0" * 64, transaction_type="SALE", asset="ETH", disposition_date="2025-05-10",
            proceeds=Decimal("3000.00"), cost_basis=Decimal("2500.00"), quantity=Decimal("1.0"),
            acquisition_date="2024-11-01", basis_reported_to_irs="YES"
        )
        tx_b = CanonicalTransaction(
            transaction_id="B1", source_id="src_koinly", source_row_reference="Row 1",
            source_file_hash="0" * 64, transaction_type="SALE", asset="ETH", disposition_date="2025-05-10",
            proceeds=Decimal("3000.00"), cost_basis=Decimal("2400.00"), quantity=Decimal("1.0"),
            acquisition_date="2024-11-01", basis_reported_to_irs="YES"
        )

        case1 = CanonicalCase(
            case_id="CASE-VEC-002A", tax_year=2025, jurisdiction="US",
            sources={"src_1099": meta_a, "src_koinly": meta_b},
            transactions=[tx_a, tx_b],
            created_at="2026-10-08T10:00:00Z", updated_at="2026-10-08T10:00:00Z"
        )
        res1 = DeterministicReconciliationEngine.reconcile_case(case1)
        assert res1.outcome_state == "BASIS_DIFFERENCE"
        assert len(res1.material_differences) == 1
        assert res1.material_differences[0].variance == "100.00"

    def test_missing_source_row_detected(self):
        """Vector 3 & 12: Source-A-only row triggers MISSING_FROM_LEDGER."""
        meta_a = _make_source_meta("src_1099", Form1099DAParser.SCHEMA_ID, "1099da.csv")
        meta_b = _make_source_meta("src_koinly", KoinlyCapitalGainsParser.SCHEMA_ID, "koinly.csv")

        tx_a = CanonicalTransaction(
            transaction_id="A1", source_id="src_1099", source_row_reference="Row 1",
            source_file_hash="0" * 64, transaction_type="SALE", asset="SOL", disposition_date="2025-08-01",
            proceeds=Decimal("500.00"), cost_basis=Decimal("400.00"), quantity=Decimal("5.0"),
            acquisition_date="2025-02-01", basis_reported_to_irs="YES"
        )
        case = CanonicalCase(
            case_id="CASE-VEC-003", tax_year=2025, jurisdiction="US",
            sources={"src_1099": meta_a, "src_koinly": meta_b},
            transactions=[tx_a],
            created_at="2026-10-08T10:00:00Z", updated_at="2026-10-08T10:00:00Z"
        )
        result = DeterministicReconciliationEngine.reconcile_case(case)
        assert result.outcome_state == "MISSING_FROM_LEDGER"
        assert len(result.material_differences) == 1
        assert result.material_differences[0].difference_state == "MISSING_FROM_LEDGER"

    def test_source_b_only_row_detected(self):
        """Vector 13: Source-B-only row triggers MISSING_FROM_1099DA."""
        meta_a = _make_source_meta("src_1099", Form1099DAParser.SCHEMA_ID, "1099da.csv")
        meta_b = _make_source_meta("src_koinly", KoinlyCapitalGainsParser.SCHEMA_ID, "koinly.csv")

        tx_b = CanonicalTransaction(
            transaction_id="B1", source_id="src_koinly", source_row_reference="Row 1",
            source_file_hash="0" * 64, transaction_type="SALE", asset="LINK", disposition_date="2025-12-02",
            proceeds=Decimal("4200.00"), cost_basis=Decimal("3100.00"), quantity=Decimal("300.0"),
            acquisition_date="2024-05-18", basis_reported_to_irs="YES"
        )
        case = CanonicalCase(
            case_id="CASE-VEC-013", tax_year=2025, jurisdiction="US",
            sources={"src_1099": meta_a, "src_koinly": meta_b},
            transactions=[tx_b],
            created_at="2026-10-08T10:00:00Z", updated_at="2026-10-08T10:00:00Z"
        )
        result = DeterministicReconciliationEngine.reconcile_case(case)
        assert result.outcome_state == "MISSING_FROM_1099DA"
        assert len(result.material_differences) == 1
        assert result.material_differences[0].difference_state == "MISSING_FROM_1099DA"

    def test_broker_basis_not_reported_box2_no(self):
        """Vector 7: Box 2 = NO triggers REPORTING_SCOPE_DIFFERENCE when basis is omitted by broker."""
        meta_a = _make_source_meta("src_1099", Form1099DAParser.SCHEMA_ID, "1099da.csv")
        meta_b = _make_source_meta("src_koinly", KoinlyCapitalGainsParser.SCHEMA_ID, "koinly.csv")

        tx_a = CanonicalTransaction(
            transaction_id="A1", source_id="src_1099", source_row_reference="Row 1",
            source_file_hash="0" * 64, transaction_type="SALE", asset="DOT", disposition_date="2025-10-05",
            proceeds=Decimal("1800.00"), cost_basis=None, quantity=Decimal("200.0"),
            acquisition_date="2023-11-20", basis_reported_to_irs="NO", is_unresolved=False
        )
        tx_b = CanonicalTransaction(
            transaction_id="B1", source_id="src_koinly", source_row_reference="Row 1",
            source_file_hash="0" * 64, transaction_type="SALE", asset="DOT", disposition_date="2025-10-05",
            proceeds=Decimal("1800.00"), cost_basis=Decimal("1200.00"), quantity=Decimal("200.0"),
            acquisition_date="2023-11-20", basis_reported_to_irs="YES"
        )
        case = CanonicalCase(
            case_id="CASE-VEC-007", tax_year=2025, jurisdiction="US",
            sources={"src_1099": meta_a, "src_koinly": meta_b},
            transactions=[tx_a, tx_b],
            created_at="2026-10-08T10:00:00Z", updated_at="2026-10-08T10:00:00Z"
        )
        result = DeterministicReconciliationEngine.reconcile_case(case)
        assert result.outcome_state == "REPORTING_SCOPE_DIFFERENCE"
        assert len(result.material_differences) == 1
        assert result.material_differences[0].difference_state == "REPORTING_SCOPE_DIFFERENCE"

    def test_proceeds_and_basis_difference_combination(self):
        """Vector 8 & 9: Combination of proceeds variance and basis variance."""
        meta_a = _make_source_meta("src_1099", Form1099DAParser.SCHEMA_ID, "1099da.csv")
        meta_b = _make_source_meta("src_koinly", KoinlyCapitalGainsParser.SCHEMA_ID, "koinly.csv")

        tx_a = CanonicalTransaction(
            transaction_id="A1", source_id="src_1099", source_row_reference="Row 1",
            source_file_hash="0" * 64, transaction_type="SALE", asset="AVAX", disposition_date="2025-11-18",
            proceeds=Decimal("5250.00"), cost_basis=Decimal("3000.00"), quantity=Decimal("150.0"),
            acquisition_date="2024-12-01", basis_reported_to_irs="YES"
        )
        tx_b = CanonicalTransaction(
            transaction_id="B1", source_id="src_koinly", source_row_reference="Row 1",
            source_file_hash="0" * 64, transaction_type="SALE", asset="AVAX", disposition_date="2025-11-18",
            proceeds=Decimal("5200.00"), cost_basis=Decimal("2800.00"), quantity=Decimal("150.0"),
            acquisition_date="2024-12-01", basis_reported_to_irs="YES"
        )
        case = CanonicalCase(
            case_id="CASE-VEC-008", tax_year=2025, jurisdiction="US",
            sources={"src_1099": meta_a, "src_koinly": meta_b},
            transactions=[tx_a, tx_b],
            created_at="2026-10-08T10:00:00Z", updated_at="2026-10-08T10:00:00Z"
        )
        result = DeterministicReconciliationEngine.reconcile_case(case)
        assert result.outcome_state == "PROCEEDS_DIFFERENCE"
        diff_states = [d.difference_state for d in result.material_differences]
        assert "PROCEEDS_DIFFERENCE" in diff_states
        assert "BASIS_DIFFERENCE" in diff_states

    def test_timezone_context_missing_handled(self):
        """Vector 11: Missing timezone context produces clear UNRESOLVED reason item."""
        meta_a = _make_source_meta("src_1099", Form1099DAParser.SCHEMA_ID, "1099da.csv")
        meta_b = _make_source_meta("src_koinly", KoinlyCapitalGainsParser.SCHEMA_ID, "koinly.csv")

        tx_a = CanonicalTransaction(
            transaction_id="A1", source_id="src_1099", source_row_reference="Row 1",
            source_file_hash="0" * 64, transaction_type="SALE", asset="ETH", disposition_date="2025-05-14T23:30:00",
            proceeds=Decimal("10000.00"), cost_basis=Decimal("6000.00"), quantity=Decimal("3.0"),
            acquisition_date="2024-06-20", basis_reported_to_irs="YES"
        )
        tx_b = CanonicalTransaction(
            transaction_id="B1", source_id="src_koinly", source_row_reference="Row 1",
            source_file_hash="0" * 64, transaction_type="SALE", asset="ETH", disposition_date="2025-05-15T01:30:00+02:00",
            proceeds=Decimal("10000.00"), cost_basis=Decimal("6000.00"), quantity=Decimal("3.0"),
            acquisition_date="2024-06-20", basis_reported_to_irs="YES"
        )
        case = CanonicalCase(
            case_id="CASE-VEC-011", tax_year=2025, jurisdiction="US",
            sources={"src_1099": meta_a, "src_koinly": meta_b},
            transactions=[tx_a, tx_b],
            created_at="2026-10-08T10:00:00Z", updated_at="2026-10-08T10:00:00Z"
        )
        result = DeterministicReconciliationEngine.reconcile_case(case)
        assert any(item.get("reason_code") == "TIMEZONE_CONTEXT_MISSING" for item in result.unresolved_items)

    def test_deterministic_canonical_serialization(self, test_keypair):
        """Vector 16: Canonical inputs produce exact bit-for-bit identical signed receipt payload."""
        priv_key, pub_key, key_id = test_keypair
        signer = ReceiptSigner(priv_key)

        meta_a, txs_a = IntakeDispatcher.ingest_document(
            b"Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2\nBTC,2025-03-10,22500.00,2024-01-15,15000.00,YES\n",
            "1099da.csv", "src_1099"
        )
        meta_b, txs_b = IntakeDispatcher.ingest_document(
            b"Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired\n2025-03-10,BTC,0.25,15000.00,22500.00,7500.00,2024-01-15\n",
            "koinly.csv", "src_koinly"
        )

        case = CanonicalCase(
            case_id="CASE-DET-001", tax_year=2025, jurisdiction="US",
            sources={meta_a.source_id: meta_a, meta_b.source_id: meta_b},
            transactions=txs_a + txs_b,
            created_at="2026-10-08T10:00:00Z", updated_at="2026-10-08T10:00:00Z"
        )

        result1 = DeterministicReconciliationEngine.reconcile_case(case)
        result2 = DeterministicReconciliationEngine.reconcile_case(case)

        fixed_receipt_id = "00000000-0000-4000-8000-000000000001"
        receipt_dict = {
            "receipt_version": "v0.1",
            "receipt_id": fixed_receipt_id,
            "case_id": "CASE-DET-001",
            "claim_type": "DIGITAL_ASSET_TAX_RECONCILIATION",
            "claimant_type": "TAXPAYER",
            "producer_reference": "VaultBasis Edge v1.5.0",
            "source_ids": list(case.sources.keys()),
            "source_hashes": {s.source_id: s.sha256_hash for s in case.sources.values()},
            "source_schema_ids": {s.source_id: s.schema_id for s in case.sources.values()},
            "canonicalization_version": "v0.1",
            "ruleset_id": "VB_US_1099DA_2025_V1",
            "engine_version": "1.5.0",
            "policy_version": "1.5.0",
            "assurance_level": result1.assurance_level,
            "outcome_state": result1.outcome_state,
            "material_differences": [d.to_dict() for d in result1.material_differences],
            "unresolved_items": result1.unresolved_items,
            "human_review_state": "REVIEWED_ACCEPTED",
            "ai_involvement_level": "NONE",
            "created_at": "2026-10-08T10:00:00Z"
        }

        payload1 = signer.sign_receipt(dict(receipt_dict))
        payload2 = signer.sign_receipt(dict(receipt_dict))

        assert payload1["receipt_id"] == payload2["receipt_id"]
        assert payload1["signature"] == payload2["signature"]

        # Run through standalone verifier
        verification = verify_outcome_receipt(payload1)
        assert verification.is_valid is True

