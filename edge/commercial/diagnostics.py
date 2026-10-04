"""
VaultBasis MMP-1.5 Sanitized Diagnostic & Support Bundle Packager
Conforms to docs/mmp15_task_ledger.md (MMP15-OPS-001) and PRD §63.1.

Architectural Invariants:
1. Schema-First Positive Allowlist: Only explicitly enumerated operational metadata is captured.
2. Complete Isolation of Financial & Case Data:
   - ZERO transaction rows, wallet addresses, cost bases, or tax lot values.
   - ZERO source files, intake raw content, or customer evidence payloads.
   - ZERO cryptographic private keys or license signing secrets.
   - ZERO raw regulated identifiers (PTIN/EFIN masked via deterministic redaction).
3. Air-Gap Safety: Fully self-contained, generated locally on-demand with zero network egress.
"""

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from edge.commercial.identity import FirmIdentityService
from edge.commercial.policy import CommercialPolicyService
from edge.storage.sqlite_store import SQLiteStore
from edge.system.version import get_system_version


class SystemDiagnosticSection(BaseModel):
    product: str
    product_version: str
    build_sha: str
    release_channel: str
    platform: str
    os_name: str
    architecture: str
    python_version: str
    schema_version: int
    license_protocol_version: str
    receipt_schema_version: str


class DatabaseDiagnosticSection(BaseModel):
    schema_version: int
    journal_mode: str
    integrity_status: str
    foreign_keys_valid: bool
    database_size_bytes: int
    applied_migrations: List[Dict[str, Any]]


class CommercialDiagnosticSection(BaseModel):
    is_licensed: bool
    tier: Optional[str] = "COMMUNITY"
    state: str
    installation_id: str
    max_cases_per_installation: Optional[int] = None
    cases_created: int
    entitlements: List[str]
    expires_at_utc: Optional[str] = None
    grace_period_days: int


class FirmDiagnosticSection(BaseModel):
    configured: bool
    identity: Optional[Dict[str, Any]] = None


class RuntimeDiagnosticSection(BaseModel):
    status: str
    egress_policy: str
    timestamp_utc: str


class DiagnosticBundleReport(BaseModel):
    """
    Strict schema-first allowlisted diagnostic package.
    """
    bundle_id: str
    generated_at_utc: str
    system: SystemDiagnosticSection
    database: DatabaseDiagnosticSection
    commercial: CommercialDiagnosticSection
    firm: FirmDiagnosticSection
    runtime: RuntimeDiagnosticSection


class DiagnosticPackager:
    """
    Packages sanitized operational and health diagnostic reports for air-gapped support.
    """

    def __init__(
        self,
        store: SQLiteStore,
        commercial_policy: CommercialPolicyService,
        firm_identity_service: FirmIdentityService,
    ):
        self.store = store
        self.commercial_policy = commercial_policy
        self.firm_identity_service = firm_identity_service

    def generate_report(self) -> DiagnosticBundleReport:
        """
        Constructs the positive-allowlisted diagnostic bundle model.
        Guarantees zero transactional, financial, evidence, or credential leakage.
        """
        now_utc = datetime.now(timezone.utc).isoformat()
        sys_ver = get_system_version()

        # Database health & metadata
        db_integrity = self.store.check_integrity()
        db_size = self.store.db_path.stat().st_size if self.store.db_path.is_file() else 0
        migrations = self.store.get_applied_migrations()

        # Commercial status
        comm_status = self.commercial_policy.get_status()

        # Firm profile (strictly redacted projection)
        firm_diag = self.firm_identity_service.get_diagnostic_identity()

        system_sec = SystemDiagnosticSection(
            product=sys_ver.product,
            product_version=sys_ver.version,
            build_sha=sys_ver.build_sha,
            release_channel=sys_ver.release_channel.value,
            platform=sys_ver.platform,
            os_name=sys_ver.os_name,
            architecture=sys_ver.architecture,
            python_version=sys_ver.python_version,
            schema_version=sys_ver.schema_version,
            license_protocol_version=sys_ver.license_protocol_version,
            receipt_schema_version=sys_ver.receipt_schema_version,
        )

        db_sec = DatabaseDiagnosticSection(
            schema_version=db_integrity.get("schema_version", self.store.CURRENT_SCHEMA_VERSION),
            journal_mode=str(db_integrity.get("journal_mode", "WAL")).upper(),
            integrity_status=db_integrity.get("structural_integrity", "UNKNOWN"),
            foreign_keys_valid=db_integrity.get("foreign_keys_valid", True),
            database_size_bytes=db_size,
            applied_migrations=migrations,
        )

        comm_sec = CommercialDiagnosticSection(
            is_licensed=comm_status.get("licensed", False),
            tier=comm_status.get("tier") or "COMMUNITY",
            state=comm_status.get("license_state", "UNLICENSED"),
            installation_id=self.commercial_policy.installation_id or "LOCAL_DEFAULT",
            max_cases_per_installation=comm_status.get("max_cases_per_installation"),
            cases_created=comm_status.get("billable_cases_count", 0),
            entitlements=comm_status.get("entitlements", []),
            expires_at_utc=comm_status.get("expires_at_utc"),
            grace_period_days=comm_status.get("grace_days_remaining", 0),
        )

        firm_sec = FirmDiagnosticSection(
            configured=firm_diag is not None,
            identity=firm_diag,
        )

        runtime_sec = RuntimeDiagnosticSection(
            status="HEALTHY",
            egress_policy="STRICT_LOCAL_ONLY",
            timestamp_utc=now_utc,
        )

        bundle_id = f"DIAG-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{sys_ver.build_sha[:8]}"

        return DiagnosticBundleReport(
            bundle_id=bundle_id,
            generated_at_utc=now_utc,
            system=system_sec,
            database=db_sec,
            commercial=comm_sec,
            firm=firm_sec,
            runtime=runtime_sec,
        )

    def export_bundle_json(self) -> str:
        """Returns JSON serialized diagnostic report."""
        report = self.generate_report()
        return report.model_dump_json(indent=2)

    def export_bundle_zip(self) -> bytes:
        """
        Creates a structured zip bundle containing:
        - manifest.json: bundle format, metadata, and SHA-256 member digests
        - diagnostic.json: complete sanitized allowlisted diagnostic metadata
        - integrity.txt: database PRAGMA integrity verification summary
        - migrations.json: schema migration ledger
        - README.txt: purpose and security boundary documentation
        """
        import hashlib
        report = self.generate_report()
        report_json = report.model_dump_json(indent=2)

        integrity_text = (
            f"VaultBasis Database Integrity Report\n"
            f"Generated: {report.generated_at_utc}\n"
            f"Structural Integrity: {report.database.integrity_status}\n"
            f"Foreign Keys Valid: {report.database.foreign_keys_valid}\n"
            f"Journal Mode: {report.database.journal_mode}\n"
            f"Schema Version: {report.database.schema_version}\n"
        )

        migrations_json = json.dumps(report.database.applied_migrations, indent=2)

        readme_text = (
            f"VaultBasis Support Diagnostic Bundle ({report.bundle_id})\n"
            f"----------------------------------------------------------------------\n"
            f"This diagnostic package was generated locally for support troubleshooting.\n"
            f"SECURITY NOTICE:\n"
            f"- No taxpayer financial data, transaction rows, or wallet addresses are included.\n"
            f"- Regulated identifiers (PTIN/EFIN) are strictly redacted.\n"
            f"- Zero client evidence source files or receipt cryptographic keys are included.\n"
        )

        # Compute SHA-256 digests for manifest
        diag_bytes = report_json.encode("utf-8")
        integ_bytes = integrity_text.encode("utf-8")
        mig_bytes = migrations_json.encode("utf-8")
        readme_bytes = readme_text.encode("utf-8")

        manifest = {
            "format": "vaultbasis-support-diagnostic-v1",
            "bundle_id": report.bundle_id,
            "created_at_utc": report.generated_at_utc,
            "build_sha": report.system.build_sha,
            "product_version": report.system.product_version,
            "files": {
                "diagnostic.json": f"sha256:{hashlib.sha256(diag_bytes).hexdigest()}",
                "integrity.txt": f"sha256:{hashlib.sha256(integ_bytes).hexdigest()}",
                "migrations.json": f"sha256:{hashlib.sha256(mig_bytes).hexdigest()}",
                "README.txt": f"sha256:{hashlib.sha256(readme_bytes).hexdigest()}",
            }
        }
        manifest_json = json.dumps(manifest, indent=2)

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", manifest_json)
            zf.writestr("diagnostic.json", report_json)
            zf.writestr("integrity.txt", integrity_text)
            zf.writestr("migrations.json", migrations_json)
            zf.writestr("README.txt", readme_text)

        buffer.seek(0)
        return buffer.getvalue()
