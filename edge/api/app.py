"""
VaultBasis Edge — Local REST API Service
Conforms to PRD §18.1 (Local REST API), §62.1 (Service Contracts), §21.1 (Zero Egress)
"""

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
from edge.connectors.validator import IntakeDispatcher
from edge.receipts.keygen import InstallationKeyManager
from edge.receipts.signer import ReceiptSigner
from edge.storage.sqlite_store import SQLiteStore
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

# Initialize local key manager and SQLite store
KEY_DIR = DATA_DIR / "keys"
DB_FILE = os.environ.get("VAULTBASIS_DB_FILE", "vaultbasis.db")
DB_PATH = DATA_DIR / DB_FILE

key_manager = InstallationKeyManager(KEY_DIR)
priv_key, pub_key = key_manager.ensure_keypair()
receipt_signer = ReceiptSigner(priv_key)
db_store = SQLiteStore(DB_PATH)

app = FastAPI(
    title="VaultBasis Edge",
    description="Independent Outcome Verification and Assurance Edge (MMP-1)",
    version="0.1.0-preview"
)

# CORS locked to loopback origins only — Edge is a local-only application.
# allow_credentials requires explicit origin list (wildcard + credentials is rejected by browsers
# and is a security defect: any site could XHR the local API while Edge runs).
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
    tax_year: int = Field(2025, description="Target tax year")
    jurisdiction: str = Field("US", description="Regulatory jurisdiction")


class CaseSummaryResponse(BaseModel):
    case_id: str
    tax_year: int
    jurisdiction: str
    case_status: str
    outcome_state: Optional[str]
    assurance_level: Optional[str]
    receipt_id: Optional[str]
    created_at: str
    updated_at: str


# ------------------------------------------------------------------------------
# API Endpoints
# ------------------------------------------------------------------------------

@app.get("/api/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "VaultBasis Edge",
        "version": "0.1.0-preview",
        "installation_key_id": receipt_signer.key_id,
        "egress_policy": "STRICT_LOCAL_ONLY",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/api/cases", response_model=CaseSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_case(req: CreateCaseRequest):
    case_id = req.case_id or f"CASE-{uuid.uuid4().hex[:8].upper()}"
    existing = db_store.get_case(case_id)
    if existing:
        # Per PRD §62.2 (Idempotency): return existing case if already created
        return CaseSummaryResponse(
            case_id=existing.case_id,
            tax_year=existing.tax_year,
            jurisdiction=existing.jurisdiction,
            case_status=existing.case_status,
            outcome_state=existing.outcome_state,
            assurance_level=existing.assurance_level,
            receipt_id=existing.receipt_id,
            created_at=existing.created_at,
            updated_at=existing.updated_at
        )

    now_utc = datetime.now(timezone.utc).isoformat()
    case = CanonicalCase(
        case_id=case_id,
        tax_year=req.tax_year,
        jurisdiction=req.jurisdiction,
        case_status="CREATED",
        created_at=now_utc,
        updated_at=now_utc
    )
    db_store.save_case(case)
    return CaseSummaryResponse(
        case_id=case.case_id,
        tax_year=case.tax_year,
        jurisdiction=case.jurisdiction,
        case_status=case.case_status,
        outcome_state=case.outcome_state,
        assurance_level=case.assurance_level,
        receipt_id=case.receipt_id,
        created_at=case.created_at,
        updated_at=case.updated_at
    )


@app.get("/api/cases", response_model=List[Dict[str, Any]])
def list_cases():
    return db_store.list_cases()


@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    case = db_store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")
    
    # Return structured case details
    return {
        "case_id": case.case_id,
        "tax_year": case.tax_year,
        "jurisdiction": case.jurisdiction,
        "case_status": case.case_status,
        "outcome_state": case.outcome_state,
        "assurance_level": case.assurance_level,
        "receipt_id": case.receipt_id,
        "sources": {k: v.model_dump() for k, v in case.sources.items()},
        "transactions": [t.to_summary_dict() for t in case.transactions],
        "created_at": case.created_at,
        "updated_at": case.updated_at
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

    db_store.add_source_and_transactions(case_id, meta, content, transactions)
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

    if len(case.sources) < 2:
        raise HTTPException(
            status_code=400,
            detail="Reconciliation requires at least two source documents (e.g. Form 1099-DA and Koinly CSV)"
        )

    # Execute deterministic reconciliation
    recon_result = DeterministicReconciliationEngine.reconcile_case(case)

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
        # 1. Signed Outcome Receipt
        zip_file.writestr(
            "receipt-v0.1.json",
            json.dumps(receipt, indent=2)
        )
        # 2. Standalone offline verifier script
        verifier_cli_path = RESOURCE_BASE / "apps" / "verifier" / "verify_receipt.py"
        if verifier_cli_path.exists():
            zip_file.writestr("verify_receipt.py", verifier_cli_path.read_text())
        # 3. Normative Schema
        schema_path = RESOURCE_BASE / "schemas" / "receipt" / "receipt-v0.1.json"
        if schema_path.exists():
            zip_file.writestr("schemas/receipt-v0.1.json", schema_path.read_text())
        # 4. Source Files
        for source_id, s_meta in case.sources.items():
            raw_bytes = db_store.get_source_file_bytes(source_id)
            if raw_bytes:
                zip_file.writestr(f"evidence/{source_id}_{s_meta.filename}", raw_bytes)
        # 5. Verification Readme
        zip_file.writestr(
            "VERIFY_INSTRUCTIONS.txt",
            f"""VAULTBASIS OUTCOME RECEIPT VERIFICATION INSTRUCTIONS
Case ID: {case.case_id}
Receipt ID: {case.receipt_id}

To verify this receipt independently on any clean machine without internet access:
1. Ensure Python 3.8+ and 'cryptography' library are installed.
2. Run:
   python3 verify_receipt.py receipt-v0.1.json --evidence-dir evidence/

IMPORTANT NOTICE:
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
WEB_VERIFIER_DIR = RESOURCE_BASE / "apps" / "web-verifier"
WEB_MARKETING_DIR = RESOURCE_BASE / "apps" / "web-marketing"

if WEB_DASHBOARD_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DASHBOARD_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    index_file = WEB_DASHBOARD_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(), status_code=200)
    return HTMLResponse("<h2>VaultBasis Dashboard building...</h2>")

@app.get("/verifier", response_class=HTMLResponse)
def serve_verifier():
    verifier_file = WEB_VERIFIER_DIR / "index.html"
    if verifier_file.exists():
        return HTMLResponse(content=verifier_file.read_text(), status_code=200)
    return HTMLResponse("<h2>VaultBasis Public Verifier building...</h2>")


@app.get("/about", response_class=HTMLResponse)
@app.get("/marketing", response_class=HTMLResponse)
def serve_marketing():
    marketing_file = WEB_MARKETING_DIR / "index.html"
    if marketing_file.exists():
        return HTMLResponse(content=marketing_file.read_text(), status_code=200)
    return HTMLResponse("<h2>VaultBasis Marketing building...</h2>")




_SCHEMA_ALLOWLIST = {"receipt-v0.1.json"}

@app.get("/schemas/{filename:path}")
def serve_schema(filename: str):
    if filename not in _SCHEMA_ALLOWLIST:
        raise HTTPException(status_code=404, detail="Schema file not found")
    schema_dir = (RESOURCE_BASE / "schemas" / "receipt").resolve()
    schema_path = (schema_dir / filename).resolve()
    # Reject any path that escapes the schema directory
    if not str(schema_path).startswith(str(schema_dir)):
        raise HTTPException(status_code=404, detail="Schema file not found")
    if schema_path.is_file():
        return Response(content=schema_path.read_text(), media_type="application/json")
    raise HTTPException(status_code=404, detail="Schema file not found")


@app.get("/docs/scope_and_limitations_v0.1.md", include_in_schema=False)
def scope_and_limitations_legacy_url():
    # Old bookmarks/old deployments link the raw .md URL: never serve raw
    # markdown as a page. Redirect to the rendered document.
    return RedirectResponse(url="/docs/scope_and_limitations_v0.1.html",
                            status_code=308)


@app.get("/docs/scope_and_limitations_v0.1.html", response_class=HTMLResponse)
def serve_scope_and_limitations():
    # Rendered via the single stdlib renderer (scripts/md_to_html.py), same as
    # the Vercel bundle — practitioners never receive raw markdown.
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
        return JSONResponse(content=json.loads(sample_path.read_text()))
    raise HTTPException(status_code=404, detail="Sample receipt not found")


@app.get("/sample-receipt-tampered.json")
def get_sample_receipt_tampered():
    sample_path = _sample_path("golden_receipt_tampered.json")
    if sample_path.is_file():
        return JSONResponse(content=json.loads(sample_path.read_text()))
    raise HTTPException(status_code=404, detail="Tampered sample receipt not found")

