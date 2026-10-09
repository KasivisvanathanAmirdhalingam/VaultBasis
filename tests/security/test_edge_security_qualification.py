"""
MMP15-SEC-QUAL-001 — Edge Runtime, Installer & Production Security Qualification Suite

Comprehensive automated security qualification tests validating:
1. Localhost HTTP & Network Boundary (Host validation, DNS rebinding defense)
2. Origin & CSRF Mutation Protection (blocks hostile web origins from localhost API)
3. Security Headers & No-Cache on sensitive API responses
4. Ingestion Security & Path Traversal Neutralization
5. CSV Formula Injection Neutralization in Exports
6. Cryptographic Receipt Producer-Verifier Roundtrip & Tamper Detection
7. Multi-Scope Verifier Transparency
8. Secret Hygiene & Private Key Isolation
"""

import io
import json
import zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from edge.api.app import app, sanitize_csv_cell, sanitize_filename
from apps.verifier.verify_receipt import verify_outcome_receipt


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Test client with isolated SQLite database and initialized evaluation."""
    test_db = tmp_path / "test_sec_vaultbasis.db"
    from edge.storage.sqlite_store import SQLiteStore
    from edge.commercial.policy import CommercialPolicyService
    from edge.commercial.audit import CommercialAuditService
    from edge.commercial.identity import FirmIdentityService
    from edge.commercial.diagnostics import DiagnosticPackager

    store = SQLiteStore(str(test_db))
    monkeypatch.setattr("edge.api.app.db_store", store)
    
    audit_svc = CommercialAuditService(store=store)
    monkeypatch.setattr("edge.api.app.commercial_audit_service", audit_svc)
    
    policy_svc = CommercialPolicyService(store=store, audit_service=audit_svc)
    monkeypatch.setattr("edge.api.app.commercial_policy", policy_svc)
    
    firm_svc = FirmIdentityService(store, audit_service=audit_svc)
    monkeypatch.setattr("edge.api.app.firm_identity_service", firm_svc)
    
    diag_pkg = DiagnosticPackager(store, policy_svc, firm_svc)
    monkeypatch.setattr("edge.api.app.diagnostic_packager", diag_pkg)
    
    # Initialize with 3-day evaluation
    policy_svc.start_evaluation("Test Practitioner")
    
    with TestClient(app) as test_client:
        # Preload canonical sample case
        test_client.post("/api/sample-case/load")
        test_client.post("/api/cases/CASE-SAMPLE-2025/reconcile")
        yield test_client


# ============================================================================
# LAYER 1: LOCALHOST HTTP & NETWORK BOUNDARY (MMP15-SEC-QUAL-001 §2-§4)
# ============================================================================

class TestLocalhostBoundary:
    """Validate loopback binding assumptions, Host header validation, and DNS rebinding protections."""

    def test_allowed_loopback_host_headers(self, client):
        """Standard localhost / loopback Host headers must be accepted."""
        allowed_hosts = [
            "127.0.0.1",
            "127.0.0.1:8000",
            "localhost",
            "localhost:8000",
            "testserver",
            "[::1]",
            "[::1]:8000"
        ]
        for host in allowed_hosts:
            res = client.get("/health", headers={"Host": host})
            assert res.status_code == 200, f"Host '{host}' should be permitted"
            assert res.json().get("status") == "HEALTHY"

    def test_reject_unauthorized_host_headers_dns_rebinding(self, client):
        """Hostile external Host headers (DNS rebinding attacks) must be blocked with 400 Bad Request."""
        hostile_hosts = [
            "attacker.example",
            "evil.com",
            "192.168.1.100",
            "10.0.0.5",
            "rebind.attacker.io:8000",
            "vaultbasis.com.attacker.com"
        ]
        for host in hostile_hosts:
            res = client.get("/health", headers={"Host": host})
            assert res.status_code == 400, f"Host '{host}' must be rejected with 400"
            data = res.json()
            assert "detail" in data
            assert "Invalid Host header" in data["detail"]


# ============================================================================
# LAYER 2: CSRF & CROSS-ORIGIN MUTATION DEFENSE (MMP15-SEC-QUAL-001 §3)
# ============================================================================

class TestCrossOriginProtection:
    """Validate that hostile external websites cannot trigger local API mutations via browser requests."""

    def test_block_hostile_origin_on_mutation_endpoints(self, client):
        """Cross-origin POST/PUT/DELETE from external web origins must be rejected with 403 Forbidden."""
        hostile_origins = [
            "https://attacker.example",
            "http://evil-tracker.io",
            "https://malicious-tax-site.org",
            "http://localhost.evil.com"
        ]
        mutation_endpoints = [
            ("POST", "/api/cases", {"client_reference": "Victim LLC", "tax_year": 2025}),
            ("POST", "/api/commercial/start-evaluation", {"customer_name": "Victim"}),
            ("POST", "/api/commercial/license", {"token": "FAKE_TOKEN"}),
            ("POST", "/api/sample-case/reset", {}),
            ("POST", "/api/system/quit", {}),
        ]

        for origin in hostile_origins:
            for method, endpoint, payload in mutation_endpoints:
                if method == "POST":
                    res = client.post(endpoint, json=payload, headers={"Origin": origin})
                assert res.status_code == 403, f"Mutation {method} {endpoint} from Origin '{origin}' must be blocked"
                assert "Cross-origin" in res.json().get("detail", "") or "Forbidden" in res.json().get("detail", "")

    def test_block_hostile_origin_on_shutdown_endpoint(self, client):
        """Cross-origin POST to /api/system/quit must be rejected with 403 Forbidden to prevent remote DoS."""
        res = client.post("/api/system/quit", headers={"Origin": "https://malicious-attacker.com"})
        assert res.status_code == 403
        assert "Cross-origin" in res.json().get("detail", "")

    def test_allow_legitimate_local_origins(self, client):
        """Requests from verified local origins must be allowed."""
        valid_origins = [
            "http://127.0.0.1:8000",
            "http://localhost:8000",
        ]
        for origin in valid_origins:
            res = client.post(
                "/api/cases",
                json={"client_reference": f"Origin Test {origin}", "tax_year": 2025},
                headers={"Host": "localhost:8000", "Origin": origin}
            )
            assert res.status_code in (200, 201), f"Origin '{origin}' should be accepted"

    def test_block_unauthenticated_null_origin_mutations(self, client):
        """Origin: null on state-mutating requests without capability must be blocked with 403 Forbidden."""
        res = client.post(
            "/api/cases",
            json={"client_reference": "Hostile File Attempt", "tax_year": 2025},
            headers={"Host": "localhost:8000", "Origin": "null"}
        )
        assert res.status_code == 403
        assert "Origin: null" in res.json().get("detail", "") or "Forbidden" in res.json().get("detail", "")

    def test_allow_null_origin_with_valid_session_capability(self, client):
        """Origin: null is permitted only when presenting a valid instance-bound session capability."""
        from edge.api.app import LOCAL_SESSION_CAPABILITY
        res = client.post(
            "/api/cases",
            json={"client_reference": "Authorized Capability Test", "tax_year": 2025},
            headers={
                "Host": "localhost:8000",
                "Origin": "null",
                "X-VaultBasis-Capability": LOCAL_SESSION_CAPABILITY
            }
        )
        assert res.status_code in (200, 201)

    def test_browser_origin_edge_cases_and_shutdown(self, client):
        """Validate shutdown authorization: loopback origin or capability required; unauthenticated null blocked."""
        from edge.api.app import LOCAL_SESSION_CAPABILITY

        # 1. Host: localhost, Origin: null without capability -> 403 Forbidden (malicious downloaded HTML defense)
        res1 = client.post("/api/system/quit", headers={"Host": "localhost:8000", "Origin": "null"})
        assert res1.status_code == 403

        # 2. Host: localhost, Origin: null WITH valid capability -> 200 OK
        res2 = client.post(
            "/api/system/quit",
            headers={"Host": "localhost:8000", "Origin": "null", "X-VaultBasis-Capability": LOCAL_SESSION_CAPABILITY}
        )
        assert res2.status_code == 200
        assert res2.json().get("status") == "SHUTTING_DOWN"

        # 3. Host: 127.0.0.1:8000, Origin: http://127.0.0.1:8000 -> 200 OK
        res3 = client.post("/api/system/quit", headers={"Host": "127.0.0.1:8000", "Origin": "http://127.0.0.1:8000"})
        assert res3.status_code == 200
        assert res3.json().get("status") == "SHUTTING_DOWN"

        # 4. Host: localhost:8000, No Origin header (direct desktop curl / script) -> 200 OK
        res4 = client.post("/api/system/quit", headers={"Host": "localhost:8000"})
        assert res4.status_code == 200
        assert res4.json().get("status") == "SHUTTING_DOWN"

    def test_offline_ui_self_containment(self):
        """Dashboard HTML must be 100% self-contained with zero external CDN scripts or fonts for air-gap safety."""
        dashboard_path = REPO_ROOT / "apps" / "web-dashboard" / "index.html" if "REPO_ROOT" in globals() else Path(__file__).resolve().parent.parent.parent / "apps" / "web-dashboard" / "index.html"
        assert dashboard_path.exists(), "Dashboard index.html not found"
        html = dashboard_path.read_text(encoding="utf-8")
        
        # Verify no external CDN scripts, CSS, or fonts
        assert "cdn.jsdelivr.net" not in html
        assert "cdnjs.cloudflare.com" not in html
        assert "unpkg.com" not in html
        assert "fonts.googleapis.com" not in html
        assert "screen-shutdown" in html
        assert "executeQuitVaultBasis" in html

    def test_local_session_capability_zero_leakage(self, client):
        """LOCAL_SESSION_CAPABILITY must be transient process-local secret material.
        It MUST NEVER appear in HTML source, API response bodies, SQLite DB, diagnostics, or receipts.
        """
        from edge.api.app import LOCAL_SESSION_CAPABILITY, DB_PATH
        import sqlite3

        # 1. Verify not in HTML source
        dashboard_path = REPO_ROOT / "apps" / "web-dashboard" / "index.html" if "REPO_ROOT" in globals() else Path(__file__).resolve().parent.parent.parent / "apps" / "web-dashboard" / "index.html"
        html = dashboard_path.read_text(encoding="utf-8")
        assert LOCAL_SESSION_CAPABILITY not in html, "LOCAL_SESSION_CAPABILITY leaked into dashboard HTML"

        # 2. Verify not in standard API responses
        endpoints = ["/api/health", "/api/cases", "/api/system/version"]
        for ep in endpoints:
            res = client.get(ep, headers={"Host": "localhost:8000"})
            assert LOCAL_SESSION_CAPABILITY not in res.text, f"LOCAL_SESSION_CAPABILITY leaked into response for {ep}"

        # 3. Verify not written to SQLite database
        if DB_PATH.exists():
            with open(DB_PATH, "rb") as f:
                db_bytes = f.read()
            assert LOCAL_SESSION_CAPABILITY.encode("utf-8") not in db_bytes, "LOCAL_SESSION_CAPABILITY leaked into SQLite file"


# ============================================================================
# LAYER 3: SECURITY HEADERS & CACHE DISCIPLINE (MMP15-SEC-QUAL-001 §34)
# ============================================================================

class TestSecurityHeaders:
    """Ensure sensitive client data in local API responses is never cached or embedded unsafely."""

    def test_api_security_and_no_cache_headers(self, client):
        """All API responses must include strict cache prevention and defensive security headers."""
        res = client.get("/api/cases")
        assert res.status_code == 200
        
        headers = res.headers
        assert "no-store" in headers.get("cache-control", "").lower()
        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert headers.get("referrer-policy") == "no-referrer"
        assert "content-security-policy" in headers


# ============================================================================
# LAYER 4: FILE INGESTION & PATH TRAVERSAL DEFENSE (MMP15-SEC-QUAL-001 §6, §9, §10)
# ============================================================================

class TestFileIngestionAndPathTraversal:
    """Validate filename sanitization and path traversal neutralization."""

    def test_sanitize_filename_removes_traversal_and_reserved_chars(self):
        """Dangerous path traversal characters and reserved names must be sanitized to safe basenames."""
        test_cases = [
            ("../../../../etc/passwd", "passwd"),
            ("..\\..\\AppData\\Roaming\\malware.exe", "malware.exe"),
            ("/absolute/path/file.csv", "file.csv"),
            ("C:\\Windows\\System32\\calc.exe", "calc.exe"),
            ("CON.csv", "_CON.csv"),
            ("NUL.txt", "_NUL.txt"),
            ("AUX", "_AUX"),
            ("evil\x00file.csv", "evilfile.csv"),
            ("normal_1099da_report.csv", "normal_1099da_report.csv")
        ]
        for hostile_input, expected_safe in test_cases:
            sanitized = sanitize_filename(hostile_input)
            assert "/" not in sanitized
            assert "\\" not in sanitized
            assert ".." not in sanitized
            assert sanitized == expected_safe


# ============================================================================
# LAYER 5: CSV FORMULA INJECTION DEFENSE (MMP15-SEC-QUAL-001 §7, §8)
# ============================================================================

class TestCSVFormulaInjection:
    """Validate that exported CSV findings neutralize dangerous spreadsheet formulas."""

    def test_sanitize_csv_cell_neutralizes_trigger_characters(self):
        """Cells starting with =, +, -, @, \\t, \\r must be prefixed with single quote '."""
        dangerous_payloads = [
            '=cmd|\' /C calc\'!A0',
            '=HYPERLINK("https://attacker.example", "Click Here")',
            '+SUM(1+1)',
            '-2+3+cmd|',
            '@SUM(A1:A10)',
            '\t=1+1',
            '\r=2+2'
        ]
        for payload in dangerous_payloads:
            sanitized = sanitize_csv_cell(payload)
            assert sanitized.startswith("'"), f"Dangerous formula '{payload}' was not neutralized"

    def test_sanitize_csv_cell_leaves_safe_values_untouched(self):
        """Legitimate numbers and text strings without leading formula characters must remain unchanged."""
        safe_values = [
            "BTC",
            "ETH",
            "12500.00",
            "2025-03-10",
            "USD",
            "Acquisition date not reported by broker"
        ]
        for val in safe_values:
            assert sanitize_csv_cell(val) == val


# ============================================================================
# LAYER 6: RECEIPT PRODUCER-VERIFIER ROUNDTRIP & REVISION LINEAGE (MMP15-SEC-QUAL-001 §30, §31, §38)
# ============================================================================

class TestReceiptRoundTripAndReviewLifecycle:
    """Validate deterministic preliminary vs final reviewed receipts and roundtrip cryptographic verification."""

    def test_reconciliation_receipt_review_lifecycle_roundtrip(self, client):
        # 1. Create a case
        case_res = client.post("/api/cases", json={
            "client_reference": "Sec Qual Client LLC",
            "tax_year": 2025
        })
        assert case_res.status_code == 201
        case_id = case_res.json()["case_id"]

        # 2. Upload Golden 6-row Form 1099-DA (Source A)
        csv_1099da = (
            "Asset,Quantity,Proceeds,Date Sold,Cost Basis,Date Acquired,Box 2\n"
            "BTC,0.25000000,22500.00,2025-03-10,15000.00,2024-01-15,YES\n"
            "ETH,3.00000000,10000.00,2025-05-14,6000.00,2024-06-20,YES\n"
            "SOL,40.00000000,6000.00,2025-08-01,3200.00,2024-10-01,YES\n"
            "ADA,5000.00000000,4500.00,2025-09-12,,2023-04-10,NO\n"
            "DOT,200.00000000,1800.00,2025-10-05,1200.00,2025-01-05,YES\n"
            "AVAX,150.00000000,5250.00,2025-11-18,3000.00,2024-12-01,YES\n"
        )
        upload_a = client.post(
            f"/api/cases/{case_id}/sources",
            files={"file": ("1099da_golden.csv", io.BytesIO(csv_1099da.encode("utf-8")), "text/csv")}
        )
        assert upload_a.status_code == 200

        # 3. Upload Golden 6-row Koinly Ledger (Source B)
        csv_koinly = (
            "Date,Asset,Amount,Proceeds,Cost Basis,Gain / Loss,Date Acquired\n"
            "2025-03-10,BTC,0.25000000,22500.00,15000.00,7500.00,2024-01-15\n"
            "2025-05-14,ETH,3.00000000,9975.00,6000.00,3975.00,2024-06-20\n"
            "2025-08-01,SOL,40.00000000,6000.00,4100.00,1900.00,2024-10-01\n"
            "2025-09-12,ADA,5000.00000000,4500.00,1800.00,2700.00,2023-04-10\n"
            "2025-10-05,DOT,200.00000000,1800.00,1200.00,600.00,2023-11-20\n"
            "2025-12-02,LINK,300.00000000,4200.00,3100.00,1100.00,2024-05-18\n"
        )
        upload_b = client.post(
            f"/api/cases/{case_id}/sources",
            files={"file": ("koinly_golden.csv", io.BytesIO(csv_koinly.encode("utf-8")), "text/csv")}
        )
        assert upload_b.status_code == 200

        # 4. Trigger Reconciliation -> Issues Preliminary Receipt (Revision 1, UNREVIEWED)
        recon_res = client.post(f"/api/cases/{case_id}/reconcile")
        assert recon_res.status_code == 200
        recon_data = recon_res.json()
        assert recon_data["status"] == "RECONCILED"
        
        prelim_receipt = recon_data["receipt"]
        assert prelim_receipt["revision"] == 1
        assert prelim_receipt["human_review_state"] == "UNREVIEWED"
        assert prelim_receipt["ruleset_id"] == "VB_US_1099DA_2025_R1"

        # Verify preliminary receipt with verifier engine
        ver_result_1 = verify_outcome_receipt(prelim_receipt)
        assert ver_result_1.is_valid is True
        assert ver_result_1.signature_valid is True

        # 5. Record Practitioner Review Dispositions
        diff_id = prelim_receipt["material_differences"][0]["difference_id"]
        review_save = client.post(f"/api/cases/{case_id}/reviews", json={
            "finding_id": diff_id,
            "disposition": "REVIEWED",
            "practitioner_notes": "Reviewed fee difference against broker settlement statement."
        })
        assert review_save.status_code == 200

        # 6. Finalize Review -> Issues Final Reviewed Receipt (Revision 2, REVIEWED_ANNOTATED)
        final_res = client.post(f"/api/cases/{case_id}/finalize-review", json={
            "reviewer_identity": "CPA Practitioner Jane Doe",
            "notes": "Completed manual verification of all material differences."
        })
        assert final_res.status_code == 200
        final_data = final_res.json()
        assert final_data["revision"] == 2
        assert final_data["human_review_state"] == "REVIEWED_ANNOTATED"
        assert final_data["prior_receipt_id"] == prelim_receipt["receipt_id"]
        
        final_receipt = final_data["receipt"]

        # Verify final reviewed receipt with verifier engine
        ver_result_2 = verify_outcome_receipt(final_receipt)
        assert ver_result_2.is_valid is True
        assert ver_result_2.signature_valid is True
        res_dict = ver_result_2.to_dict()
        assert res_dict["checks"]["installation_identity"] == "NOT_AUTHENTICATED"
        assert res_dict["checks"]["tax_correctness"] == "NOT_DETERMINED"

        # 7. Test Three-Tier Exports
        # Tier 1: Receipt Only (.json)
        export_rcpt = client.get(f"/api/cases/{case_id}/export/receipt")
        assert export_rcpt.status_code == 200
        assert export_rcpt.headers["content-type"].startswith("application/json")
        exported_rcpt_json = export_rcpt.json()
        assert exported_rcpt_json["receipt_id"] == final_receipt["receipt_id"]

        # Tier 2: Findings Workpaper (.csv)
        export_csv = client.get(f"/api/cases/{case_id}/export/findings")
        assert export_csv.status_code == 200
        assert "text/csv" in export_csv.headers["content-type"]
        csv_text = export_csv.text
        assert "Finding_ID,Finding_Type,Classification_or_Reason,Asset" in csv_text
        assert "ETH" in csv_text
        assert "PROCEEDS_DIFFERENCE" in csv_text

        # Tier 3: Full Evidence Package (.zip)
        export_zip = client.get(f"/api/cases/{case_id}/export/package")
        assert export_zip.status_code == 200
        assert export_zip.headers["content-type"] == "application/zip"
        
        # Unpack ZIP in-memory and assert manifest + integrity
        with zipfile.ZipFile(io.BytesIO(export_zip.content)) as zf:
            namelist = zf.namelist()
            assert "manifest.json" in namelist
            assert "receipt-v0.1.json" in namelist
            assert any(f.startswith("VaultBasis_Findings_") and f.endswith(".csv") for f in namelist)
            assert "VERIFY.html" in namelist
            assert "schemas/receipt-v0.1.json" in namelist
            assert any(f.startswith("evidence/") for f in namelist)

            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
            assert manifest["receipt_id"] == final_receipt["receipt_id"]
            assert manifest["case_id"] == case_id
            assert manifest["revision"] == 2

    def test_tampered_receipt_fails_verification(self, client):
        """Mutating payload content or signature in a receipt must immediately cause verifier to FAIL."""
        # Get sample receipt
        res = client.get("/api/cases/CASE-SAMPLE-2025/receipt")
        assert res.status_code == 200
        receipt = res.json()

        # Mutate an amount in receipt
        tampered_receipt = json.loads(json.dumps(receipt))
        tampered_receipt["material_differences"][0]["variance"] = "999999.00"

        ver_result = verify_outcome_receipt(tampered_receipt)
        assert ver_result.is_valid is False
        assert ver_result.signature_valid is False


# ============================================================================
# LAYER 7: SECRET HYGIENE & RESOURCE LIMITS (MMP15-SEC-QUAL-001 §7, §11, §12)
# ============================================================================

class TestSecretHygieneAndResourceLimits:
    """Validate that private commercial signing keys and sensitive credentials never leak."""

    def test_runtime_contains_no_commercial_private_keys(self):
        """The distributed package and repo runtime must never bundle private signing keys."""
        import os
        from pathlib import Path
        repo_root = Path(__file__).resolve().parent.parent.parent
        edge_dir = repo_root / "edge"
        
        # Search edge package for suspicious private key files
        suspicious_extensions = [".pem", ".key", ".pkcs8"]
        found_private_keys = []
        for root, _, files in os.walk(edge_dir):
            for file in files:
                if any(file.endswith(ext) for ext in suspicious_extensions):
                    found_private_keys.append(os.path.join(root, file))
        
        assert len(found_private_keys) == 0, f"Found private key artifacts in edge distribution: {found_private_keys}"

    def test_upload_exceeding_max_bytes_is_rejected(self, client):
        """Uploading files exceeding MAX_UPLOAD_BYTES (25MB) must be rejected fail-closed."""
        # Create a real case first
        case_res = client.post("/api/cases", json={
            "client_reference": "Resource Limit Test LLC",
            "tax_year": 2025
        })
        assert case_res.status_code == 201
        case_id = case_res.json()["case_id"]

        # Create a dummy large stream (26 MB)
        large_content = b"0" * (26 * 1024 * 1024)
        
        res = client.post(
            f"/api/cases/{case_id}/sources",
            files={"file": ("oversized.csv", io.BytesIO(large_content), "text/csv")}
        )
        assert res.status_code in (400, 413)
        assert "exceeds" in res.json().get("detail", "").lower() or "too large" in res.json().get("detail", "").lower()

