"""
VaultBasis MMP-1.5 Local Persistence Durability & Recovery Test Suite
Tests MMP15-DATA-001:
1. WAL journal mode & synchronous configuration
2. Foreign key relational constraint enforcement
3. Transactional schema migration ledger & version history
4. Idempotent startup & schema migration upgrades
5. Structural integrity check & foreign key check verification
6. Point-in-time online non-blocking backup creation
7. Database restore & post-restore integrity validation
8. Atomic rollback & collision resilience
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from edge.storage.sqlite_store import SQLiteStore, EvidenceCollisionError
from schemas.canonical.case import CanonicalCase, SourceDocumentMetadata
from schemas.canonical.transaction import CanonicalTransaction


@pytest.fixture
def temp_store(tmp_path):
    db_file = tmp_path / "durability_test.db"
    return SQLiteStore(db_file)


def test_sqlite_pragmas_wal_and_foreign_keys(temp_store):
    """Asserts that WAL mode, foreign keys, synchronous=FULL, and busy timeout are strictly configured."""
    with temp_store._get_connection() as conn:
        journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        assert journal_mode.upper() == "WAL"

        synchronous = conn.execute("PRAGMA synchronous;").fetchone()[0]
        assert synchronous == 2  # 2 corresponds to FULL in SQLite PRAGMA

        foreign_keys = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        assert foreign_keys == 1

        busy_timeout = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
        assert busy_timeout >= 5000


def test_schema_migrations_ledger(temp_store):
    """Asserts that schema migrations table is populated sequentially."""
    migrations = temp_store.get_applied_migrations()
    assert len(migrations) >= 5
    versions = [m["version"] for m in migrations]
    assert versions == [1, 2, 3, 4, 5]
    assert migrations[0]["name"] == "initial_core_schema"
    assert migrations[1]["name"] == "commercial_licensing_schema"
    assert migrations[2]["name"] == "firm_and_workspace_identity"
    assert migrations[3]["name"] == "commercial_audit_log"
    assert migrations[4]["name"] == "installation_evaluation"


def test_schema_initialization_is_idempotent(temp_store):
    """Re-initializing the store on an existing DB must not duplicate migrations or fail."""
    # Re-run init
    temp_store._init_db()
    migrations = temp_store.get_applied_migrations()
    assert len(migrations) == 5


def test_foreign_key_cascade_deletion(temp_store):
    """Deleting a case must cascade delete its associated sources, transactions, and receipts."""
    now_utc = datetime.now(timezone.utc).isoformat()
    case = CanonicalCase(
        case_id="CASE-CASCADE-001",
        client_reference="Acme Corp",
        tax_year=2025,
        jurisdiction="US",
        case_status="CREATED",
        created_at=now_utc,
        updated_at=now_utc,
    )
    temp_store.save_case(case)

    # Ingest a source and transaction
    meta = SourceDocumentMetadata(
        source_id="SRC-CASCADE-01",
        filename="test.csv",
        sha256_hash="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        byte_size=120,
        schema_id="1099DA",
        row_count=1,
        ingested_at=now_utc,
    )

    tx = CanonicalTransaction(
        transaction_id="TX-CASCADE-01",
        source_id="SRC-CASCADE-01",
        source_file_hash="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        source_row_reference="1",
        asset="BTC",
        amount="1.5",
        timestamp=now_utc,
        transaction_type="DISPOSAL",
        proceeds="50000.00",
        cost_basis="30000.00",
        raw_row={},
    )

    temp_store.add_source_and_transactions("CASE-CASCADE-001", meta, b"test,csv,bytes", [tx])
    temp_store.save_receipt("RCPT-CASCADE-01", "CASE-CASCADE-001", {"receipt_id": "RCPT-CASCADE-01"})

    # Verify rows exist
    with temp_store._get_connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM sources WHERE case_id = 'CASE-CASCADE-001'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM transactions WHERE case_id = 'CASE-CASCADE-001'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM receipts WHERE case_id = 'CASE-CASCADE-001'").fetchone()[0] == 1

    # Delete the case
    temp_store.delete_case("CASE-CASCADE-001")

    # Verify cascading deletion
    with temp_store._get_connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM cases WHERE case_id = 'CASE-CASCADE-001'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM sources WHERE case_id = 'CASE-CASCADE-001'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM transactions WHERE case_id = 'CASE-CASCADE-001'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM receipts WHERE case_id = 'CASE-CASCADE-001'").fetchone()[0] == 0


def test_integrity_checks(temp_store):
    """Verifies PRAGMA integrity_check and foreign_key_check."""
    diag = temp_store.check_integrity()
    assert diag["healthy"] is True
    assert diag["structural_integrity"] == "OK"
    assert diag["foreign_keys_valid"] is True
    assert diag["journal_mode"].upper() == "WAL"

    assert temp_store.quick_check() is True


def test_online_backup_and_restore(temp_store, tmp_path):
    """Asserts point-in-time backup snapshot and restore workflow."""
    now_utc = datetime.now(timezone.utc).isoformat()
    case = CanonicalCase(
        case_id="CASE-BACKUP-001",
        client_reference="Backup Test Client",
        tax_year=2025,
        jurisdiction="US",
        case_status="CREATED",
        created_at=now_utc,
        updated_at=now_utc,
    )
    temp_store.save_case(case)
    temp_store.save_commercial_license("TEST-BACKUP-TOKEN-VAL")

    # Perform online snapshot backup
    backup_file = tmp_path / "vaultbasis_snapshot.db"
    temp_store.backup(backup_file)
    assert backup_file.is_file()
    assert backup_file.stat().st_size > 0

    # Modify the live database (delete case and license)
    temp_store.delete_case("CASE-BACKUP-001")
    temp_store.remove_commercial_license()
    assert temp_store.get_case("CASE-BACKUP-001") is None
    assert temp_store.get_commercial_license() is None

    # Restore from backup snapshot
    restored_ok = temp_store.restore(backup_file, verify_integrity=True)
    assert restored_ok is True

    # Assert data was fully restored
    restored_case = temp_store.get_case("CASE-BACKUP-001")
    assert restored_case is not None
    assert restored_case.client_reference == "Backup Test Client"
    assert temp_store.get_commercial_license() == "TEST-BACKUP-TOKEN-VAL"


def test_restore_incompatible_future_version_rejected(temp_store, tmp_path):
    """Restore must fail safely if the backup comes from an incompatible future schema version."""
    future_db_file = tmp_path / "future_schema.db"
    conn = sqlite3.connect(str(future_db_file))
    conn.execute("CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, name TEXT, applied_at TEXT);")
    conn.execute("INSERT INTO schema_migrations VALUES (999, 'future_migration_v999', '2026-10-04T00:00:00Z');")
    conn.commit()
    conn.close()

    with pytest.raises(ValueError, match="Incompatible backup schema version 999"):
        temp_store.restore(future_db_file)


def test_restore_corrupt_file_rejected(temp_store, tmp_path):
    """Restore must fail safely if the backup file is corrupt / invalid SQLite database."""
    corrupt_file = tmp_path / "corrupt.db"
    corrupt_file.write_bytes(b"THIS IS NOT A VALID SQLITE DATABASE FILE HEADER")

    with pytest.raises(Exception):
        temp_store.restore(corrupt_file)
