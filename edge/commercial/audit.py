"""
VaultBasis MMP-1.5 Commercial & Administrative Audit Event Log Service
Conforms to docs/mmp15_task_ledger.md (MMP15-AUD-001) and PRD §65.1.

Architectural Invariants:
1. Administrative Scope Only: Captures commercial lifecycle, identity updates, diagnostic exports, and restore events.
   STRICT PRIVACY: NEVER records client transactions, tax lots, cost basis amounts, or raw regulated IDs.
2. Tamper-Evident Hash Chaining: Each event cryptographically commits to the SHA-256 hash of the preceding event.
3. Append-Only Persistence: Events are immutable and append-only in local SQLite storage.
4. Air-Gapped Operation: Strictly local audit logging with zero telemetry or network egress.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from edge.storage.sqlite_store import SQLiteStore
from edge.system.version import get_system_version


class AuditEventType(str, Enum):
    """
    Controlled administrative audit event vocabulary.
    """
    LICENSE_INSTALLED = "LICENSE_INSTALLED"
    LICENSE_REPLACED = "LICENSE_REPLACED"
    LICENSE_REJECTED = "LICENSE_REJECTED"
    LICENSE_STATE_CHANGED = "LICENSE_STATE_CHANGED"
    FIRM_IDENTITY_CREATED = "FIRM_IDENTITY_CREATED"
    FIRM_IDENTITY_UPDATED = "FIRM_IDENTITY_UPDATED"
    FIRM_IDENTITY_REMOVED = "FIRM_IDENTITY_REMOVED"
    DIAGNOSTIC_EXPORTED = "DIAGNOSTIC_EXPORTED"
    RELEASE_CHANNEL_CHANGED = "RELEASE_CHANNEL_CHANGED"
    DATABASE_RESTORE_STARTED = "DATABASE_RESTORE_STARTED"
    DATABASE_RESTORE_COMPLETED = "DATABASE_RESTORE_COMPLETED"
    DATABASE_RESTORE_FAILED = "DATABASE_RESTORE_FAILED"


class AuditEvent(BaseModel):
    """
    Immutable administrative audit log entry with cryptographic hash chaining.
    """
    event_id: str
    event_type: AuditEventType
    occurred_at: str
    actor_type: str = "SYSTEM"
    actor_id: str = "SYSTEM"
    workspace_id: Optional[str] = None
    installation_id: Optional[str] = None
    build_sha: str
    details: Dict[str, Any] = Field(default_factory=dict)
    event_hash: str
    previous_event_hash: Optional[str] = None


def compute_event_hash(
    event_id: str,
    event_type: str,
    occurred_at: str,
    actor_type: str,
    actor_id: str,
    workspace_id: Optional[str],
    installation_id: Optional[str],
    build_sha: str,
    details_json: str,
    previous_event_hash: Optional[str],
) -> str:
    """
    Computes SHA-256 digest over canonicalized event attributes for tamper evidence.
    """
    payload = f"{event_id}|{event_type}|{occurred_at}|{actor_type}|{actor_id}|{workspace_id or ''}|{installation_id or ''}|{build_sha}|{details_json}|{previous_event_hash or 'GENESIS'}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class CommercialAuditService:
    """
    Manages tamper-evident administrative audit logging in SQLite.
    """

    def __init__(self, store: SQLiteStore, installation_id: Optional[str] = None):
        self.store = store
        self.installation_id = installation_id

    def record_event(
        self,
        event_type: AuditEventType,
        actor_type: str = "SYSTEM",
        actor_id: str = "SYSTEM",
        workspace_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Records an append-only administrative audit event with hash chaining.
        """
        now_utc = datetime.now(timezone.utc).isoformat()
        sys_ver = get_system_version()
        event_id = str(uuid.uuid4())
        details_map = details or {}
        details_json = json.dumps(details_map, sort_keys=True)

        # Get previous event hash
        last_event = self.store.get_last_audit_event()
        previous_hash = last_event["event_hash"] if last_event else None

        inst_id = self.installation_id or "LOCAL_DEFAULT"

        event_hash = compute_event_hash(
            event_id=event_id,
            event_type=event_type.value,
            occurred_at=now_utc,
            actor_type=actor_type,
            actor_id=actor_id,
            workspace_id=workspace_id,
            installation_id=inst_id,
            build_sha=sys_ver.build_sha,
            details_json=details_json,
            previous_event_hash=previous_hash,
        )

        event_record = {
            "event_id": event_id,
            "event_type": event_type.value,
            "occurred_at": now_utc,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "workspace_id": workspace_id,
            "installation_id": inst_id,
            "build_sha": sys_ver.build_sha,
            "details_json": details_json,
            "event_hash": event_hash,
            "previous_event_hash": previous_hash,
        }

        self.store.insert_audit_event(event_record)

        return AuditEvent(
            event_id=event_id,
            event_type=event_type,
            occurred_at=now_utc,
            actor_type=actor_type,
            actor_id=actor_id,
            workspace_id=workspace_id,
            installation_id=inst_id,
            build_sha=sys_ver.build_sha,
            details=details_map,
            event_hash=event_hash,
            previous_event_hash=previous_hash,
        )

    def get_events(self, limit: int = 100, offset: int = 0) -> List[AuditEvent]:
        """Returns paginated audit events."""
        raw_rows = self.store.get_audit_events(limit=limit, offset=offset)
        events = []
        for r in raw_rows:
            details_dict = json.loads(r.get("details_json", "{}"))
            events.append(
                AuditEvent(
                    event_id=r["event_id"],
                    event_type=AuditEventType(r["event_type"]),
                    occurred_at=r["occurred_at"],
                    actor_type=r["actor_type"],
                    actor_id=r["actor_id"],
                    workspace_id=r.get("workspace_id"),
                    installation_id=r.get("installation_id"),
                    build_sha=r["build_sha"],
                    details=details_dict,
                    event_hash=r["event_hash"],
                    previous_event_hash=r.get("previous_event_hash"),
                )
            )
        return events

    def count_events(self) -> int:
        """Returns count of recorded audit events."""
        return self.store.count_audit_events()

    def verify_chain_integrity(self) -> Dict[str, Any]:
        """
        Validates hash chain integrity across all historical audit events.
        """
        # Fetch all events chronologically (oldest to newest)
        with self.store._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM commercial_audit_log ORDER BY occurred_at ASC, rowid ASC"
            ).fetchall()

        if not rows:
            return {"valid": True, "event_count": 0, "broken_at": None}

        prev_hash = None
        for idx, row_raw in enumerate(rows):
            r = dict(row_raw)
            # Check previous hash pointer
            if r.get("previous_event_hash") != prev_hash:
                return {
                    "valid": False,
                    "event_count": len(rows),
                    "broken_at": r["event_id"],
                    "reason": f"Mismatched previous_event_hash at index {idx}",
                }

            # Recalculate event hash
            expected_hash = compute_event_hash(
                event_id=r["event_id"],
                event_type=r["event_type"],
                occurred_at=r["occurred_at"],
                actor_type=r["actor_type"],
                actor_id=r["actor_id"],
                workspace_id=r.get("workspace_id"),
                installation_id=r.get("installation_id"),
                build_sha=r["build_sha"],
                details_json=r.get("details_json", "{}"),
                previous_event_hash=prev_hash,
            )

            if r["event_hash"] != expected_hash:
                return {
                    "valid": False,
                    "event_count": len(rows),
                    "broken_at": r["event_id"],
                    "reason": f"Corrupted event_hash at index {idx}",
                }

            prev_hash = r["event_hash"]

        return {"valid": True, "event_count": len(rows), "broken_at": None}
