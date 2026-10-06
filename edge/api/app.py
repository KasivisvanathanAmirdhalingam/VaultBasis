"""
VaultBasis Edge — Local REST API Service
Conforms to PRD §18.1 (Local REST API), §62.1 (Service Contracts), §21.1 (Zero Egress)
"""

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
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import os
import sys

from apps.verifier.verify_receipt import verify_outcome_receipt
from edge.assurance.reconciliation_engine import DeterministicReconciliationEngine
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
from edge.connectors.validator import IntakeDispatcher
from edge.receipts.keygen import InstallationKeyManager
from edge.receipts.signer import ReceiptSigner
from edge.storage.sqlite_store import SQLiteStore, EvidenceCollisionError
from edge.system.version import get_system_version
from schemas.canonical.case import CanonicalCase


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
)
firm_identity_service = FirmIdentityService(db_store, audit_service=commercial_audit_service)
diagnostic_packager = DiagnosticPackager(db_store, commercial_policy, firm_identity_service)



app = FastAPI(
    title="VaultBasis Edge",
    description="Independent Outcome Verification and Assurance Edge (MMP-1)",
    version="0.1.0-preview"
)

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
    db_store.save_case(case)
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

    cloned_case = CanonicalCase(
        case_id=new_id,
        client_reference=new_client_ref,
        tax_year=source_case.tax_year,
        jurisdiction=source_case.jurisdiction,
        case_status="CREATED",
        case_kind="PRODUCTION",
        sample_definition_id=None,
        sample_manifest_digest=None,
        sources=source_case.sources.copy(),
        transactions=source_case.transactions.copy(),
        created_at=now_utc,
        updated_at=now_utc
    )
    db_store.save_case(cloned_case)
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
    else:
        outcome_state = getattr(case_dict_or_obj, "outcome_state", None)
        case_status = getattr(case_dict_or_obj, "case_status", "CREATED")

    if outcome_state:
        workflow_status = "RECONCILED"
    elif case_status == "SOURCES_INGESTED":
        workflow_status = "READY_TO_RECONCILE"
    elif case_status in ("CREATED", "PENDING"):
        workflow_status = "NEEDS_EVIDENCE"
    else:
        workflow_status = case_status

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

    source_id = f"SRC-{uuid.uuid4().hex[:6].upper()}_{Path(file.filename or 'file').stem}"
    try:
        meta, transactions = IntakeDispatcher.ingest_document(
            data_bytes=content,
            filename=file.filename or "unknown",
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

    # Evaluate commercial entitlement before performing reconciliation
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

    if len(case.sources) < 2:
        raise HTTPException(
            status_code=400,
            detail="Reconciliation requires at least two source documents (e.g. Form 1099-DA and Koinly CSV)"
        )


    # Compute a manifest hash of the current source set (sorted for determinism).
    current_manifest = hashlib.sha256(
        json.dumps(
            sorted((sid, s.sha256_hash) for sid, s in case.sources.items())
        ).encode()
    ).hexdigest()

    # Execute deterministic reconciliation
    recon_result = DeterministicReconciliationEngine.reconcile_case(case)

    # Return existing receipt only if sources are identical to when it was issued.
    if case.receipt_id:
        existing_receipt = db_store.get_receipt(case.receipt_id)
        if existing_receipt:
            issued_sources = existing_receipt.get("source_hashes", {})
            issued_manifest = hashlib.sha256(
                json.dumps(sorted(issued_sources.items())).encode()
            ).hexdigest()
            if current_manifest == issued_manifest:
                return {
                    "status": "RECEIPT_ALREADY_ISSUED",
                    "case_id": case_id,
                    "receipt_id": case.receipt_id,
                    "outcome_state": case.outcome_state,
                    "assurance_level": case.assurance_level,
                    "reconciliation": recon_result.to_dict(),
                    "receipt": existing_receipt,
                    "message": "Receipt already exists for this case. View it via /cases/{case_id}/receipt.",
                }

    # Build Outcome Receipt Payload
    receipt_id = str(uuid.uuid4())
    source_hashes = {s.source_id: s.sha256_hash for s in case.sources.values()}
    source_schema_ids = {s.source_id: s.schema_id for s in case.sources.values()}

    receipt_payload = {
        "receipt_version": "v0.1",
        "receipt_id": receipt_id,
        "case_id": case.case_id,
        "claim_type": "DIGITAL_ASSET_TAX_RECONCILIATION",
        "claimant_type": "TAXPAYER",
        "producer_reference": "VaultBasis Edge v0.1.0-preview",
        "source_ids": list(case.sources.keys()),
        "source_hashes": source_hashes,
        "source_schema_ids": source_schema_ids,
        "canonicalization_version": "v0.1",
        "ruleset_id": f"US_IRC_1099DA_{case.tax_year}_V1",
        "engine_version": "0.1.0",
        "policy_version": "0.1.0",
        "assurance_level": recon_result.assurance_level,
        "outcome_state": recon_result.outcome_state,
        "material_differences": [d.to_dict() for d in recon_result.material_differences],
        "unresolved_items": recon_result.unresolved_items,
        "human_review_state": "UNREVIEWED",
        "ai_involvement_level": "NONE",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # Cryptographically sign receipt using local Ed25519 installation key
    signed_receipt = receipt_signer.sign_receipt(receipt_payload)

    # Persist receipt and update case status
    db_store.save_receipt(receipt_id, case.case_id, signed_receipt)
    case.outcome_state = recon_result.outcome_state
    case.assurance_level = recon_result.assurance_level
    case.receipt_id = receipt_id
    case.case_status = "RECEIPT_ISSUED"
    db_store.save_case(case)

    return {
        "status": "RECONCILED",
        "case_id": case_id,
        "outcome_state": recon_result.outcome_state,
        "assurance_level": recon_result.assurance_level,
        "receipt_id": receipt_id,
        "reconciliation": recon_result.to_dict(),
        "receipt": signed_receipt
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


@app.get("/api/cases/{case_id}/export")
def export_evidence_bundle(case_id: str):
    case = db_store.get_case(case_id)
    if not case or not case.receipt_id:
        raise HTTPException(status_code=404, detail="Case has no completed receipt to export")

    receipt = db_store.get_receipt(case.receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt record not found")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Primary Signed Outcome Receipt
        zip_file.writestr(
            "receipt-v0.1.json",
            json.dumps(receipt, indent=2)
        )
        # 2. Normative JSON Schema
        schema_path = RESOURCE_BASE / "schemas" / "receipt" / "receipt-v0.1.json"
        if schema_path.exists():
            zip_file.writestr("schemas/receipt-v0.1.json", schema_path.read_text(encoding="utf-8"))
        # 3. Source Evidence Files
        for source_id, s_meta in case.sources.items():
            raw_bytes = db_store.get_source_file_bytes(source_id)
            if raw_bytes:
                zip_file.writestr(f"evidence/{source_id}_{s_meta.filename}", raw_bytes)
        # 4. Verification Readme (strictly practitioner guidance and schema instructions; zero implementation code)
        zip_file.writestr(
            "VERIFY_INSTRUCTIONS.txt",
            f"""VAULTBASIS OUTCOME RECEIPT VERIFICATION INSTRUCTIONS
Case ID: {case.case_id}
Client: {getattr(case, 'client_reference', 'Sample Client')}
Receipt ID: {case.receipt_id}

HOW TO VERIFY THIS RECEIPT:

PRIMARY PRACTITIONER PATH (GUI / Offline Verifier):
1. Open VaultBasis Edge or navigate to http://127.0.0.1:8000/offline-verifier (or https://vaultbasis.com/verifier).
2. Select or drag-and-drop 'receipt-v0.1.json' into the verifier window.
3. Review the automated verification checklist (Schema Conformance, Contract Version, Key Consistency, Signature Verification).

SECONDARY TECHNICAL AUDIT PATH (Air-gapped Python CLI):
For independent technical auditors wishing to verify via command line using the standalone verifier utility provided in the VaultBasis distribution or repository:
1. Run verify_receipt.py against the exported receipt and evidence folder:
   python3 verify_receipt.py receipt-v0.1.json --evidence-dir evidence/

IMPORTANT REGULATORY & ASSURANCE BOUNDARY:
VaultBasis performs bounded, deterministic reconciliation of supported sources under declared semantics. It does not assess tax correctness, establish legal compliance, or determine whether source information is complete or accurate. Successful verification confirms that the receipt signature is valid for the declared installation public key and that the signed receipt content has not changed relative to that signature. Verification does not constitute a professional opinion, legal finding, government approval, or endorsement by the IRS or any other government authority. The practitioner remains responsible for professional interpretation and application of applicable law.
"""
        )

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=VaultBasis_Evidence_{case_id}.zip"}
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
