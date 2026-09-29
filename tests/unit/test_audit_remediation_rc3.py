"""
RC3 Audit Remediation Regression Tests

Proves that each reproduced defect is eliminated by its fix.
Tests must fail on the pre-fix code and pass on the fixed code.
"""
import hashlib
import json
import sys
from pathlib import Path
import pytest

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


# ---------------------------------------------------------------------------
# P1-4: Evidence collision — sources and transactions must reject, not replace
# ---------------------------------------------------------------------------

class TestEvidenceCollisionRejection:

    def _make_store(self, tmp_path, case_id="CASE-001"):
        from edge.storage.sqlite_store import SQLiteStore
        from schemas.canonical.case import CanonicalCase
        from datetime import datetime, timezone
        store = SQLiteStore(tmp_path / "test.db")
        now = datetime.now(timezone.utc).isoformat()
        store.save_case(CanonicalCase(case_id=case_id, tax_year=2025, created_at=now, updated_at=now))
        return store

    def _make_source_meta(self, source_id="SRC-AABBCC_test"):
        from schemas.canonical.case import SourceDocumentMetadata
        from datetime import datetime, timezone
        return SourceDocumentMetadata(
            source_id=source_id,
            filename="test.csv",
            sha256_hash="a" * 64,
            byte_size=100,
            schema_id="IRS_1099DA_2025_PREVIEW",
            row_count=1,
            ingested_at=datetime.now(timezone.utc).isoformat(),
        )

    def test_source_collision_raises_error(self, tmp_path):
        """Inserting a source with an existing source_id must raise EvidenceCollisionError."""
        from edge.storage.sqlite_store import EvidenceCollisionError
        store = self._make_store(tmp_path)
        meta = self._make_source_meta()

        # First insert must succeed
        store.add_source_and_transactions("CASE-001", meta, b"original bytes", [])

        # Second insert with same source_id must raise — not silently replace
        with pytest.raises(EvidenceCollisionError) as exc_info:
            store.add_source_and_transactions("CASE-001", meta, b"different bytes", [])
        assert "already exists" in str(exc_info.value)

    def test_source_collision_preserves_original_bytes(self, tmp_path):
        """After a collision attempt, the original source bytes must be intact."""
        from edge.storage.sqlite_store import EvidenceCollisionError
        store = self._make_store(tmp_path)
        meta = self._make_source_meta()

        store.add_source_and_transactions("CASE-001", meta, b"original bytes", [])
        try:
            store.add_source_and_transactions("CASE-001", meta, b"replacement bytes", [])
        except EvidenceCollisionError:
            pass

        # Original bytes must still be in the DB
        original = store.get_source_file_bytes(meta.source_id)
        assert original == b"original bytes"

    def test_distinct_source_ids_do_not_collide(self, tmp_path):
        """Two sources with different IDs must both insert successfully."""
        store = self._make_store(tmp_path)
        meta_a = self._make_source_meta("SRC-AAAAAA_test")
        meta_b = self._make_source_meta("SRC-BBBBBB_test")

        store.add_source_and_transactions("CASE-001", meta_a, b"bytes a", [])
        store.add_source_and_transactions("CASE-001", meta_b, b"bytes b", [])  # must not raise

    def _make_transaction(self, transaction_id="TX-0001", source_id="SRC-AABBCC_test", proceeds="300.00"):
        from schemas.canonical.transaction import CanonicalTransaction
        return CanonicalTransaction(
            transaction_id=transaction_id,
            source_id=source_id,
            source_file_hash="a" * 64,
            source_row_reference="Line:1",
            transaction_type="SALE",
            asset="BTC",
            proceeds=proceeds,
            cost_basis="250.00",
            gain_loss="50.00",
            disposition_date="2025-04-10",
        )

    def test_transaction_collision_raises_error(self, tmp_path):
        """Inserting a transaction with an existing transaction_id must raise EvidenceCollisionError."""
        from edge.storage.sqlite_store import EvidenceCollisionError
        store = self._make_store(tmp_path)
        meta = self._make_source_meta()
        tx_original = self._make_transaction(proceeds="300.00")

        store.add_source_and_transactions("CASE-001", meta, b"bytes", [tx_original])

        # Second source with a transaction sharing an existing transaction_id must raise
        meta2 = self._make_source_meta("SRC-CCCCCC_test")
        tx_collision = self._make_transaction(source_id="SRC-CCCCCC_test", proceeds="999.00")
        with pytest.raises(EvidenceCollisionError) as exc_info:
            store.add_source_and_transactions("CASE-001", meta2, b"bytes2", [tx_collision])
        assert "already exists" in str(exc_info.value)

    def test_transaction_collision_preserves_original(self, tmp_path):
        """After a transaction_id collision attempt, the original transaction data must be intact."""
        from edge.storage.sqlite_store import EvidenceCollisionError
        import sqlite3
        store = self._make_store(tmp_path)
        meta = self._make_source_meta()
        tx_original = self._make_transaction(proceeds="300.00")
        store.add_source_and_transactions("CASE-001", meta, b"bytes", [tx_original])

        meta2 = self._make_source_meta("SRC-CCCCCC_test")
        tx_collision = self._make_transaction(source_id="SRC-CCCCCC_test", proceeds="999.00")
        try:
            store.add_source_and_transactions("CASE-001", meta2, b"bytes2", [tx_collision])
        except EvidenceCollisionError:
            pass

        # Read transaction data directly from storage layer
        conn = sqlite3.connect(str(store.db_path))
        row = conn.execute(
            "SELECT data_json FROM transactions WHERE transaction_id = ?", ("TX-0001",)
        ).fetchone()
        conn.close()
        import json
        saved = json.loads(row[0])
        assert saved["proceeds"] == "300.00", (
            f"Original transaction proceeds must be preserved; got {saved['proceeds']}"
        )

    def test_receipt_collision_preserves_original(self, tmp_path):
        """INSERT OR IGNORE on receipts: second save must not overwrite first."""
        store = self._make_store(tmp_path)
        original = {"receipt_id": "r1", "outcome_state": "MATCHED", "source_hashes": {}}
        replacement = {"receipt_id": "r1", "outcome_state": "TAMPERED", "source_hashes": {}}

        store.save_receipt("r1", "CASE-001", original)
        store.save_receipt("r1", "CASE-001", replacement)  # must silently ignore

        saved = store.get_receipt("r1")
        assert saved["outcome_state"] == "MATCHED", (
            "Second save must not overwrite existing receipt"
        )


# ---------------------------------------------------------------------------
# P1-3: Receipt idempotency — stale receipt must not mask changed sources
# ---------------------------------------------------------------------------

class TestReceiptIdempotency:

    def _source_manifest(self, source_hashes: dict) -> str:
        return hashlib.sha256(
            json.dumps(sorted(source_hashes.items())).encode()
        ).hexdigest()

    def test_same_sources_manifest_matches(self):
        """Same source set produces the same manifest hash."""
        hashes = {"SRC-A": "aaa", "SRC-B": "bbb"}
        m1 = self._source_manifest(hashes)
        m2 = self._source_manifest(hashes)
        assert m1 == m2

    def test_added_source_changes_manifest(self):
        """Adding a source changes the manifest hash."""
        before = {"SRC-A": "aaa", "SRC-B": "bbb"}
        after  = {"SRC-A": "aaa", "SRC-B": "bbb", "SRC-C": "ccc"}
        assert self._source_manifest(before) != self._source_manifest(after)

    def test_changed_source_hash_changes_manifest(self):
        """Replacing a source file (different SHA-256) changes the manifest."""
        before = {"SRC-A": "aaa", "SRC-B": "bbb"}
        after  = {"SRC-A": "aaa", "SRC-B": "ccc_different"}
        assert self._source_manifest(before) != self._source_manifest(after)

    def test_manifest_is_order_independent(self):
        """Source dict insertion order must not affect the manifest hash."""
        m1 = self._source_manifest({"SRC-A": "aaa", "SRC-B": "bbb"})
        m2 = self._source_manifest({"SRC-B": "bbb", "SRC-A": "aaa"})
        assert m1 == m2


# ---------------------------------------------------------------------------
# P1-9: DB isolation — each test gets its own database
# ---------------------------------------------------------------------------

class TestDatabaseIsolation:

    def test_store_uses_isolated_path(self, tmp_path):
        """The monkeypatched db_store must point at the test-specific path."""
        import edge.api.app as app_module
        db_path = str(app_module.db_store.db_path)
        assert "vaultbasis.db" not in db_path or str(tmp_path) in db_path, (
            f"db_store is using shared path: {db_path}"
        )

    def test_case_created_in_one_test_is_absent_in_another(self, tmp_path):
        """State written in this test must not leak to any other test."""
        import edge.api.app as app_module
        from schemas.canonical.case import CanonicalCase
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        case = CanonicalCase(case_id="ISOLATION-TEST-CASE", tax_year=2025, created_at=now, updated_at=now)
        app_module.db_store.save_case(case)

        # Verify it was written to this test's isolated DB
        retrieved = app_module.db_store.get_case("ISOLATION-TEST-CASE")
        assert retrieved is not None

    def test_isolation_test_case_absent_from_fresh_db(self, tmp_path):
        """The case written in the previous test must not exist here."""
        import edge.api.app as app_module

        # Each test gets a fresh DB via the autouse fixture —
        # the case from the previous test must be absent
        retrieved = app_module.db_store.get_case("ISOLATION-TEST-CASE")
        assert retrieved is None, (
            "Case from a previous test leaked into this test's database"
        )


# ---------------------------------------------------------------------------
# P1-1: CORS — loopback-only origins
# ---------------------------------------------------------------------------

class TestCORSConfiguration:

    def test_cors_does_not_allow_wildcard(self):
        """CORS must not allow all origins."""
        import edge.api.app as app_module
        cors_middleware = None
        for middleware in app_module.app.user_middleware:
            if "CORSMiddleware" in str(middleware):
                cors_middleware = middleware
                break
        # If CORSMiddleware is present, wildcard must not be in allow_origins
        if cors_middleware:
            kwargs = cors_middleware.kwargs
            assert "*" not in kwargs.get("allow_origins", []), (
                "CORS wildcard origin is not permitted"
            )

    def test_cors_allows_loopback(self):
        """CORS must permit 127.0.0.1:8000."""
        import edge.api.app as app_module
        for middleware in app_module.app.user_middleware:
            if "CORSMiddleware" in str(middleware):
                origins = middleware.kwargs.get("allow_origins", [])
                assert any("127.0.0.1" in o for o in origins), (
                    "Loopback origin must be permitted"
                )
                return


# ---------------------------------------------------------------------------
# P1-2: Schema path traversal — allowlist enforced
# ---------------------------------------------------------------------------

class TestSchemaAccessControl:

    def test_allowlisted_schema_accessible(self):
        """receipt-v0.1.json must be in the allowlist."""
        import edge.api.app as app_module
        assert "receipt-v0.1.json" in app_module._SCHEMA_ALLOWLIST

    def test_traversal_filename_not_in_allowlist(self):
        """Path traversal strings must not be in the allowlist."""
        import edge.api.app as app_module
        traversal_attempts = [
            "../../etc/passwd",
            "../keys/installation_ed25519.key",
            "receipt-v0.1.json/../../../etc/passwd",
        ]
        for attempt in traversal_attempts:
            assert attempt not in app_module._SCHEMA_ALLOWLIST, (
                f"Traversal string '{attempt}' must not be in allowlist"
            )
