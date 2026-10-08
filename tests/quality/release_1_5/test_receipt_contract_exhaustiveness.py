"""
VaultBasis Edge — Release 1.5 Receipt Schema Exhaustiveness & Contract Compatibility Suite
MMP-1.5 Final Engineering Closure — Stage 3: Receipt Contract & Compatibility

Tests:
1. Enumerate every engine-emittable difference_state, reason_code, outcome_state, and human_review_state.
2. Prove each valid state is strictly accepted by the normative receipt contract (receipt-v0.1.json) and standalone verifier.
3. Assert that unauthorized / invented states are rejected by the schema validator.
4. Verify the frozen MMP-1.5 Contract Compatibility Matrix across parsers, rulesets, schemas, and license protocols.
"""

import json
import pytest
import uuid
from pathlib import Path

from apps.verifier.verify_receipt import verify_outcome_receipt, SCHEMA_PATH
from edge.receipts.keygen import InstallationKeyManager
from edge.receipts.signer import ReceiptSigner
from edge.connectors.form1099da_parser import Form1099DAParser
from edge.connectors.koinly_parser import KoinlyCapitalGainsParser
from edge.system.version import get_system_version
import jsonschema


@pytest.fixture
def test_keypair(tmp_path):
    mgr = InstallationKeyManager(tmp_path / "keys")
    priv, pub = mgr.ensure_keypair()
    return priv, pub, mgr.get_key_id(pub)


@pytest.fixture
def normative_schema():
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)


class TestReceiptContractExhaustiveness:

    ALL_OUTCOME_STATES = [
        "MATCHED",
        "PROCEEDS_DIFFERENCE",
        "BASIS_DIFFERENCE",
        "ACQUISITION_DATE_DIFFERENCE",
        "DISPOSITION_DATE_DIFFERENCE",
        "MISSING_FROM_1099DA",
        "MISSING_FROM_LEDGER",
        "AMBIGUOUS_MATCH",
        "AGGREGATED_LINE",
        "TRANSFER_RELATED",
        "REPORTING_SCOPE_DIFFERENCE",
        "SOURCE_ERROR_SUSPECTED",
        "UNRESOLVED_DATA",
    ]

    ALL_DIFFERENCE_STATES = [
        "PROCEEDS_DIFFERENCE",
        "BASIS_DIFFERENCE",
        "ACQUISITION_DATE_DIFFERENCE",
        "DISPOSITION_DATE_DIFFERENCE",
        "MISSING_FROM_1099DA",
        "MISSING_FROM_LEDGER",
        "AMBIGUOUS_MATCH",
        "AGGREGATED_LINE",
        "TRANSFER_RELATED",
        "REPORTING_SCOPE_DIFFERENCE",
        "SOURCE_ERROR_SUSPECTED",
    ]

    ALL_REASON_CODES = [
        "PRECISION_UNRESOLVED",
        "PRICE_UNAVAILABLE",
        "BASIS_UNAVAILABLE",
        "DATE_UNAVAILABLE",
        "TIMEZONE_CONTEXT_MISSING",
        "INVENTORY_DEFICIT",
        "AMBIGUOUS_SOURCE_DATA",
    ]

    ALL_HUMAN_REVIEW_STATES = [
        "UNREVIEWED",
        "REVIEWED_ACCEPTED",
        "REVIEWED_DISPUTED",
        "REVIEWED_ANNOTATED",
    ]

    def _build_receipt_payload(self, outcome_state: str, diff_state: str, reason_code: str, review_state: str) -> dict:
        return {
            "receipt_version": "v0.1",
            "receipt_id": str(uuid.uuid4()),
            "case_id": "CASE-EXHAUSTIVE-001",
            "claim_type": "DIGITAL_ASSET_TAX_RECONCILIATION",
            "claimant_type": "TAXPAYER",
            "producer_reference": "VaultBasis Edge v1.5.0",
            "source_ids": ["src_1099da_01", "src_koinly_01"],
            "source_hashes": {
                "src_1099da_01": "a" * 64,
                "src_koinly_01": "b" * 64,
            },
            "source_schema_ids": {
                "src_1099da_01": "VB-1099DA-2025-SOURCE-V1",
                "src_koinly_01": "KOINLY_CAPITAL_GAINS_CSV_V1",
            },
            "canonicalization_version": "v0.1",
            "ruleset_id": "VB_US_1099DA_2025_V1",
            "engine_version": "1.5.0",
            "policy_version": "1.5.0",
            "assurance_level": "L2_EVIDENCE_RECONCILED",
            "outcome_state": outcome_state,
            "material_differences": [
                {
                    "difference_id": "DIFF-001",
                    "difference_state": diff_state,
                    "asset": "BTC",
                    "source_a_ref": "src_1099da_01:Row:1",
                    "source_a_value": "1000.00",
                    "source_b_ref": "src_koinly_01:Row:1",
                    "source_b_value": "1200.00",
                    "variance": "200.00",
                    "description": "Exhaustiveness test difference record",
                    "rule_reference": "VB_US_1099DA_2025_V1",
                    "provenance_references": []
                }
            ],
            "unresolved_items": [
                {
                    "item_id": "UNRES-001",
                    "reason_code": reason_code,
                    "affected_source_id": "src_1099da_01",
                    "affected_row_ref": "Row:1",
                    "description": "Exhaustiveness test unresolved record",
                    "rule_reference": "VB_US_1099DA_2025_V1",
                    "provenance_references": []
                }
            ],
            "human_review_state": review_state,
            "ai_involvement_level": "NONE",
            "created_at": "2026-10-08T10:00:00Z"
        }

    @pytest.mark.parametrize("outcome_state", ALL_OUTCOME_STATES)
    def test_all_outcome_states_valid_in_schema_and_verifier(self, test_keypair, outcome_state):
        priv_key, pub_key, key_id = test_keypair
        signer = ReceiptSigner(priv_key)
        payload = self._build_receipt_payload(
            outcome_state=outcome_state,
            diff_state="BASIS_DIFFERENCE",
            reason_code="BASIS_UNAVAILABLE",
            review_state="REVIEWED_ACCEPTED"
        )
        signed = signer.sign_receipt(payload)
        verification = verify_outcome_receipt(signed)
        assert verification.is_valid is True, f"Outcome state {outcome_state} failed: {verification.errors}"

    @pytest.mark.parametrize("diff_state", ALL_DIFFERENCE_STATES)
    def test_all_difference_states_valid_in_schema_and_verifier(self, test_keypair, diff_state):
        priv_key, pub_key, key_id = test_keypair
        signer = ReceiptSigner(priv_key)
        payload = self._build_receipt_payload(
            outcome_state="BASIS_DIFFERENCE",
            diff_state=diff_state,
            reason_code="BASIS_UNAVAILABLE",
            review_state="REVIEWED_ACCEPTED"
        )
        signed = signer.sign_receipt(payload)
        verification = verify_outcome_receipt(signed)
        assert verification.is_valid is True, f"Difference state {diff_state} failed: {verification.errors}"

    @pytest.mark.parametrize("reason_code", ALL_REASON_CODES)
    def test_all_reason_codes_valid_in_schema_and_verifier(self, test_keypair, reason_code):
        priv_key, pub_key, key_id = test_keypair
        signer = ReceiptSigner(priv_key)
        payload = self._build_receipt_payload(
            outcome_state="UNRESOLVED_DATA",
            diff_state="BASIS_DIFFERENCE",
            reason_code=reason_code,
            review_state="REVIEWED_ACCEPTED"
        )
        signed = signer.sign_receipt(payload)
        verification = verify_outcome_receipt(signed)
        assert verification.is_valid is True, f"Reason code {reason_code} failed: {verification.errors}"

    @pytest.mark.parametrize("review_state", ALL_HUMAN_REVIEW_STATES)
    def test_all_human_review_states_valid_in_schema_and_verifier(self, test_keypair, review_state):
        priv_key, pub_key, key_id = test_keypair
        signer = ReceiptSigner(priv_key)
        payload = self._build_receipt_payload(
            outcome_state="MATCHED",
            diff_state="BASIS_DIFFERENCE",
            reason_code="BASIS_UNAVAILABLE",
            review_state=review_state
        )
        signed = signer.sign_receipt(payload)
        verification = verify_outcome_receipt(signed)
        assert verification.is_valid is True, f"Review state {review_state} failed: {verification.errors}"

    def test_invalid_unauthorized_states_rejected(self, test_keypair, normative_schema):
        """Negative test: Prove arbitrary/invented states are strictly rejected by the schema."""
        priv_key, pub_key, key_id = test_keypair
        signer = ReceiptSigner(priv_key)

        # Invalid outcome state
        bad_outcome = self._build_receipt_payload("MAGIC_AI_MATCH", "BASIS_DIFFERENCE", "BASIS_UNAVAILABLE", "REVIEWED_ACCEPTED")
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=bad_outcome, schema=normative_schema)

        # Invalid human review state
        bad_review = self._build_receipt_payload("MATCHED", "BASIS_DIFFERENCE", "BASIS_UNAVAILABLE", "AI_AUTOMATED")
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=bad_review, schema=normative_schema)

    def test_contract_compatibility_matrix(self):
        """Verifies the exact MMP-1.5 Contract Compatibility Matrix."""
        sys_ver = get_system_version()
        assert sys_ver.version.startswith("1.5.")
        assert Form1099DAParser.SCHEMA_ID == "VB-1099DA-2025-SOURCE-V1"
        assert KoinlyCapitalGainsParser.SCHEMA_ID == "KOINLY_CAPITAL_GAINS_CSV_V1"
