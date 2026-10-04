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
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for high concurrency & robustness
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
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
                    updated_at TEXT NOT NULL
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

                CREATE TABLE IF NOT EXISTS commercial_license (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    token_text TEXT NOT NULL,
                    installed_at TEXT NOT NULL
                );
            """)
            # Migration check: ensure client_reference column exists
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(cases)")
            columns = [row[1] for row in cursor.fetchall()]
            if "client_reference" not in columns:
                cursor.execute("ALTER TABLE cases ADD COLUMN client_reference TEXT DEFAULT 'Sample Client'")

    def save_case(self, case: CanonicalCase):
        now_utc = datetime.now(timezone.utc).isoformat()
        client_ref = getattr(case, "client_reference", "Sample Client") or "Sample Client"
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO cases (case_id, client_reference, tax_year, jurisdiction, case_status, outcome_state, assurance_level, receipt_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(case_id) DO UPDATE SET
                    client_reference=excluded.client_reference,
                    case_status=excluded.case_status,
                    outcome_state=excluded.outcome_state,
                    assurance_level=excluded.assurance_level,
                    receipt_id=excluded.receipt_id,
                    updated_at=excluded.updated_at;
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
                now_utc
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
            return CanonicalCase(
                case_id=row["case_id"],
                client_reference=client_ref,
                tax_year=row["tax_year"],
                jurisdiction=row["jurisdiction"],
                case_status=row["case_status"],
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
            return [dict(r) for r in rows]

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

    def get_source_file_bytes(self, source_id: str) -> Optional[bytes]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT raw_content FROM sources WHERE source_id = ?", (source_id,)).fetchone()
            if row:
                return row["raw_content"]
            return None

    def count_billable_cases(self, sample_case_ids: Optional[Set[str]] = None) -> int:
        """
        Returns count of persistent practitioner-created production cases.
        Explicitly excludes bundled sample cases from capacity metering.
        """
        excluded = sample_case_ids or {"CASE-SAMPLE-2025"}
        placeholders = ",".join("?" for _ in excluded)
        with self._get_connection() as conn:
            query = f"SELECT COUNT(*) FROM cases WHERE case_id NOT IN ({placeholders})"
            cursor = conn.execute(query, list(excluded))
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

