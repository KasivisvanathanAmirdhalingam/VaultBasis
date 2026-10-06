"""
VaultBasis Edge — Local SQLite Persistence Store
Conforms to PRD §18.2 (Local Data Persistence) and §22.1 (Data Recovery)
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class EvidenceCollisionError(Exception):
    """Raised when an insert would silently overwrite existing evidence."""
from schemas.canonical.case import CanonicalCase, SourceDocumentMetadata
from schemas.canonical.transaction import CanonicalTransaction


class SQLiteStore:
    """
    Local SQLite persistence store conforming to MMP15-DATA-001 Durability & Recovery Contract.
    Features WAL mode, foreign key enforcement, transactional versioned migrations, point-in-time
    online backup/restore, and corruption health checks.
    """

    CURRENT_SCHEMA_VERSION = 5

    def __init__(self, db_path: Path, synchronous: str = "FULL"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.synchronous = synchronous
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        conn.row_factory = sqlite3.Row
        # Enforce WAL mode, foreign keys, synchronous safety, and busy timeout
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute(f"PRAGMA synchronous = {self.synchronous};")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            # 1. Create migration ledger table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                );
            """)

            # 2. Run versioned migrations in strict transactional sequence
            self._run_migrations(conn)

    def _run_migrations(self, conn: sqlite3.Connection):
        cursor = conn.cursor()
        applied_rows = cursor.execute("SELECT version FROM schema_migrations ORDER BY version ASC").fetchall()
        applied_versions = {row[0] for row in applied_rows}

        # Migration 1: Initial Core Reconciliation Tables
        if 1 not in applied_versions:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY,
                    client_reference TEXT DEFAULT 'Sample Client',
                    tax_year INTEGER NOT NULL,
                    jurisdiction TEXT NOT NULL,
                    case_status TEXT NOT NULL,
                    outcome_state TEXT,
                    assurance_level TEXT,
                    receipt_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    case_kind TEXT DEFAULT 'PRODUCTION'
                );

                CREATE TABLE IF NOT EXISTS sources (
                    source_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    sha256_hash TEXT NOT NULL,
                    byte_size INTEGER NOT NULL,
                    schema_id TEXT NOT NULL,
                    row_count INTEGER NOT NULL,
                    raw_content BLOB NOT NULL,
                    ingested_at TEXT NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES cases (case_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES cases (case_id) ON DELETE CASCADE,
                    FOREIGN KEY (source_id) REFERENCES sources (source_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS receipts (
                    receipt_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES cases (case_id) ON DELETE CASCADE
                );
            """)
            now_utc = datetime.now(timezone.utc).isoformat()
            conn.execute("INSERT INTO schema_migrations (version, name, applied_at) VALUES (1, 'initial_core_schema', ?)", (now_utc,))

        # Migration 2: Commercial License Table & Migration Columns
        if 2 not in applied_versions:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS commercial_license (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    token_text TEXT NOT NULL,
                    installed_at TEXT NOT NULL
                );
            """)
            # Ensure client_reference and case_kind columns exist
            cursor.execute("PRAGMA table_info(cases)")
            columns = [row[1] for row in cursor.fetchall()]
            if "client_reference" not in columns:
                cursor.execute("ALTER TABLE cases ADD COLUMN client_reference TEXT DEFAULT 'Sample Client'")
            if "case_kind" not in columns:
                cursor.execute("ALTER TABLE cases ADD COLUMN case_kind TEXT DEFAULT 'PRODUCTION'")
            now_utc = datetime.now(timezone.utc).isoformat()
            conn.execute("INSERT INTO schema_migrations (version, name, applied_at) VALUES (2, 'commercial_licensing_schema', ?)", (now_utc,))

        # Migration 3: Firm & Workspace Identity Table (MMP15-ORG-001)
        if 3 not in applied_versions:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS firm_identity (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    organization_id TEXT NOT NULL,
                    firm_name TEXT NOT NULL,
                    office_id TEXT,
                    workspace_id TEXT NOT NULL,
                    preparer_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    ptin TEXT,
                    efin TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)
            now_utc = datetime.now(timezone.utc).isoformat()
            conn.execute("INSERT INTO schema_migrations (version, name, applied_at) VALUES (3, 'firm_and_workspace_identity', ?)", (now_utc,))

        # Migration 4: Commercial & Administrative Audit Log Table (MMP15-AUD-001)
        if 4 not in applied_versions:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS commercial_audit_log (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    actor_type TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    workspace_id TEXT,
                    installation_id TEXT,
                    build_sha TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    event_hash TEXT NOT NULL,
                    previous_event_hash TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_audit_occurred_at ON commercial_audit_log (occurred_at);
                CREATE INDEX IF NOT EXISTS idx_audit_event_type ON commercial_audit_log (event_type);
            """)
            now_utc = datetime.now(timezone.utc).isoformat()
            conn.execute("INSERT INTO schema_migrations (version, name, applied_at) VALUES (4, 'commercial_audit_log', ?)", (now_utc,))

        # Migration 5: Local Installation-Bound Evaluation State (MMP15-EVAL-E2E-001)
        if 5 not in applied_versions:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS installation_evaluation (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    installation_id TEXT NOT NULL,
                    customer_name TEXT NOT NULL,
                    activated_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    max_cases INTEGER NOT NULL DEFAULT 1,
                    anti_replay_hash TEXT NOT NULL
                );
            """)
            now_utc = datetime.now(timezone.utc).isoformat()
            conn.execute("INSERT INTO schema_migrations (version, name, applied_at) VALUES (5, 'installation_evaluation', ?)", (now_utc,))

        # Idempotent verification for existing databases
        cursor.execute("PRAGMA table_info(cases)")
        existing_cols = [row[1] for row in cursor.fetchall()]
        if existing_cols:
            if "client_reference" not in existing_cols:
                cursor.execute("ALTER TABLE cases ADD COLUMN client_reference TEXT DEFAULT 'Sample Client'")
            if "case_kind" not in existing_cols:
                cursor.execute("ALTER TABLE cases ADD COLUMN case_kind TEXT DEFAULT 'PRODUCTION'")
            if "sample_definition_id" not in existing_cols:
                cursor.execute("ALTER TABLE cases ADD COLUMN sample_definition_id TEXT")
            if "sample_manifest_digest" not in existing_cols:
                cursor.execute("ALTER TABLE cases ADD COLUMN sample_manifest_digest TEXT")


    def save_case(self, case: CanonicalCase):
        now_utc = datetime.now(timezone.utc).isoformat()
        client_ref = getattr(case, "client_reference", "Sample Client") or "Sample Client"
        case_kind = getattr(case, "case_kind", "PRODUCTION") or "PRODUCTION"
        sample_def_id = getattr(case, "sample_definition_id", None)
        sample_digest = getattr(case, "sample_manifest_digest", None)
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO cases (
                    case_id, client_reference, tax_year, jurisdiction, case_status,
                    outcome_state, assurance_level, receipt_id, created_at, updated_at,
                    case_kind, sample_definition_id, sample_manifest_digest
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(case_id) DO UPDATE SET
                    client_reference=excluded.client_reference,
                    case_status=excluded.case_status,
                    outcome_state=excluded.outcome_state,
                    assurance_level=excluded.assurance_level,
                    receipt_id=excluded.receipt_id,
                    updated_at=excluded.updated_at,
                    case_kind=excluded.case_kind,
                    sample_definition_id=excluded.sample_definition_id,
                    sample_manifest_digest=excluded.sample_manifest_digest;
            """, (
                case.case_id,
                client_ref,
                case.tax_year,
                case.jurisdiction,
                case.case_status,
                case.outcome_state,
                case.assurance_level,
                case.receipt_id,
                case.created_at,
                now_utc,
                case_kind,
                sample_def_id,
                sample_digest
            ))

    def get_case(self, case_id: str) -> Optional[CanonicalCase]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
            if not row:
                return None

            sources = {}
            for s_row in conn.execute("SELECT * FROM sources WHERE case_id = ?", (case_id,)).fetchall():
                sources[s_row["source_id"]] = SourceDocumentMetadata(
                    source_id=s_row["source_id"],
                    filename=s_row["filename"],
                    sha256_hash=s_row["sha256_hash"],
                    byte_size=s_row["byte_size"],
                    schema_id=s_row["schema_id"],
                    row_count=s_row["row_count"],
                    ingested_at=s_row["ingested_at"]
                )

            transactions = []
            for t_row in conn.execute("SELECT data_json FROM transactions WHERE case_id = ?", (case_id,)).fetchall():
                transactions.append(CanonicalTransaction.model_validate_json(t_row["data_json"]))

            client_ref = row["client_reference"] if "client_reference" in row.keys() and row["client_reference"] else "Sample Client"
            case_kind = row["case_kind"] if "case_kind" in row.keys() and row["case_kind"] else "PRODUCTION"
            sample_def_id = row["sample_definition_id"] if "sample_definition_id" in row.keys() else None
            sample_digest = row["sample_manifest_digest"] if "sample_manifest_digest" in row.keys() else None
            return CanonicalCase(
                case_id=row["case_id"],
                client_reference=client_ref,
                tax_year=row["tax_year"],
                jurisdiction=row["jurisdiction"],
                case_status=row["case_status"],
                case_kind=case_kind,
                sample_definition_id=sample_def_id,
                sample_manifest_digest=sample_digest,
                outcome_state=row["outcome_state"],
                assurance_level=row["assurance_level"],
                receipt_id=row["receipt_id"],
                sources=sources,
                transactions=transactions,
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

    def list_cases(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM cases ORDER BY updated_at DESC").fetchall()
            result = []
            for r in rows:
                c = dict(r)
                src_rows = conn.execute(
                    "SELECT source_id, schema_id, filename FROM sources WHERE case_id = ?",
                    (c["case_id"],)
                ).fetchall()
                c["sources_summary"] = [dict(s) for s in src_rows]
                result.append(c)
            return result

    def delete_case(self, case_id: str):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM cases WHERE case_id = ?", (case_id,))

    def add_source_and_transactions(
        self,
        case_id: str,
        meta: SourceDocumentMetadata,
        raw_bytes: bytes,
        transactions: List[CanonicalTransaction]
    ):
        with self._get_connection() as conn:
            existing_source = conn.execute(
                "SELECT source_id FROM sources WHERE source_id = ?", (meta.source_id,)
            ).fetchone()
            if existing_source:
                raise EvidenceCollisionError(
                    f"Source '{meta.source_id}' already exists in case '{case_id}'. "
                    "Existing evidence cannot be overwritten. Upload the source under a new case."
                )
            conn.execute("""
                INSERT INTO sources (source_id, case_id, filename, sha256_hash, byte_size, schema_id, row_count, raw_content, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meta.source_id,
                case_id,
                meta.filename,
                meta.sha256_hash,
                meta.byte_size,
                meta.schema_id,
                meta.row_count,
                raw_bytes,
                meta.ingested_at
            ))

            for tx in transactions:
                existing_tx = conn.execute(
                    "SELECT transaction_id FROM transactions WHERE transaction_id = ?",
                    (tx.transaction_id,)
                ).fetchone()
                if existing_tx:
                    raise EvidenceCollisionError(
                        f"Transaction '{tx.transaction_id}' already exists. "
                        "Existing transaction evidence cannot be overwritten."
                    )
                conn.execute("""
                    INSERT INTO transactions (transaction_id, case_id, source_id, data_json)
                    VALUES (?, ?, ?, ?)
                """, (
                    tx.transaction_id,
                    case_id,
                    meta.source_id,
                    tx.model_dump_json()
                ))

            conn.execute(
                "UPDATE cases SET case_status = 'SOURCES_INGESTED', updated_at = ? WHERE case_id = ?",
                (datetime.now(timezone.utc).isoformat(), case_id)
            )

    def save_receipt(self, receipt_id: str, case_id: str, receipt_dict: Dict[str, Any]):
        now_utc = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO receipts (receipt_id, case_id, receipt_json, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                receipt_id,
                case_id,
                json.dumps(receipt_dict),
                now_utc
            ))
            conn.execute("""
                UPDATE cases SET 
                    receipt_id = ?, 
                    case_status = 'RECEIPT_ISSUED',
                    updated_at = ?
                WHERE case_id = ?
            """, (receipt_id, now_utc, case_id))

    def get_receipt(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT receipt_json FROM receipts WHERE receipt_id = ?", (receipt_id,)).fetchone()
            if row:
                return json.loads(row["receipt_json"])
            return None

    def delete_receipt(self, receipt_id: str):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM receipts WHERE receipt_id = ?", (receipt_id,))

    def get_source_file_bytes(self, source_id: str) -> Optional[bytes]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT raw_content FROM sources WHERE source_id = ?", (source_id,)).fetchone()
            if row:
                return row["raw_content"]
            return None

    def count_billable_cases(self, sample_case_ids: Optional[Set[str]] = None, since_iso: Optional[str] = None) -> int:
        """
        Returns count of persistent practitioner-created production cases.
        Explicitly excludes bundled sample cases and test fixtures from capacity metering.
        Optionally filters by cases created since a specific ISO timestamp (e.g. evaluation activation).
        """
        excluded = sample_case_ids or {"CASE-SAMPLE-2025"}
        placeholders = ",".join("?" for _ in excluded)
        params: List[Any] = list(excluded)
        query = f"SELECT COUNT(*) FROM cases WHERE case_kind = 'PRODUCTION' AND case_id NOT IN ({placeholders})"
        if since_iso:
            query += " AND created_at >= ?"
            params.append(since_iso)
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return row[0] if row else 0

    def get_commercial_license(self) -> Optional[str]:
        """Retrieves stored commercial license token text if present."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT token_text FROM commercial_license WHERE id = 1").fetchone()
            if row:
                return row["token_text"]
            return None

    def save_commercial_license(self, token_text: str):
        """Stores or replaces the local commercial license token."""
        now_utc = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO commercial_license (id, token_text, installed_at)
                VALUES (1, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    token_text=excluded.token_text,
                    installed_at=excluded.installed_at;
            """, (token_text, now_utc))

    def remove_commercial_license(self):
        """Removes installed commercial license token."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM commercial_license WHERE id = 1")

    # --------------------------------------------------------------------------
    # Installation-Bound Evaluation Persistence (MMP15-EVAL-E2E-001)
    # --------------------------------------------------------------------------

    def get_installation_evaluation(self) -> Optional[Dict[str, Any]]:
        """Retrieves active installation-bound evaluation record if present."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM installation_evaluation WHERE id = 1").fetchone()
            if row:
                return dict(row)
            return None

    def save_installation_evaluation(
        self,
        installation_id: str,
        customer_name: str,
        activated_at: str,
        expires_at: str,
        max_cases: int = 1,
        anti_replay_hash: Optional[str] = None,
    ):
        """Stores local installation evaluation state with anti-replay hash."""
        import hashlib
        if not anti_replay_hash:
            anti_replay_hash = hashlib.sha256(f"{installation_id}:{activated_at}:{expires_at}".encode("utf-8")).hexdigest()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO installation_evaluation (id, installation_id, customer_name, activated_at, expires_at, max_cases, anti_replay_hash)
                VALUES (1, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    installation_id=excluded.installation_id,
                    customer_name=excluded.customer_name,
                    activated_at=excluded.activated_at,
                    expires_at=excluded.expires_at,
                    max_cases=excluded.max_cases,
                    anti_replay_hash=excluded.anti_replay_hash;
            """, (installation_id, customer_name, activated_at, expires_at, max_cases, anti_replay_hash))

    def remove_installation_evaluation(self):
        """Clears local installation evaluation state."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM installation_evaluation WHERE id = 1")

    # --------------------------------------------------------------------------
    # Durability & Recovery Contract Methods (MMP15-DATA-001)
    # --------------------------------------------------------------------------

    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """Returns ordered list of all schema migrations successfully applied."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT version, name, applied_at FROM schema_migrations ORDER BY version ASC").fetchall()
            return [dict(r) for r in rows]

    def check_integrity(self) -> Dict[str, Any]:
        """
        Executes structural integrity and relational foreign key verification.
        Returns detailed health diagnosis conforming to PRD §22.1.
        """
        with self._get_connection() as conn:
            # 1. Full Structural Integrity Check
            integrity_rows = [row[0] for row in conn.execute("PRAGMA integrity_check;").fetchall()]
            is_structurally_ok = integrity_rows == ["ok"]

            # 2. Relational Foreign Key Check
            fk_violations = [dict(r) for r in conn.execute("PRAGMA foreign_key_check;").fetchall()]
            is_fk_ok = len(fk_violations) == 0

            # 3. Journal Mode Check
            journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]

            is_healthy = is_structurally_ok and is_fk_ok

            return {
                "healthy": is_healthy,
                "structural_integrity": "OK" if is_structurally_ok else "CORRUPTED",
                "integrity_details": integrity_rows,
                "foreign_keys_valid": is_fk_ok,
                "foreign_key_violations": fk_violations,
                "journal_mode": journal_mode,
                "schema_version": self.CURRENT_SCHEMA_VERSION,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def quick_check(self) -> bool:
        """Fast non-blocking startup sanity check."""
        try:
            with self._get_connection() as conn:
                res = conn.execute("PRAGMA quick_check;").fetchone()
                return res is not None and res[0] == "ok"
        except Exception:
            return False

    def backup(self, target_path: Path) -> Path:
        """
        Creates a consistent, non-blocking point-in-time snapshot backup using SQLite's Online Backup API.
        Safe for execution while readers and writers are actively querying the primary database.
        """
        dest_path = Path(target_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove any existing destination file before snapshotting
        if dest_path.is_file():
            dest_path.unlink()

        with self._get_connection() as src_conn:
            dest_conn = sqlite3.connect(str(dest_path))
            try:
                src_conn.backup(dest_conn)
            finally:
                dest_conn.close()
        return dest_path

    def restore(self, backup_path: Path, verify_integrity: bool = True) -> bool:
        """
        Restores the active database from a point-in-time backup snapshot.
        Strict Recovery Contract:
        1. Pre-validates backup snapshot integrity before applying.
        2. Validates backup schema compatibility (cannot restore incompatible newer schema versions).
        3. Restores snapshot atomically into live storage.
        4. Verifies post-restore integrity and foreign key constraints.
        """
        src_path = Path(backup_path)
        if not src_path.is_file():
            raise FileNotFoundError(f"Backup file not found: '{backup_path}'")

        # 1. Pre-flight integrity validation on backup snapshot
        pre_conn = sqlite3.connect(str(src_path))
        try:
            pre_check = pre_conn.execute("PRAGMA integrity_check;").fetchall()
            if not pre_check or pre_check[0][0].lower() != "ok":
                raise ValueError(f"Backup file corruption detected: {pre_check}")

            # Check schema version compatibility
            try:
                cur = pre_conn.cursor()
                cur.execute("SELECT MAX(version) FROM schema_migrations")
                row = cur.fetchone()
                backup_version = row[0] if row and row[0] is not None else 1
                if backup_version > self.CURRENT_SCHEMA_VERSION:
                    raise ValueError(
                        f"Incompatible backup schema version {backup_version}. "
                        f"Current runtime supports up to version {self.CURRENT_SCHEMA_VERSION}."
                    )
            except sqlite3.OperationalError:
                # schema_migrations table might not exist in un-migrated legacy backup
                pass
        finally:
            pre_conn.close()

        # 2. Atomic restore into live store
        backup_conn = sqlite3.connect(str(src_path))
        try:
            with self._get_connection() as live_conn:
                backup_conn.backup(live_conn)
        finally:
            backup_conn.close()

        # 3. Post-restore health verification
        if verify_integrity:
            diag = self.check_integrity()
            if not diag["healthy"]:
                raise RuntimeError(f"Post-restore integrity check failed: {diag}")
            return diag["healthy"]
        return True

    # --------------------------------------------------------------------------
    # Firm & Workspace Identity Persistence (MMP15-ORG-001)
    # --------------------------------------------------------------------------

    def get_firm_identity(self) -> Optional[Dict[str, Any]]:
        """Retrieves active firm and workspace identity profile."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM firm_identity WHERE id = 1").fetchone()
            if row:
                return dict(row)
            return None

    def save_firm_identity(self, firm_dict: Dict[str, Any]):
        """Stores or updates active firm and workspace identity profile."""
        now_utc = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO firm_identity (
                    id, organization_id, firm_name, office_id, workspace_id,
                    preparer_id, display_name, ptin, efin, created_at, updated_at
                )
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    organization_id=excluded.organization_id,
                    firm_name=excluded.firm_name,
                    office_id=excluded.office_id,
                    workspace_id=excluded.workspace_id,
                    preparer_id=excluded.preparer_id,
                    display_name=excluded.display_name,
                    ptin=excluded.ptin,
                    efin=excluded.efin,
                    updated_at=excluded.updated_at;
            """, (
                firm_dict["organization_id"],
                firm_dict["firm_name"],
                firm_dict.get("office_id"),
                firm_dict["workspace_id"],
                firm_dict["preparer_id"],
                firm_dict["display_name"],
                firm_dict.get("ptin"),
                firm_dict.get("efin"),
                firm_dict.get("created_at", now_utc),
                now_utc
            ))

    def delete_firm_identity(self):
        """Clears stored firm and workspace identity profile."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM firm_identity WHERE id = 1")

    # --------------------------------------------------------------------------
    # Commercial & Administrative Audit Log Persistence (MMP15-AUD-001)
    # --------------------------------------------------------------------------

    def insert_audit_event(self, event_dict: Dict[str, Any]):
        """Inserts an immutable administrative audit event record."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO commercial_audit_log (
                    event_id, event_type, occurred_at, actor_type, actor_id,
                    workspace_id, installation_id, build_sha, details_json,
                    event_hash, previous_event_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                event_dict["event_id"],
                event_dict["event_type"],
                event_dict["occurred_at"],
                event_dict.get("actor_type", "SYSTEM"),
                event_dict.get("actor_id", "UNKNOWN"),
                event_dict.get("workspace_id"),
                event_dict.get("installation_id"),
                event_dict.get("build_sha", "UNKNOWN"),
                event_dict.get("details_json", "{}"),
                event_dict["event_hash"],
                event_dict.get("previous_event_hash"),
            ))

    def get_last_audit_event(self) -> Optional[Dict[str, Any]]:
        """Retrieves the most recent audit event record for hash chaining."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM commercial_audit_log ORDER BY occurred_at DESC, rowid DESC LIMIT 1"
            ).fetchone()
            if row:
                return dict(row)
            return None

    def get_audit_events(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieves paginated audit events ordered chronologically descending."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM commercial_audit_log ORDER BY occurred_at DESC, rowid DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()
            return [dict(r) for r in rows]

    def count_audit_events(self) -> int:
        """Returns total number of recorded audit events."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM commercial_audit_log").fetchone()
            return row[0] if row else 0


