"""
VaultBasis Edge — Device Replacement & Offline License Migration Drill Test
MMP-1.5 Productization & Operations Drill

Validates the complete offline cryptographic device replacement procedure:
1. Machine A (Installation A) activates License Rev 1 and creates case evidence + signed receipt.
2. Machine B (Installation B) initializes with a distinct fresh keypair.
3. Offline authority produces License Rev 2 bound to Machine B's installation key ID.
4. Machine B accepts License Rev 2 and unlocks full commercial entitlement.
5. Backed up database from Machine A restores cleanly into Machine B.
6. Historical receipts signed by Machine A remain independently verifiable by the Offline Verifier.
"""

from datetime import datetime, timezone
from pathlib import Path
import pytest

from edge.commercial.engine import evaluate_license_token
from edge.commercial.models import LicenseState, LicenseTier
from edge.commercial.policy import CommercialPolicyService
from edge.commercial.audit import CommercialAuditService
from edge.receipts.keygen import InstallationKeyManager
from edge.receipts.signer import ReceiptSigner
from edge.storage.sqlite_store import SQLiteStore
from apps.verifier.verify_receipt import verify_outcome_receipt
from schemas.canonical.case import CanonicalCase, SourceDocumentMetadata
from tools.issue_license import (
    build_license_payload,
    encode_token_base64,
    generate_commercial_keypair,
    sign_license_payload,
)


def test_device_replacement_and_migration_drill(tmp_path, monkeypatch):
    # 1. Ephemeral Commercial Authority Keypair
    priv_hex, pub_hex = generate_commercial_keypair()
    keyring_override = {"vb_auth_key_1": pub_hex}
    monkeypatch.setattr("edge.commercial.keys.COMMERCIAL_KEYRING", keyring_override)

    # -------------------------------------------------------------------------
    # STAGE 1: Machine A Initial Operation & Case Creation
    # -------------------------------------------------------------------------
    machine_a_dir = tmp_path / "machine_a"
    km_a = InstallationKeyManager(machine_a_dir / "keys")
    priv_a, pub_a = km_a.ensure_keypair()
    key_id_a = km_a.get_key_id(pub_a)

    store_a = SQLiteStore(machine_a_dir / "vaultbasis.db")
    audit_a = CommercialAuditService(store=store_a, installation_id=key_id_a)
    policy_a = CommercialPolicyService(
        store=store_a,
        license_dir=machine_a_dir / "license",
        installation_id=key_id_a,
        audit_service=audit_a,
    )

    # Issue License Rev 1 for Machine A
    payload_r1 = build_license_payload(
        customer_id="Acme CPA Partners",
        tier="PRACTICE",
        max_cases=100,
        valid_days=365,
        license_id="LIC-2026-0042-R1",
        key_id="vb_auth_key_1",
        installation_id=key_id_a,
    )
    envelope_r1 = sign_license_payload(payload_r1, priv_hex)
    token_r1 = encode_token_base64(envelope_r1)

    eval_r1 = policy_a.install_license_token(token_r1)
    assert eval_r1.is_active is True
    assert eval_r1.tier == LicenseTier.PRACTICE

    # Create Case and Sign Receipt on Machine A
    signer_a = ReceiptSigner(priv_a)
    case_a = CanonicalCase(
        case_id="CASE-ACME-001",
        tax_year=2025,
        jurisdiction="US",
        sources={
            "src_1099": SourceDocumentMetadata(
                source_id="src_1099",
                filename="1099da.csv",
                sha256_hash="a" * 64,
                byte_size=100,
                schema_id="VB-1099DA-2025-SOURCE-V1",
                row_count=1,
                ingested_at="2026-10-01T12:00:00Z"
            )
        },
        transactions=[],
        created_at="2026-10-01T12:00:00Z",
        updated_at="2026-10-01T12:00:00Z"
    )
    store_a.save_case(case_a)

    receipt_payload_a = {
        "receipt_version": "v0.1",
        "receipt_id": "11111111-1111-4000-8000-111111111111",
        "case_id": "CASE-ACME-001",
        "claim_type": "DIGITAL_ASSET_TAX_RECONCILIATION",
        "claimant_type": "TAXPAYER",
        "producer_reference": "VaultBasis Edge v1.5.0",
        "source_ids": ["src_1099"],
        "source_hashes": {"src_1099": "a" * 64},
        "source_schema_ids": {"src_1099": "VB-1099DA-2025-SOURCE-V1"},
        "canonicalization_version": "v0.1",
        "ruleset_id": "VB_US_1099DA_2025_R1",
        "engine_version": "1.5.0",
        "policy_version": "1.5.0",
        "assurance_level": "L2_EVIDENCE_RECONCILED",
        "outcome_state": "MATCHED",
        "material_differences": [],
        "unresolved_items": [],
        "human_review_state": "REVIEWED_ACCEPTED",
        "ai_involvement_level": "NONE",
        "created_at": "2026-10-01T12:00:00Z"
    }
    signed_receipt_a = signer_a.sign_receipt(receipt_payload_a)
    store_a.save_receipt("11111111-1111-4000-8000-111111111111", "CASE-ACME-001", signed_receipt_a, revision=1)

    # -------------------------------------------------------------------------
    # STAGE 2: Machine B Fresh Setup (Simulate Replacement Machine)
    # -------------------------------------------------------------------------
    machine_b_dir = tmp_path / "machine_b"
    km_b = InstallationKeyManager(machine_b_dir / "keys")
    priv_b, pub_b = km_b.ensure_keypair()
    key_id_b = km_b.get_key_id(pub_b)
    assert key_id_b != key_id_a, "Machine B must have an isolated new installation key ID"

    store_b = SQLiteStore(machine_b_dir / "vaultbasis.db")
    audit_b = CommercialAuditService(store=store_b, installation_id=key_id_b)
    policy_b = CommercialPolicyService(
        store=store_b,
        license_dir=machine_b_dir / "license",
        installation_id=key_id_b,
        audit_service=audit_b,
    )

    # Initial state on Machine B is unlicensed
    status_b_initial = policy_b.get_status()
    assert status_b_initial["licensed"] is False

    # Old License Rev 1 (bound to Machine A) is rejected on Machine B due to installation ID mismatch
    eval_r1_on_b = policy_b.install_license_token(token_r1)
    assert eval_r1_on_b.is_active is False
    assert eval_r1_on_b.state == LicenseState.INSTALLATION_MISMATCH

    # -------------------------------------------------------------------------
    # STAGE 3: Issue Replacement License Rev 2 Bound to Machine B
    # -------------------------------------------------------------------------
    payload_r2 = build_license_payload(
        customer_id="Acme CPA Partners",
        tier="PRACTICE",
        max_cases=100,
        valid_days=365,
        license_id="LIC-2026-0042-R2",
        key_id="vb_auth_key_1",
        installation_id=key_id_b,
    )
    envelope_r2 = sign_license_payload(payload_r2, priv_hex)
    token_r2 = encode_token_base64(envelope_r2)

    eval_r2 = policy_b.install_license_token(token_r2)
    assert eval_r2.is_active is True
    assert eval_r2.tier == LicenseTier.PRACTICE
    assert policy_b.get_status()["licensed"] is True

    # -------------------------------------------------------------------------
    # STAGE 4: Restore Historical Database from Machine A into Machine B
    # -------------------------------------------------------------------------
    # Perform clean WAL checkpoint on Machine A before backup
    store_a.checkpoint_wal()
    backup_db_bytes = (machine_a_dir / "vaultbasis.db").read_bytes()
    (machine_b_dir / "vaultbasis_restored.db").write_bytes(backup_db_bytes)
    restored_store_b = SQLiteStore(machine_b_dir / "vaultbasis_restored.db")

    restored_case = restored_store_b.get_case("CASE-ACME-001")
    assert restored_case is not None
    assert restored_case.case_id == "CASE-ACME-001"

    restored_receipt = restored_store_b.get_receipt("11111111-1111-4000-8000-111111111111")
    assert restored_receipt is not None

    # Verify Historical Receipt Remains Cryptographically Valid via Standalone Verifier
    verification = verify_outcome_receipt(restored_receipt)
    assert verification.is_valid is True
    assert verification.signature_valid is True
    assert verification.key_fingerprint_valid is True
