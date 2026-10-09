"""
VaultBasis Edge — Local REST API Service
Conforms to PRD §18.1 (Local REST API), §62.1 (Service Contracts), §21.1 (Zero Egress)
"""

import csv
import hashlib
import io
import json
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import os
import re
import signal
import sys
import threading
import time

from apps.verifier.verify_receipt import verify_outcome_receipt
from edge.assurance.reconciliation_engine import DeterministicReconciliationEngine
from edge.assurance.rulesets import SUPPORTED_RULESETS
from edge.commercial.audit import AuditEventType, CommercialAuditService
from edge.commercial.diagnostics import DiagnosticPackager
from edge.commercial.identity import (
    FirmIdentity,
    FirmIdentityService,
)
from edge.commercial.policy import (
    CaseWritePolicy,
    CommercialOperation,
    CommercialDenialCode,
    CommercialPolicyDecision,
    CommercialPolicyService,
)
from edge.commercial.models import LicenseTier
from edge.connectors.validator import IntakeDispatcher
from edge.receipts.keygen import InstallationKeyManager
from edge.receipts.signer import ReceiptSigner
from edge.storage.sqlite_store import SQLiteStore, EvidenceCollisionError
from edge.system.version import get_system_version
from schemas.canonical.case import CanonicalCase, SourceDocumentMetadata
from schemas.canonical.transaction import CanonicalTransaction


def _resource_base() -> Path:
    # Dev/CI: repository checkout layout. Frozen (PyInstaller .app / .exe):
    # probe candidate roots for the bundled resources instead of trusting CWD,
    # so the app behaves identically wherever the user launches it from.
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates = []
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass))
        candidates += [
            exe_dir,
            exe_dir / "Resources",
            exe_dir.parent / "Resources",  # macOS Contents/MacOS -> Contents/Resources
            exe_dir.parent,
        ]
        for cand in candidates:
            if (cand / "apps" / "web-dashboard" / "index.html").is_file():
                return cand
        return candidates[0]
    return Path(__file__).resolve().parent.parent.parent


def _user_data_dir() -> Path:
    # Frozen apps must never write beside the bundle: per-OS user data location.
    if getattr(sys, "frozen", False):
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "VaultBasis"
        if sys.platform == "win32":
            base = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            return Path(base) / "VaultBasis"
        return Path.home() / ".local" / "share" / "vaultbasis"
    return Path(__file__).resolve().parent.parent.parent / "data"


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESOURCE_BASE = _resource_base()
DATA_DIR = _user_data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Initialize local key manager, SQLite store, commercial policy service, and firm identity service
KEY_DIR = DATA_DIR / "keys"
DB_FILE = os.environ.get("VAULTBASIS_DB_FILE", "vaultbasis.db")
DB_PATH = DATA_DIR / DB_FILE

key_manager = InstallationKeyManager(KEY_DIR)
priv_key, pub_key = key_manager.ensure_keypair()
receipt_signer = ReceiptSigner(priv_key)
db_store = SQLiteStore(DB_PATH)
commercial_audit_service = CommercialAuditService(
    store=db_store,
    installation_id=os.environ.get("VAULTBASIS_INSTALLATION_ID")
)
commercial_policy = CommercialPolicyService(
    store=db_store,
    license_dir=DATA_DIR / "license",
    installation_id=os.environ.get("VAULTBASIS_INSTALLATION_ID"),
    audit_service=commercial_audit_service,
    allow_dev_preview=os.environ.get("VAULTBASIS_ALLOW_DEV_PREVIEW", "false").lower() in ("true", "1", "yes"),
)
firm_identity_service = FirmIdentityService(db_store, audit_service=commercial_audit_service)
diagnostic_packager = DiagnosticPackager(db_store, commercial_policy, firm_identity_service)

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB file size limit


def sanitize_filename(filename: str) -> str:
    """Strips path traversal sequences, hostile characters, and Windows reserved names."""
    normalized = filename.replace('\x00', '').replace('\\', '/')
    clean = Path(normalized).name
    clean = re.sub(r'^\.+', '', clean)
    clean = re.sub(r'[^\w\.\-\_]', '_', clean)
    stem = Path(clean).stem.upper()
    if stem in {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}:
        clean = f"_{clean}"
    return clean or "unnamed_evidence.csv"


def sanitize_csv_cell(value: Any) -> str:
    """Neutralizes CSV formula injection characters (=, +, -, @, \\t, \\r)."""
    if value is None:
        return ""
    s = str(value)
    if s and s[0] in ('=', '+', '-', '@', '\t', '\r'):
        return f"'{s}"
    return s


app = FastAPI(
    title="VaultBasis Edge",
    description="Independent Outcome Verification and Assurance Edge (MMP-1)",
    version=get_system_version().version
)

import secrets

LOCAL_SESSION_CAPABILITY = secrets.token_hex(16)
ALLOWED_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1", "[::1]", "testserver", "local"}


@app.middleware("http")
async def security_and_host_validation_middleware(request, call_next):
    # 1. Host header validation (DNS rebinding protection)
    raw_host = request.headers.get("host", "")
    if raw_host.startswith("[") and "]" in raw_host:
        host_name = raw_host[:raw_host.index("]") + 1].lower()
    else:
        host_name = raw_host.split(":")[0].lower() if raw_host else ""
        
    if host_name and host_name not in ALLOWED_LOOPBACK_HOSTS:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": f"Invalid Host header '{host_name}'. VaultBasis Edge only accepts loopback traffic."}
        )

    # 2. Origin validation for state-mutating requests (CSRF / Cross-Origin / Hostile File origin defense)
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        origin = request.headers.get("origin")
        capability = request.headers.get("x-vaultbasis-capability")
        has_valid_capability = bool(capability and capability == LOCAL_SESSION_CAPABILITY)

        # Reject Origin: null unless presenting a valid instance-bound capability token
        if origin == "null" and not has_valid_capability:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Forbidden: 'Origin: null' mutation rejected. Must originate from verified loopback origin or present valid local session capability."}
            )
        elif origin and origin != "null":
            origin_clean = origin.split("://")[-1].split(":")[0].lower()
            if origin_clean not in ALLOWED_LOOPBACK_HOSTS and not has_valid_capability:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": f"Forbidden: Cross-origin mutation request from '{origin}' blocked."}
                )

    response = await call_next(request)

    # 3. Security Headers
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' data:; connect-src 'self' http://127.0.0.1:* http://localhost:*; frame-ancestors 'none';"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"

    # 4. Cache-Control for sensitive API endpoints
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, max-age=0, must-revalidate"

    return response


# CORS locked to loopback origins only — Edge is a local-only application.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Accept"],
)


# ------------------------------------------------------------------------------
# Request / Response Schemas
# ------------------------------------------------------------------------------

class CreateCaseRequest(BaseModel):
    case_id: Optional[str] = Field(None, description="Optional custom case ID (defaults to UUID)")
    client_reference: Optional[str] = Field("Sample Client", description="Client or engagement reference (e.g. Acme Holdings LLC)")
    tax_year: int = Field(2025, description="Target tax year")
    jurisdiction: str = Field("US", description="Regulatory jurisdiction")


class CloneCaseRequest(BaseModel):
    new_case_id: Optional[str] = Field(None, description="Optional new case ID for cloned production case")
    client_reference: Optional[str] = Field(None, description="Optional updated client reference")


class InstallLicenseRequest(BaseModel):
    token: str = Field(..., description="VaultBasis signed commercial license token string (Base64 or JSON envelope)")


class FindingReviewRequest(BaseModel):
    finding_id: str
    disposition: str = Field("REVIEWED", description="OPEN | REVIEWED | FOLLOW_UP_REQUIRED | LEFT_UNRESOLVED")
    note: Optional[str] = None
    reviewer_reference: Optional[str] = None


class FinalizeReviewRequest(BaseModel):
    reviewer_reference: Optional[str] = "Practitioner Review"
    review_notes: Optional[str] = None


class StartEvaluationRequest(BaseModel):
    customer_name: Optional[str] = Field("Evaluation Practitioner", description="Practitioner or entity reference")


class CaseSummaryResponse(BaseModel):
    case_id: str
    client_reference: Optional[str] = "Sample Client"
    tax_year: int
    jurisdiction: str
    case_status: str
    outcome_state: Optional[str]
    assurance_level: Optional[str]
    receipt_id: Optional[str]
    created_at: str
    updated_at: str


# ------------------------------------------------------------------------------
# Sample Case Fixtures
# ------------------------------------------------------------------------------

SAMPLE_1099DA_CSV = b"""Property,Date sold,Proceeds,Date acquired,Cost basis,Box 2
BTC,2025-11-20,18400.00,2025-02-11,12100.00,YES
ETH,2025-12-05,3200.00,2025-03-01,2800.00,YES
SOL,2025-08-14,4500.00,2025-01-10,,NO
AVAX,2025-09-10,9950.00,2025-01-01,8000.00,YES
LINK,2025-10-01,1500.00,2025-04-01,1200.00,YES
"""

SAMPLE_KOINLY_CSV = b"""Date,Asset,Amount,Cost basis,Proceeds,Gain / loss,Date acquired
2025-11-20,BTC,1.0,16300.00,18400.00,2100.00,2025-02-11
2025-12-05,ETH,1.0,2800.00,3200.00,400.00,2025-03-01
2025-08-14,SOL,30.0,4000.00,4500.00,500.00,2025-01-10
2025-09-10,AVAX,500.0,8000.00,10000.00,2000.00,2025-01-01
2025-10-01,LINK,100.0,1200.00,1500.00,300.00,2025-04-01
"""


# ------------------------------------------------------------------------------
# API Endpoints
# ------------------------------------------------------------------------------

@app.get("/api/health")
@app.get("/health")
def health_check():
    sys_ver = get_system_version()
    return {
        "status": "HEALTHY",
        "readiness": "ready",
        "database": "ready",
        "migrations": "ready",
        "frontend_assets": "ready",
        "service": "VaultBasis Edge",
        "version": sys_ver.version,
        "source_commit": sys_ver.build_sha,
        "installation_key_id": receipt_signer.key_id,
        "egress_policy": "STRICT_LOCAL_ONLY",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }




@app.get("/api/system/version")
def get_version_info():
    """
    Returns immutable build, release channel, schema version, and compatibility metadata.
    Read-only, strictly local, zero network egress.
    """
    return get_system_version().model_dump()


@app.get("/api/system/diagnostic")
def get_system_diagnostic():
    """
    Returns positive-allowlisted sanitized diagnostic report for support and operational triage.
    STRICT PRIVACY GUARANTEE: Zero financial data, transaction rows, evidence files, private keys, or raw PTIN/EFIN.
    """
    report = diagnostic_packager.generate_report()
    commercial_audit_service.record_event(
        AuditEventType.DIAGNOSTIC_EXPORTED,
        actor_type="USER",
        details={"bundle_id": report.bundle_id, "format": "JSON"}
    )
    return report.model_dump()


@app.get("/api/system/diagnostic/bundle")
def download_diagnostic_bundle():
    """
    Downloads structured ZIP bundle containing diagnostic.json, integrity.txt, migrations.json, and README.txt.
    """
    report = diagnostic_packager.generate_report()
    commercial_audit_service.record_event(
        AuditEventType.DIAGNOSTIC_EXPORTED,
        actor_type="USER",
        details={"bundle_id": report.bundle_id, "format": "ZIP"}
    )
    bundle_zip_bytes = diagnostic_packager.export_bundle_zip()
    filename = f"VaultBasis_Support_Diagnostic_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
    return Response(
        content=bundle_zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/api/system/quit")
@app.post("/api/system/shutdown")
def quit_vaultbasis():
    """
    Safely terminates the local VaultBasis Edge process.
    Performs full SQLite WAL checkpoint, flushes pending state, and exits.
    """
    try:
        db_store.checkpoint_wal()
    except Exception:
        pass

    def _shutdown_worker():
        time.sleep(0.25)
        try:
            os.kill(os.getpid(), signal.SIGTERM)
        except Exception:
            os._exit(0)

    threading.Thread(target=_shutdown_worker, daemon=True).start()
    return {
        "status": "SHUTTING_DOWN",
        "message": "VaultBasis Edge is closing safely. Database checkpointed, sockets closing.",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/commercial/audit")
def get_commercial_audit_events(limit: int = 100, offset: int = 0):
    """
    Returns paginated tamper-evident administrative audit events and hash chain verification status.
    Strictly administrative scope: license changes, firm profile mutations, diagnostic exports.
    """
    events = [e.model_dump() for e in commercial_audit_service.get_events(limit=limit, offset=offset)]
    total_count = commercial_audit_service.count_events()
    chain_status = commercial_audit_service.verify_chain_integrity()
    return {
        "events": events,
        "total_count": total_count,
        "chain_integrity": chain_status,
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/commercial/status")
def get_commercial_status():
    """
    Returns non-sensitive commercial entitlement status and case capacity metrics.
    Safe for UI dashboard rendering and operational health diagnostics.
    """
    return commercial_policy.get_status()


@app.post("/api/commercial/license")
def install_commercial_license(req: InstallLicenseRequest):
    """
    Installs and evaluates a local offline commercial license token.
    Persists token in local storage upon successful evaluation.
    """
    res = commercial_policy.install_license_token(req.token)
    return {
        "status": "INSTALLED" if res.is_active else "REJECTED",
        "license_state": res.state.value,
        "tier": res.tier.value if res.tier else None,
        "license_id": res.license_id,
        "customer_id": res.customer_id,
        "max_cases_per_installation": res.max_cases_per_installation,
        "entitlements": res.entitlements,
        "days_remaining": res.days_remaining,
        "grace_days_remaining": res.grace_days_remaining,
        "diagnostic_reason": res.diagnostic_reason,
    }


@app.post("/api/commercial/start-evaluation")
def start_evaluation(req: Optional[StartEvaluationRequest] = None):
    """
    Activates an authentic 72-hour Evaluation entitlement (MMP15-EVAL-E2E-001).
    Signs and installs a valid Evaluation token with 1 client case capacity.
    """
    name = (req.customer_name if req and req.customer_name else "Evaluation Practitioner")
    res = commercial_policy.start_evaluation(customer_name=name)
    return {
        "status": "INSTALLED" if res.is_active else "REJECTED",
        "license_state": res.state.value,
        "tier": res.tier.value if res.tier else None,
        "license_id": res.license_id,
        "customer_id": res.customer_id,
        "max_cases_per_installation": res.max_cases_per_installation,
        "entitlements": res.entitlements,
        "days_remaining": res.days_remaining,
        "grace_days_remaining": res.grace_days_remaining,
        "diagnostic_reason": res.diagnostic_reason,
    }


@app.get("/api/firm/identity")
def get_firm_identity():
    """
    Returns public metadata of active firm and workspace identity profile.
    STRICT PRIVACY GUARANTEE: Regulated identifiers (PTIN/EFIN) are strictly isolated and omitted.
    """
    ident = firm_identity_service.get_public_identity()
    if not ident:
        return {
            "configured": False,
            "organization_id": None,
            "firm_name": None,
            "office_id": None,
            "workspace_id": "WS-DEFAULT",
            "preparer_id": None,
            "display_name": None,
            "has_ptin_configured": False,
            "has_efin_configured": False,
        }
    return {"configured": True, **ident}


@app.post("/api/firm/identity")
def update_firm_identity(identity: FirmIdentity):
    """
    Saves or updates local firm, workspace, practitioner, and regulated identifiers.
    Regulated identifiers are stored locally and never emitted in public receipts.
    """
    saved = firm_identity_service.save_identity(identity)
    return {
        "status": "SAVED",
        "configured": True,
        **saved.to_public_metadata()
    }


@app.delete("/api/firm/identity")
def clear_firm_identity():
    """Clears stored firm and workspace identity profile."""
    firm_identity_service.clear_identity()
    return {"status": "CLEARED", "configured": False}


@app.post("/api/sample-case/load")
def load_sample_case():
    """
    Preload the canonical Sample Case for zero-knowledge onboarding.
    Populates Source A (Broker Form 1099-DA) and Source B (Tax-Ledger Koinly Report).
    Explicitly unmetered — does not count against commercial case capacity.
    """
    case_id = "CASE-SAMPLE-2025"
    client_ref = "Sample Client (Acme Holdings LLC)"
    now_utc = datetime.now(timezone.utc).isoformat()
    manifest_digest = hashlib.sha256(SAMPLE_1099DA_CSV + SAMPLE_KOINLY_CSV).hexdigest()

    existing = db_store.get_case(case_id)
    if not existing:
        case = CanonicalCase(
            case_id=case_id,
            client_reference=client_ref,
            tax_year=2025,
            jurisdiction="US",
            case_status="CREATED",
            case_kind="BUNDLED_SAMPLE",
            sample_definition_id="SAMPLE-A-2025-01",
            sample_manifest_digest=manifest_digest,
            created_at=now_utc,
            updated_at=now_utc
        )
        db_store.save_case(case)
    else:
        # Guarantee sample metadata and provenance are maintained on reload
        if existing.case_kind != "BUNDLED_SAMPLE" or not existing.sample_definition_id or not existing.sample_manifest_digest:
            existing.case_kind = "BUNDLED_SAMPLE"
            existing.sample_definition_id = "SAMPLE-A-2025-01"
            existing.sample_manifest_digest = manifest_digest
            db_store.save_case(existing)

    # Ingest Source A (Broker 1099-DA) if not already present
    src_a_id = f"SRC-SAMPLE_1099DA"
    try:
        meta_a, txs_a = IntakeDispatcher.ingest_document(
            data_bytes=SAMPLE_1099DA_CSV,
            filename="Sample_Coinbase_1099DA.csv",
            source_id=src_a_id,
            declared_schema="AUTO"
        )
        db_store.add_source_and_transactions(case_id, meta_a, SAMPLE_1099DA_CSV, txs_a)
    except EvidenceCollisionError:
        pass

    # Ingest Source B (Tax-Ledger Koinly) if not already present
    src_b_id = f"SRC-SAMPLE_KOINLY"
    try:
        meta_b, txs_b = IntakeDispatcher.ingest_document(
            data_bytes=SAMPLE_KOINLY_CSV,
            filename="Sample_Koinly_Capital_Gains.csv",
            source_id=src_b_id,
            declared_schema="AUTO"
        )
        db_store.add_source_and_transactions(case_id, meta_b, SAMPLE_KOINLY_CSV, txs_b)
    except EvidenceCollisionError:
        pass

    return get_case(case_id)


@app.post("/api/sample-case/reset")
def reset_sample_case():
    """
    Resets the canonical sample case to its pristine, unreconciled baseline state.
    Clears any generated receipt/findings while preserving the immutable authentic sources.
    """
    case_id = "CASE-SAMPLE-2025"
    case = db_store.get_case(case_id)
    if not case:
        return load_sample_case()

    case.case_status = "SOURCES_INGESTED"
    case.outcome_state = None
    case.assurance_level = None
    if case.receipt_id:
        db_store.delete_receipt(case.receipt_id)
    case.receipt_id = None
    case.updated_at = datetime.now(timezone.utc).isoformat()
    db_store.save_case(case)
    return get_case(case_id)


@app.post("/api/cases/{case_id}/reset")
def reset_case_by_id(case_id: str):
    """
    Resets a sample case by ID.
    """
    if case_id == "CASE-SAMPLE-2025":
        return reset_sample_case()
    case = db_store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")
    if getattr(case, "case_kind", "PRODUCTION") == "BUNDLED_SAMPLE":
        case.case_status = "SOURCES_INGESTED"
        case.outcome_state = None
        case.assurance_level = None
        if case.receipt_id:
            db_store.delete_receipt(case.receipt_id)
        case.receipt_id = None
        case.updated_at = datetime.now(timezone.utc).isoformat()
        db_store.save_case(case)
        return get_case(case_id)
    raise HTTPException(status_code=400, detail="Only sample cases support automated reset.")


@app.post("/api/cases", response_model=CaseSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_case(req: CreateCaseRequest):
    case_id = req.case_id or f"CASE-{uuid.uuid4().hex[:8].upper()}"
    client_ref = req.client_reference or "Sample Client"
    existing = db_store.get_case(case_id)
    if existing:
        return CaseSummaryResponse(
            case_id=existing.case_id,
            client_reference=existing.client_reference,
            tax_year=existing.tax_year,
            jurisdiction=existing.jurisdiction,
            case_status=existing.case_status,
            outcome_state=existing.outcome_state,
            assurance_level=existing.assurance_level,
            receipt_id=existing.receipt_id,
            created_at=existing.created_at,
            updated_at=existing.updated_at
        )

    # Evaluate commercial entitlement before persisting new billable case
    decision = commercial_policy.authorize(CommercialOperation.CREATE_CASE)
    if not decision.allowed:
        return JSONResponse(
            status_code=decision.http_status,
            content=decision.to_error_dict()
        )

    now_utc = datetime.now(timezone.utc).isoformat()

    case = CanonicalCase(
        case_id=case_id,
        client_reference=client_ref,
        tax_year=req.tax_year,
        jurisdiction=req.jurisdiction,
        case_status="CREATED",
        case_kind="PRODUCTION",
        created_at=now_utc,
        updated_at=now_utc
    )
    eval_res = commercial_policy.evaluate_current_license()
    is_eval = (eval_res.tier in (LicenseTier.TRIAL, LicenseTier.EVALUATION))
    max_cases = eval_res.max_cases_per_installation or (3 if is_eval else 0)
    eval_state = db_store.get_installation_evaluation() if is_eval else None
    since_iso = eval_state.get("activated_at") if (is_eval and eval_state) else None

    try:
        db_store.create_case_atomic(
            case=case,
            is_evaluation=is_eval,
            max_cases=max_cases,
            since_iso=since_iso
        )
    except ValueError as e:
        denial = commercial_policy.authorize(CommercialOperation.CREATE_CASE)
        return JSONResponse(
            status_code=denial.http_status,
            content=denial.to_error_dict()
        )

    return CaseSummaryResponse(
        case_id=case.case_id,
        client_reference=case.client_reference,
        tax_year=case.tax_year,
        jurisdiction=case.jurisdiction,
        case_status=case.case_status,
        outcome_state=case.outcome_state,
        assurance_level=case.assurance_level,
        receipt_id=case.receipt_id,
        created_at=case.created_at,
        updated_at=case.updated_at
    )


@app.post("/api/cases/{case_id}/clone", response_model=CaseSummaryResponse, status_code=status.HTTP_201_CREATED)
def clone_case(case_id: str, req: Optional[CloneCaseRequest] = None):
    """
    Clones an existing case (sample or template) into a new production case.
    Cloned cases immediately lose bundled sample provenance, are assigned case_kind='PRODUCTION',
    and require active commercial entitlement to create and reconcile.
    """
    source_case = db_store.get_case(case_id)
    if not source_case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    # Evaluate commercial entitlement for creating a new production case
    decision = commercial_policy.authorize(CommercialOperation.CREATE_CASE)
    if not decision.allowed:
        return JSONResponse(
            status_code=decision.http_status,
            content=decision.to_error_dict()
        )

    now_utc = datetime.now(timezone.utc).isoformat()
    new_id = (req.new_case_id if req and req.new_case_id else None) or f"CASE-{uuid.uuid4().hex[:8].upper()}"
    new_client_ref = (req.client_reference if req and req.client_reference else None) or f"Copy of {getattr(source_case, 'client_reference', 'Case')}"

    eval_res = commercial_policy.evaluate_current_license()
    is_eval = (eval_res.tier in (LicenseTier.TRIAL, LicenseTier.EVALUATION))
    max_cases = eval_res.max_cases_per_installation or (3 if is_eval else 0)
    eval_state = db_store.get_installation_evaluation() if is_eval else None
    since_iso = eval_state.get("activated_at") if (is_eval and eval_state) else None

    cloned_sources = {}
    cloned_transactions = []
    source_payloads = []

    for src_id, src_meta in source_case.sources.items():
        new_src_id = f"SRC-{uuid.uuid4().hex[:6].upper()}_{Path(src_meta.filename).stem}"
        new_meta = SourceDocumentMetadata(
            source_id=new_src_id,
            filename=src_meta.filename,
            sha256_hash=src_meta.sha256_hash,
            byte_size=src_meta.byte_size,
            schema_id=src_meta.schema_id,
            row_count=src_meta.row_count,
            ingested_at=now_utc
        )
        cloned_sources[new_src_id] = new_meta

        raw_bytes = db_store.get_source_file_bytes(src_id)
        if raw_bytes is None:
            if "1099" in src_meta.filename:
                raw_bytes = SAMPLE_1099DA_CSV
            else:
                raw_bytes = SAMPLE_KOINLY_CSV

        txs = []
        for t in source_case.transactions:
            if t.source_id == src_id:
                t_dict = t.model_dump()
                t_dict["source_id"] = new_src_id
                t_dict["transaction_id"] = f"{new_src_id}_{t.source_row_reference}"
                txs.append(CanonicalTransaction(**t_dict))
        cloned_transactions.extend(txs)
        source_payloads.append((new_meta, raw_bytes, txs))

    cloned_case = CanonicalCase(
        case_id=new_id,
        client_reference=new_client_ref,
        tax_year=source_case.tax_year,
        jurisdiction=source_case.jurisdiction,
        case_status="SOURCES_INGESTED" if cloned_sources else "CREATED",
        case_kind="PRODUCTION",
        sample_definition_id=None,
        sample_manifest_digest=None,
        sources=cloned_sources,
        transactions=cloned_transactions,
        created_at=now_utc,
        updated_at=now_utc
    )

    try:
        db_store.create_case_atomic(
            case=cloned_case,
            is_evaluation=is_eval,
            max_cases=max_cases,
            since_iso=since_iso
        )
    except ValueError:
        denial = commercial_policy.authorize(CommercialOperation.CREATE_CASE)
        return JSONResponse(
            status_code=denial.http_status,
            content=denial.to_error_dict()
        )

    # Persist cloned sources and transactions into db_store for the new case
    for meta, raw_bytes, txs in source_payloads:
        try:
            db_store.add_source_and_transactions(new_id, meta, raw_bytes, txs)
        except EvidenceCollisionError:
            pass

    return CaseSummaryResponse(
        case_id=cloned_case.case_id,
        client_reference=cloned_case.client_reference,
        tax_year=cloned_case.tax_year,
        jurisdiction=cloned_case.jurisdiction,
        case_status=cloned_case.case_status,
        outcome_state=cloned_case.outcome_state,
        assurance_level=cloned_case.assurance_level,
        receipt_id=cloned_case.receipt_id,
        created_at=cloned_case.created_at,
        updated_at=cloned_case.updated_at
    )


def _derive_case_metadata(case_dict_or_obj: Any) -> Dict[str, Any]:
    if isinstance(case_dict_or_obj, dict):
        outcome_state = case_dict_or_obj.get("outcome_state")
        case_status = case_dict_or_obj.get("case_status", "CREATED")
        sources_summary = case_dict_or_obj.get("sources_summary", [])
        if not sources_summary and "sources" in case_dict_or_obj:
            sources_dict = case_dict_or_obj.get("sources") or {}
            sources_summary = [{"schema_id": getattr(s, "schema_id", s.get("schema_id") if isinstance(s, dict) else "")} for s in sources_dict.values()]
    else:
        outcome_state = getattr(case_dict_or_obj, "outcome_state", None)
        case_status = getattr(case_dict_or_obj, "case_status", "CREATED")
        sources = getattr(case_dict_or_obj, "sources", {}) or {}
        sources_summary = [{"schema_id": s.schema_id} for s in sources.values()]

    schema_ids = [str(s.get("schema_id", "")).upper() for s in sources_summary]
    has_1099da = any("1099" in sid for sid in schema_ids)
    has_ledger = any("KOINLY" in sid or "LEDGER" in sid or "COINTRACKER" in sid for sid in schema_ids)

    # Determine evidence status and action based on actual source presence
    has_both_sources = (has_1099da and has_ledger) or len(sources_summary) >= 2
    if has_both_sources:
        workflow_status = "READY_TO_RECONCILE" if not outcome_state else "RECONCILED"
        evidence_gap = "NONE"
        evidence_status_label = "Ready to Reconcile" if not outcome_state else "Reconciled"
        next_action_label = "Run deterministic reconciliation →" if not outcome_state else "View Evidence Receipt →"
    elif has_1099da and not has_ledger:
        workflow_status = "NEEDS_EVIDENCE"
        evidence_gap = "MISSING_LEDGER"
        evidence_status_label = "Missing tax ledger"
        next_action_label = "Add client ledger →"
    elif has_ledger and not has_1099da:
        workflow_status = "NEEDS_EVIDENCE"
        evidence_gap = "MISSING_1099DA"
        evidence_status_label = "Missing broker evidence"
        next_action_label = "Add Form 1099-DA →"
    elif case_status in ("INGESTION_FAILED", "VALIDATION_FAILED"):
        workflow_status = "NEEDS_EVIDENCE"
        evidence_gap = "SOURCE_REJECTED"
        evidence_status_label = "Source rejected"
        next_action_label = "Review import error →"
    else:
        workflow_status = "NEEDS_EVIDENCE"
        evidence_gap = "MISSING_BOTH"
        evidence_status_label = "Missing both sources"
        next_action_label = "Complete intake →"

    if outcome_state:
        workflow_status = "RECONCILED"

    # attention_status: deterministic classification
    # Needs Attention =
    #   reconciliation discrepancy (DIFFERENCE_IDENTIFIED / UNRESOLVED / AMBIGUOUS)
    #   OR ingestion / validation / reconciliation failure
    #   OR data integrity warnings
    if outcome_state in ("DIFFERENCE_IDENTIFIED", "UNRESOLVED", "AMBIGUOUS_MATCH", "PROCEEDS_DIFFERENCE", "BASIS_DIFFERENCE", "UNRESOLVED_DATA"):
        attention_status = "REVIEW_REQUIRED"
    elif case_status in ("INGESTION_FAILED", "VALIDATION_FAILED", "RECONCILIATION_FAILED", "ERROR"):
        attention_status = "ERROR"
    else:
        attention_status = "NONE"

    return {
        "workflow_status": workflow_status,
        "attention_status": attention_status,
        "evidence_gap": evidence_gap,
        "evidence_status_label": evidence_status_label,
        "next_action_label": next_action_label,
    }


@app.get("/api/cases", response_model=List[Dict[str, Any]])
def list_cases():
    raw_cases = db_store.list_cases()
    enriched = []
    for c in raw_cases:
        meta = _derive_case_metadata(c)
        c_copy = dict(c)
        c_copy.update(meta)
        enriched.append(c_copy)
    return enriched


@app.delete("/api/cases/{case_id}")
def delete_case(case_id: str):
    case = db_store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")
    CaseWritePolicy.assert_can_mutate(case, "deletion")
    db_store.delete_case(case_id)
    return {"status": "DELETED", "case_id": case_id}


@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    case = db_store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")
    
    is_sample = (getattr(case, "case_kind", "PRODUCTION") == "BUNDLED_SAMPLE" or case.case_id == "CASE-SAMPLE-2025")
    recon_decision = commercial_policy.authorize(
        CommercialOperation.RECONCILE_CASE,
        context={"case_id": case.case_id, "case_kind": getattr(case, "case_kind", "PRODUCTION")}
    )
    can_reconcile = (len(case.sources) >= 2) and recon_decision.allowed
    meta = _derive_case_metadata(case)

    # Attach existing reconciliation and receipt findings if case has been reconciled
    reconciliation_data = None
    receipt_data = None
    if case.receipt_id:
        receipt_data = db_store.get_receipt(case.receipt_id)
        if len(case.sources) >= 2:
            try:
                recon_res = DeterministicReconciliationEngine.reconcile_case(case)
                reconciliation_data = recon_res.to_dict()
            except Exception:
                if receipt_data:
                    reconciliation_data = {
                        "outcome_state": receipt_data.get("outcome_state"),
                        "assurance_level": receipt_data.get("assurance_level"),
                        "material_differences": receipt_data.get("material_differences", []),
                        "unresolved_items": receipt_data.get("unresolved_items", []),
                        "agreed_records": [],
                        "total_evaluated_count": len(receipt_data.get("material_differences", [])) + len(receipt_data.get("unresolved_items", []))
                    }
        elif receipt_data:
            reconciliation_data = {
                "outcome_state": receipt_data.get("outcome_state"),
                "assurance_level": receipt_data.get("assurance_level"),
                "material_differences": receipt_data.get("material_differences", []),
                "unresolved_items": receipt_data.get("unresolved_items", []),
                "agreed_records": [],
                "total_evaluated_count": len(receipt_data.get("material_differences", [])) + len(receipt_data.get("unresolved_items", []))
            }

    reviews_data = db_store.get_finding_reviews(case.case_id)
    receipts_history = db_store.list_receipts_for_case(case.case_id)

    # Return structured case details with domain actions
    return {
        "case_id": case.case_id,
        "client_reference": getattr(case, "client_reference", "Sample Client") or "Sample Client",
        "tax_year": case.tax_year,
        "jurisdiction": case.jurisdiction,
        "case_status": case.case_status,
        "workflow_status": meta["workflow_status"],
        "attention_status": meta["attention_status"],
        "case_kind": getattr(case, "case_kind", "PRODUCTION") or "PRODUCTION",
        "sample_definition_id": getattr(case, "sample_definition_id", None),
        "outcome_state": case.outcome_state,
        "assurance_level": case.assurance_level,
        "receipt_id": case.receipt_id,
        "reconciliation": reconciliation_data,
        "receipt": receipt_data,
        "reviews": reviews_data,
        "receipt_history": receipts_history,
        "sources": {k: v.model_dump() for k, v in case.sources.items()},
        "transactions": [t.to_summary_dict() for t in case.transactions],
        "created_at": case.created_at,
        "updated_at": case.updated_at,
        "actions": {
            "can_reconcile": can_reconcile,
            "can_upload_source_a": not is_sample and case.receipt_id is None,
            "can_upload_source_b": not is_sample and case.receipt_id is None,
            "can_clone": True,
            "can_view_receipt": case.receipt_id is not None,
            "can_finalize_review": case.receipt_id is not None and not is_sample,
            "can_record_reviews": not is_sample,
            "is_sample": is_sample,
            "can_restart_sample": is_sample,
        }
    }



@app.post("/api/cases/{case_id}/sources")
async def upload_source(
    case_id: str,
    file: UploadFile = File(...),
    source_type: str = Form("AUTO")
):
    case = db_store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    CaseWritePolicy.assert_can_mutate(case, "evidence uploads or modifications")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum allowed size of {MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
        )

    safe_filename = sanitize_filename(file.filename or "evidence.csv")
    source_id = f"SRC-{uuid.uuid4().hex[:6].upper()}_{Path(safe_filename).stem}"
    try:
        meta, transactions = IntakeDispatcher.ingest_document(
            data_bytes=content,
            filename=safe_filename,
            source_id=source_id,
            declared_schema=source_type
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Intake parser failure: {str(e)}")

    try:
        db_store.add_source_and_transactions(case_id, meta, content, transactions)
    except EvidenceCollisionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {
        "status": "INGESTED",
        "case_id": case_id,
        "source": meta.model_dump(),
        "parsed_rows": len(transactions)
    }


@app.post("/api/cases/{case_id}/reconcile")
def reconcile_case(case_id: str):
    case = db_store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    decision = commercial_policy.authorize(
        CommercialOperation.RECONCILE_CASE,
        context={
            "case_id": case_id,
            "case_kind": getattr(case, "case_kind", "PRODUCTION") or "PRODUCTION"
        }
    )
    if not decision.allowed:
        return JSONResponse(
            status_code=decision.http_status,
            content=decision.to_error_dict()
        )

    if getattr(case, "case_kind", "PRODUCTION") == "BUNDLED_SAMPLE" and case.receipt_id and case.case_status == "RECONCILED":
        existing_receipt = db_store.get_receipt(case.receipt_id)
        if existing_receipt:
            return {
                "status": "RECEIPT_ALREADY_ISSUED",
                "case_id": case_id,
                "outcome_state": case.outcome_state,
                "assurance_level": case.assurance_level,
                "receipt_id": case.receipt_id,
                "reconciliation": DeterministicReconciliationEngine.reconcile_case(case).to_dict(),
                "receipt": existing_receipt
            }

    if len(case.sources) < 2:
        raise HTTPException(
            status_code=400,
            detail="Reconciliation requires at least two source documents (e.g. Form 1099-DA and Koinly CSV)"
        )

    # Enforce approved rule pack routing (fail closed if jurisdiction / tax_year is unsupported)
    normative_jurisdiction = (case.jurisdiction or "").strip().upper()
    ruleset_key = (normative_jurisdiction, case.tax_year)
    if ruleset_key not in SUPPORTED_RULESETS:
        raise HTTPException(
            status_code=422,
            detail=f"RULESET_UNSUPPORTED: No approved ruleset available for jurisdiction '{case.jurisdiction}' and tax year {case.tax_year}. Supported combinations: US / 2025 (Ruleset: VB_US_1099DA_2025_R1)."
        )
    ruleset_id = SUPPORTED_RULESETS[ruleset_key]

    # Compute manifest hash of sources
    current_manifest = hashlib.sha256(
        json.dumps(
            sorted((sid, s.sha256_hash) for sid, s in case.sources.items())
        ).encode()
    ).hexdigest()

    # Execute deterministic reconciliation
    recon_result = DeterministicReconciliationEngine.reconcile_case(case)

    # Build Outcome Receipt Payload (Preliminary Receipt)
    receipt_id = str(uuid.uuid4())
    source_hashes = {s.source_id: s.sha256_hash for s in case.sources.values()}
    source_schema_ids = {s.source_id: s.schema_id for s in case.sources.values()}
    sys_ver = get_system_version()
    revisions = db_store.list_receipts_for_case(case_id)
    revision_num = len(revisions) + 1

    receipt_payload = {
        "receipt_version": "v0.1",
        "receipt_id": receipt_id,
        "case_id": case.case_id,
        "revision": revision_num,
        "claim_type": "DIGITAL_ASSET_TAX_RECONCILIATION",
        "claimant_type": "TAXPAYER",
        "producer_reference": f"VaultBasis Edge v{sys_ver.version}",
        "source_ids": list(case.sources.keys()),
        "source_hashes": source_hashes,
        "source_schema_ids": source_schema_ids,
        "canonicalization_version": "v0.1",
        "ruleset_id": ruleset_id,
        "engine_version": sys_ver.version,
        "policy_version": "1.5.0",
        "assurance_level": recon_result.assurance_level,
        "outcome_state": recon_result.outcome_state,
        "material_differences": [d.to_dict() for d in recon_result.material_differences],
        "unresolved_items": recon_result.unresolved_items,
        "human_review_state": "UNREVIEWED",
        "ai_involvement_level": "NONE",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # Cryptographically sign preliminary receipt
    signed_receipt = receipt_signer.sign_receipt(receipt_payload)

    # Persist receipt and transition case to RECONCILED (Preliminary stage)
    db_store.save_receipt(receipt_id, case.case_id, signed_receipt, case_status="RECONCILED", revision=revision_num)
    case.outcome_state = recon_result.outcome_state
    case.assurance_level = recon_result.assurance_level
    case.receipt_id = receipt_id
    case.case_status = "RECONCILED"
    db_store.save_case(case)

    return {
        "status": "RECONCILED",
        "case_id": case_id,
        "outcome_state": recon_result.outcome_state,
        "assurance_level": recon_result.assurance_level,
        "receipt_id": receipt_id,
        "revision": revision_num,
        "human_review_state": "UNREVIEWED",
        "reconciliation": recon_result.to_dict(),
        "receipt": signed_receipt
    }


@app.get("/api/cases/{case_id}/reviews")
def get_case_reviews(case_id: str):
    case = db_store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")
    reviews = db_store.get_finding_reviews(case_id)
    return {
        "case_id": case_id,
        "reviews": reviews
    }


@app.post("/api/cases/{case_id}/reviews")
def record_finding_review(case_id: str, req: FindingReviewRequest):
    case = db_store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")
    CaseWritePolicy.assert_can_mutate(case, "practitioner review annotations")
    valid_dispositions = {"OPEN", "REVIEWED", "FOLLOW_UP_REQUIRED", "LEFT_UNRESOLVED"}
    if req.disposition not in valid_dispositions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid disposition '{req.disposition}'. Expected one of {valid_dispositions}"
        )
    db_store.save_finding_review(
        case_id=case_id,
        finding_id=req.finding_id,
        disposition=req.disposition,
        note=req.note,
        reviewer_reference=req.reviewer_reference or "Practitioner Review"
    )
    return {
        "status": "RECORDED",
        "case_id": case_id,
        "finding_id": req.finding_id,
        "disposition": req.disposition,
        "reviews": db_store.get_finding_reviews(case_id)
    }


@app.post("/api/cases/{case_id}/finalize-review")
def finalize_practitioner_review(case_id: str, req: Optional[FinalizeReviewRequest] = None):
    case = db_store.get_case(case_id)
    if not case or not case.receipt_id:
        raise HTTPException(status_code=400, detail="Case must be reconciled before finalizing review.")
    CaseWritePolicy.assert_can_mutate(case, "practitioner review finalization")

    prelim_receipt = db_store.get_receipt(case.receipt_id)
    if not prelim_receipt:
        raise HTTPException(status_code=404, detail="Preliminary receipt not found.")

    diffs = prelim_receipt.get("material_differences", [])
    unres = prelim_receipt.get("unresolved_items", [])
    total_findings = len(diffs) + len(unres)

    final_review_state = "REVIEWED_ACCEPTED" if total_findings == 0 else "REVIEWED_ANNOTATED"

    final_receipt_id = str(uuid.uuid4())
    revisions = db_store.list_receipts_for_case(case_id)
    revision_num = len(revisions) + 1

    final_payload = dict(prelim_receipt)
    final_payload["receipt_id"] = final_receipt_id
    final_payload["revision"] = revision_num
    final_payload["prior_receipt_id"] = prelim_receipt.get("receipt_id")
    final_payload["human_review_state"] = final_review_state
    final_payload["created_at"] = datetime.now(timezone.utc).isoformat()
    final_payload.pop("signature", None)
    final_payload.pop("signer_public_key", None)
    final_payload.pop("signer_key_id", None)

    signed_final = receipt_signer.sign_receipt(final_payload)
    db_store.save_receipt(
        final_receipt_id,
        case_id,
        signed_final,
        case_status="RECEIPT_ISSUED",
        revision=revision_num
    )
    case.case_status = "RECEIPT_ISSUED"
    case.receipt_id = final_receipt_id
    db_store.save_case(case)

    return {
        "status": "REVIEW_FINALIZED",
        "case_id": case_id,
        "receipt_id": final_receipt_id,
        "revision": revision_num,
        "prior_receipt_id": prelim_receipt.get("receipt_id"),
        "human_review_state": final_review_state,
        "receipt": signed_final
    }


@app.get("/api/cases/{case_id}/receipt")
def get_receipt(case_id: str):
    case = db_store.get_case(case_id)
    if not case or not case.receipt_id:
        raise HTTPException(status_code=404, detail="No receipt found for this case")

    receipt = db_store.get_receipt(case.receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt record not found")
    return receipt


# ------------------------------------------------------------------------------
# Three-Tier Evidence Export Architecture (MMP15-GOLDEN-RESULT-CLOSURE-001)
# ------------------------------------------------------------------------------

def _build_findings_csv(case: CanonicalCase, receipt: Dict[str, Any], reviews: Dict[str, Any]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["# VaultBasis Findings Workpaper"])
    writer.writerow(["# Case ID", sanitize_csv_cell(case.case_id)])
    writer.writerow(["# Tax Year", sanitize_csv_cell(case.tax_year)])
    writer.writerow(["# Receipt ID", sanitize_csv_cell(receipt.get("receipt_id", ""))])
    writer.writerow(["# Outcome State", sanitize_csv_cell(receipt.get("outcome_state", ""))])
    writer.writerow(["# Human Review State", sanitize_csv_cell(receipt.get("human_review_state", ""))])
    writer.writerow([])
    writer.writerow([
        "Finding_ID",
        "Finding_Type",
        "Classification_or_Reason",
        "Asset",
        "Source_A_Ref",
        "Source_A_Value",
        "Source_B_Ref",
        "Source_B_Value",
        "Variance",
        "Description",
        "Review_Disposition",
        "Practitioner_Note",
        "Reviewer_Ref"
    ])
    for d in receipt.get("material_differences", []):
        f_id = d.get("difference_id", "")
        rev = reviews.get(f_id, {})
        writer.writerow([
            sanitize_csv_cell(f_id),
            "MATERIAL_DIFFERENCE",
            sanitize_csv_cell(d.get("difference_state", "")),
            sanitize_csv_cell(d.get("asset", "")),
            sanitize_csv_cell(d.get("source_a_ref", "")),
            sanitize_csv_cell(d.get("source_a_value", "")),
            sanitize_csv_cell(d.get("source_b_ref", "")),
            sanitize_csv_cell(d.get("source_b_value", "")),
            sanitize_csv_cell(d.get("variance", "")),
            sanitize_csv_cell(d.get("description", "")),
            sanitize_csv_cell(rev.get("disposition", "OPEN")),
            sanitize_csv_cell(rev.get("note", "")),
            sanitize_csv_cell(rev.get("reviewer_reference", ""))
        ])
    for u in receipt.get("unresolved_items", []):
        u_id = u.get("item_id", "")
        rev = reviews.get(u_id, {})
        writer.writerow([
            sanitize_csv_cell(u_id),
            "UNRESOLVED_ITEM",
            sanitize_csv_cell(u.get("reason_code", "")),
            sanitize_csv_cell(u.get("affected_source_id", "")),
            sanitize_csv_cell(u.get("affected_row_ref", "")),
            "",
            "",
            "",
            "",
            sanitize_csv_cell(u.get("description", "")),
            sanitize_csv_cell(rev.get("disposition", "OPEN")),
            sanitize_csv_cell(rev.get("note", "")),
            sanitize_csv_cell(rev.get("reviewer_reference", ""))
        ])
    return buf.getvalue()


@app.get("/api/cases/{case_id}/export/receipt")
def export_receipt_only(case_id: str):
    """Tier 1: Export signed Evidence Receipt JSON only."""
    case = db_store.get_case(case_id)
    if not case or not case.receipt_id:
        raise HTTPException(status_code=404, detail="Case has no receipt to export")
    receipt = db_store.get_receipt(case.receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt record not found")
    content = json.dumps(receipt, indent=2).encode("utf-8")
    filename = f"VaultBasis_Receipt_{case.receipt_id}.json"
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/api/cases/{case_id}/export/findings")
def export_findings_workpaper(case_id: str):
    """Tier 2: Export Findings Workpaper CSV with practitioner review dispositions."""
    case = db_store.get_case(case_id)
    if not case or not case.receipt_id:
        raise HTTPException(status_code=404, detail="Case has no reconciliation findings to export")
    receipt = db_store.get_receipt(case.receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt record not found")
    reviews = db_store.get_finding_reviews(case_id)
    csv_str = _build_findings_csv(case, receipt, reviews)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"VaultBasis_Findings_{case_id}_{timestamp}.csv"
    return Response(
        content=csv_str.encode("utf-8"),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/api/cases/{case_id}/export/package")
@app.get("/api/cases/{case_id}/export")
def export_full_evidence_package(case_id: str):
    """Tier 3: Export complete Evidence Package ZIP with manifest, receipt, findings, schema, and sources."""
    case = db_store.get_case(case_id)
    if not case or not case.receipt_id:
        raise HTTPException(status_code=404, detail="Case has no completed receipt to export")

    receipt = db_store.get_receipt(case.receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt record not found")

    reviews = db_store.get_finding_reviews(case_id)
    findings_csv = _build_findings_csv(case, receipt, reviews)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sys_ver = get_system_version()

    manifest_files = []
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Primary Signed Outcome Receipt
        receipt_bytes = json.dumps(receipt, indent=2).encode("utf-8")
        receipt_filename = "receipt-v0.1.json"
        zip_file.writestr(receipt_filename, receipt_bytes)
        manifest_files.append({
            "path": receipt_filename,
            "role": "SIGNED_EVIDENCE_RECEIPT",
            "sha256": hashlib.sha256(receipt_bytes).hexdigest(),
            "byte_size": len(receipt_bytes)
        })

        # 2. Findings Workpaper CSV
        findings_bytes = findings_csv.encode("utf-8")
        findings_filename = f"VaultBasis_Findings_{timestamp}.csv"
        zip_file.writestr(findings_filename, findings_bytes)
        manifest_files.append({
            "path": findings_filename,
            "role": "FINDINGS_WORKPAPER_CSV",
            "sha256": hashlib.sha256(findings_bytes).hexdigest(),
            "byte_size": len(findings_bytes)
        })

        # 3. Normative JSON Schema
        schema_path = RESOURCE_BASE / "schemas" / "receipt" / "receipt-v0.1.json"
        if schema_path.exists():
            schema_bytes = schema_path.read_bytes()
            zip_file.writestr("schemas/receipt-v0.1.json", schema_bytes)
            manifest_files.append({
                "path": "schemas/receipt-v0.1.json",
                "role": "NORMATIVE_EVIDENCE_SCHEMA",
                "sha256": hashlib.sha256(schema_bytes).hexdigest(),
                "byte_size": len(schema_bytes)
            })

        # 4. Standalone Offline Verifier HTML
        verifier_path = RESOURCE_BASE / "apps" / "edge-offline-verifier" / "index.html"
        if verifier_path.exists():
            verifier_bytes = verifier_path.read_bytes()
            zip_file.writestr("VERIFY.html", verifier_bytes)
            manifest_files.append({
                "path": "VERIFY.html",
                "role": "STANDALONE_OFFLINE_VERIFIER_UI",
                "sha256": hashlib.sha256(verifier_bytes).hexdigest(),
                "byte_size": len(verifier_bytes)
            })

        # 5. Source Evidence Files
        for source_id, s_meta in case.sources.items():
            raw_bytes = db_store.get_source_file_bytes(source_id)
            if raw_bytes:
                src_path = f"evidence/{source_id}_{sanitize_filename(s_meta.filename)}"
                zip_file.writestr(src_path, raw_bytes)
                manifest_files.append({
                    "path": src_path,
                    "role": "CLIENT_SOURCE_EVIDENCE",
                    "sha256": s_meta.sha256_hash,
                    "byte_size": len(raw_bytes)
                })

        # 6. Verification & Confidentiality Instructions
        verify_instructions = f"""VAULTBASIS OUTCOME RECEIPT VERIFICATION INSTRUCTIONS
VAULTBASIS EVIDENCE PACKAGE VERIFICATION & CONFIDENTIALITY NOTICE
Case Identifier: {case.case_id}
Tax Year: {case.tax_year}
Receipt ID: {case.receipt_id}
Package Exported: {datetime.now(timezone.utc).isoformat()}

CONFIDENTIALITY & DATA RETENTION NOTICE:
This export package contains client-provided tax records and transaction evidence.
Handle according to your firm's confidentiality, record retention, and secure transmission policies.

HOW TO VERIFY THIS EVIDENCE PACKAGE:
1. Double-click 'VERIFY.html' in this folder to open the self-contained Offline Verifier in any web browser.
2. Drag and drop '{receipt_filename}' into the verifier.
3. Confirm that all four integrity checks pass:
   ✓ JSON Schema Conformance: PASS
   ✓ Evidence Contract Version: PASS
   ✓ Receipt Key Self-Consistency: PASS
   ✓ Signature Integrity: PASS

LIMITATIONS & ASSURANCE BOUNDARY:
VaultBasis performs bounded, deterministic reconciliation under declared semantics.
It does not assess tax correctness or establish legal compliance. Verification confirms payload
integrity and cryptographic signature validity. It does not independently authenticate the
originating installation identity.
"""
        zip_file.writestr("VERIFY_INSTRUCTIONS.txt", verify_instructions)
        manifest_files.append({
            "path": "VERIFY_INSTRUCTIONS.txt",
            "role": "VERIFICATION_INSTRUCTIONS",
            "sha256": hashlib.sha256(verify_instructions.encode("utf-8")).hexdigest(),
            "byte_size": len(verify_instructions.encode("utf-8"))
        })

        # 7. Package Manifest JSON
        manifest_obj = {
            "package_version": "1.0",
            "case_id": case.case_id,
            "receipt_id": case.receipt_id,
            "revision": receipt.get("revision", 1),
            "receipt_created_at": receipt.get("created_at"),
            "package_exported_at": datetime.now(timezone.utc).isoformat(),
            "product_version": sys_ver.version,
            "source_commit": sys_ver.build_sha,
            "ruleset_id": receipt.get("ruleset_id"),
            "human_review_state": receipt.get("human_review_state"),
            "outcome_state": receipt.get("outcome_state"),
            "files": manifest_files
        }
        zip_file.writestr("manifest.json", json.dumps(manifest_obj, indent=2))

    zip_buffer.seek(0)
    pkg_filename = f"VaultBasis_Evidence_{case_id}_{timestamp}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={pkg_filename}"}
    )


@app.post("/api/receipts/verify")
async def verify_uploaded_receipt(file: UploadFile = File(...)):
    content = await file.read()
    try:
        receipt_data = json.loads(content.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {str(e)}")

    res = verify_outcome_receipt(receipt_data)
    return res.to_dict()


# ------------------------------------------------------------------------------
# Mount Dashboard and Verifier Web UI
# ------------------------------------------------------------------------------

WEB_DASHBOARD_DIR = RESOURCE_BASE / "apps" / "web-dashboard"
WEB_OFFLINE_VERIFIER_DIR = RESOURCE_BASE / "apps" / "edge-offline-verifier"
WEB_MARKETING_DIR = RESOURCE_BASE / "apps" / "web-marketing"

if WEB_DASHBOARD_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DASHBOARD_DIR)), name="static")

@app.get("/favicon.ico")
def serve_favicon_ico():
    ico_file = WEB_DASHBOARD_DIR / "favicon.ico"
    if ico_file.is_file():
        return FileResponse(path=str(ico_file), media_type="image/x-icon")
    svg_file = WEB_DASHBOARD_DIR / "favicon.svg"
    if svg_file.is_file():
        return Response(content=svg_file.read_bytes(), media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="Favicon not found")

@app.get("/favicon.svg")
def serve_favicon_svg():
    svg_file = WEB_DASHBOARD_DIR / "favicon.svg"
    if svg_file.is_file():
        return Response(content=svg_file.read_bytes(), media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="Favicon not found")

@app.get("/apple-touch-icon.png")
def serve_apple_touch_icon():
    png_file = WEB_DASHBOARD_DIR / "apple-touch-icon.png"
    if png_file.is_file():
        return FileResponse(path=str(png_file), media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")

@app.get("/site.webmanifest")
def serve_site_webmanifest():
    manifest_file = WEB_DASHBOARD_DIR / "site.webmanifest"
    if manifest_file.is_file():
        return Response(content=manifest_file.read_bytes(), media_type="application/manifest+json")
    raise HTTPException(status_code=404, detail="Manifest not found")

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    index_file = WEB_DASHBOARD_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"), status_code=200)
    return HTMLResponse("<h2>VaultBasis Dashboard building...</h2>")

@app.get("/verifier")
def verifier_redirect():
    return RedirectResponse(url="https://vaultbasis.com/verifier", status_code=302)

@app.get("/offline-verifier", response_class=HTMLResponse)
def serve_offline_verifier():
    index_file = WEB_OFFLINE_VERIFIER_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"), status_code=200)
    return HTMLResponse("<h2>Offline Verifier building...</h2>")

@app.get("/evidence-receipt-guide", response_class=HTMLResponse)
def serve_evidence_receipt_guide():
    guide_file = WEB_DASHBOARD_DIR / "evidence-receipt-guide.html"
    if guide_file.exists():
        return HTMLResponse(content=guide_file.read_text(encoding="utf-8"), status_code=200)
    return HTMLResponse("<h2>Evidence Receipt Guide building...</h2>")

@app.get("/about", response_class=HTMLResponse)
@app.get("/marketing", response_class=HTMLResponse)
def serve_marketing():
    marketing_file = WEB_MARKETING_DIR / "index.html"
    if marketing_file.exists():
        return HTMLResponse(content=marketing_file.read_text(encoding="utf-8"), status_code=200)
    return HTMLResponse("<h2>VaultBasis Marketing building...</h2>")


_SCHEMA_ALLOWLIST = {"receipt-v0.1.json"}

@app.get("/schemas/{filename:path}")
def serve_schema(filename: str):
    if filename not in _SCHEMA_ALLOWLIST:
        raise HTTPException(status_code=404, detail="Schema file not found")
    schema_dir = (RESOURCE_BASE / "schemas" / "receipt").resolve()
    schema_path = (schema_dir / filename).resolve()
    if not str(schema_path).startswith(str(schema_dir)):
        raise HTTPException(status_code=404, detail="Schema file not found")
    if schema_path.is_file():
        return Response(content=schema_path.read_text(encoding="utf-8"), media_type="application/json")
    raise HTTPException(status_code=404, detail="Schema file not found")


@app.get("/docs/scope_and_limitations_v0.1.md", include_in_schema=False)
def scope_and_limitations_legacy_url():
    return RedirectResponse(url="/docs/scope_and_limitations_v0.1.html", status_code=308)


@app.get("/docs/scope_and_limitations_v0.1.html", response_class=HTMLResponse)
def serve_scope_and_limitations():
    from scripts.md_to_html import render_page
    doc_path = RESOURCE_BASE / "docs" / "scope_and_limitations_v0.1.md"
    if not doc_path.is_file():
        raise HTTPException(status_code=404, detail="Scope & Limitations document not found")
    return HTMLResponse(
        content=render_page(doc_path.read_text(encoding="utf-8"),
                            "VaultBasis MMP-1 Supported Scope & Limitations"),
        status_code=200,
    )


def _sample_path(name: str) -> Path:
    bundled = RESOURCE_BASE / "sample" / name
    if bundled.is_file():
        return bundled
    return REPO_ROOT / "tests" / "fixtures" / name


@app.get("/sample-receipt.json")
@app.get("/api/sample-receipt")
def get_sample_receipt():
    sample_path = _sample_path("golden_receipt_valid.json")
    if sample_path.is_file():
        return JSONResponse(content=json.loads(sample_path.read_text(encoding="utf-8")))
    raise HTTPException(status_code=404, detail="Sample receipt not found")


@app.get("/sample-receipt-tampered.json")
def get_sample_receipt_tampered():
    sample_path = _sample_path("golden_receipt_tampered.json")
    if sample_path.is_file():
        return JSONResponse(content=json.loads(sample_path.read_text(encoding="utf-8")))
    raise HTTPException(status_code=404, detail="Tampered sample receipt not found")
