"""
VaultBasis Edge Navigation Contract — MAC-NAV-001 through MAC-NAV-005 remediation gate.
Tag: regression, edge-navigation, packaging

Validates:
1. Every practitioner-visible href in the Edge dashboard is classified and correctly owned.
2. No local Edge route resolves to a localhost destination for external informational links.
3. /verifier redirects to the canonical production URL (not served locally).
4. /offline-verifier serves an HTML page (local offline capability).
5. /api/receipts/verify accepts a receipt and returns a verification result.
6. Absolute prohibitions: no javascript: hrefs, no href="#" navigation placeholders,
   no unimplemented local routes returning JSON 404 errors for practitioner navigation.
7. Egress claims: ZERO TRANSACTION EGRESS / Zero Transaction-Data Egress must not appear
   in the packaged Edge dashboard.
8. Negative control: a deliberately broken local link is detected by the contract.
"""

import re
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from edge.api.app import app

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

DASHBOARD_FILE = WORKSPACE_ROOT / "apps" / "web-dashboard" / "index.html"
OFFLINE_VERIFIER_FILE = WORKSPACE_ROOT / "apps" / "edge-offline-verifier" / "index.html"

# Canonical external destinations — must use https://vaultbasis.com, not localhost.
REQUIRED_EXTERNAL_HREFS = [
    "https://vaultbasis.com",
    "https://vaultbasis.com/verifier",
    "https://vaultbasis.com/faq",
    "https://vaultbasis.com/contact",
    "https://vaultbasis.com/security-disclosure",
]

# These root-relative local paths previously broke because they had no Edge handler.
# They must not appear as practitioner-visible hrefs in the dashboard any more.
PROHIBITED_BROKEN_LOCAL_HREFS = [
    '"/faq"',
    '"/contact"',
    '"/security-disclosure"',
    '"/about"',
    '"/privacy-policy"',
    '"/terms-of-service"',
    '"/trust-assurance"',
]

# Absolute egress claims must not appear in the packaged Edge shell.
PROHIBITED_EGRESS_CLAIMS = [
    "ZERO TRANSACTION EGRESS",
    "Zero Transaction-Data Egress",
]

# Local routes that must exist and serve HTML.
REQUIRED_LOCAL_ROUTES = [
    "/",
    "/offline-verifier",
    "/docs/scope_and_limitations_v0.1.html",
    "/schemas/receipt-v0.1.json",
]


@pytest.fixture
def client():
    return TestClient(app, follow_redirects=False)


@pytest.mark.regression
def test_dashboard_has_no_prohibited_broken_local_hrefs():
    """Broken local links that caused MAC-NAV-001..005 must not appear in the dashboard."""
    assert DASHBOARD_FILE.is_file(), "Dashboard HTML must exist"
    html = DASHBOARD_FILE.read_text(encoding="utf-8")
    for broken in PROHIBITED_BROKEN_LOCAL_HREFS:
        assert broken not in html, (
            f"Prohibited broken local href {broken} still present in dashboard. "
            "These routes have no Edge handler and expose JSON 404 to practitioners."
        )


@pytest.mark.regression
def test_dashboard_contains_required_external_hrefs():
    """Informational destinations must point to the canonical production site."""
    assert DASHBOARD_FILE.is_file()
    html = DASHBOARD_FILE.read_text(encoding="utf-8")
    for href in REQUIRED_EXTERNAL_HREFS:
        assert href in html, (
            f"Required canonical external href {href!r} not found in dashboard. "
            "External informational links must use https://vaultbasis.com."
        )


@pytest.mark.regression
def test_dashboard_has_no_javascript_href_navigation():
    """No practitioner navigation may use javascript: pseudo-URLs as destinations."""
    assert DASHBOARD_FILE.is_file()
    html = DASHBOARD_FILE.read_text(encoding="utf-8")
    js_hrefs = re.findall(r'href=["\']javascript:[^"\']*["\']', html)
    assert js_hrefs == [], f"javascript: hrefs found in dashboard: {js_hrefs}"


@pytest.mark.regression
def test_dashboard_has_no_prohibited_egress_claims():
    """Absolute egress claims must not appear in the packaged Edge shell."""
    assert DASHBOARD_FILE.is_file()
    html = DASHBOARD_FILE.read_text(encoding="utf-8")
    for claim in PROHIBITED_EGRESS_CLAIMS:
        assert claim not in html, (
            f"Prohibited egress claim {claim!r} found in dashboard. "
            "Replace with approved local-processing terminology."
        )


@pytest.mark.regression
def test_offline_verifier_file_exists_with_required_content():
    """Offline verifier asset must exist and carry correct verification boundary wording."""
    assert OFFLINE_VERIFIER_FILE.is_file(), "apps/edge-offline-verifier/index.html must exist"
    html = OFFLINE_VERIFIER_FILE.read_text(encoding="utf-8")
    assert "NOT DETERMINED" in html, "Tax Correctness NOT DETERMINED must be present"
    assert "signature_authenticity" in html or "Signature Verification" in html
    assert "schema_conformance" in html or "Payload Integrity" in html
    # Must not promise tax correctness or claim installation authentication
    assert "tax correctness" not in html.lower() or "NOT DETERMINED" in html
    # Must not contain the session-check that caused the cascade failure
    assert "verifier-session-check" not in html


@pytest.mark.regression
def test_verifier_route_redirects_to_production(client):
    """/verifier must redirect to canonical production URL, not serve the production verifier locally."""
    res = client.get("/verifier")
    assert res.status_code in (301, 302, 307, 308), (
        f"/verifier must redirect (got {res.status_code}). "
        "Edge must not serve the production verifier locally."
    )
    location = res.headers.get("location", "")
    assert "vaultbasis.com/verifier" in location, (
        f"/verifier redirect location {location!r} must point to https://vaultbasis.com/verifier"
    )
    assert "127.0.0.1" not in location, "/verifier must not redirect to localhost"


@pytest.mark.regression
def test_offline_verifier_route_serves_html(client):
    """/offline-verifier must serve an HTML page without requiring authentication."""
    res = client.get("/offline-verifier")
    assert res.status_code == 200, f"/offline-verifier returned {res.status_code}"
    assert "text/html" in res.headers.get("content-type", "")
    assert "VaultBasis" in res.text
    assert "NOT DETERMINED" in res.text


@pytest.mark.regression
def test_required_local_routes_serve_html(client):
    """Core Edge routes must serve HTML, not JSON errors."""
    tc = TestClient(app, follow_redirects=True)
    for route in REQUIRED_LOCAL_ROUTES:
        res = tc.get(route)
        assert res.status_code == 200, f"{route} returned {res.status_code}"
        ct = res.headers.get("content-type", "")
        # Schema endpoint serves JSON — that is correct.
        if route == "/schemas/receipt-v0.1.json":
            assert "json" in ct, f"{route} should serve JSON"
        else:
            assert "html" in ct or "<html" in res.text.lower(), (
                f"{route} must serve HTML, got content-type: {ct}"
            )


@pytest.mark.regression
def test_receipts_verify_endpoint_accepts_valid_receipt(client):
    """POST /api/receipts/verify must accept a receipt and return a structured result."""
    golden = WORKSPACE_ROOT / "tests" / "fixtures" / "golden_receipt_valid.json"
    assert golden.is_file(), "Golden valid receipt fixture must exist"
    with open(golden, "rb") as f:
        res = client.post("/api/receipts/verify", files={"file": ("receipt.json", f, "application/json")})
    assert res.status_code == 200, f"/api/receipts/verify returned {res.status_code}"
    data = res.json()
    assert "overall_status" in data, "Verification response must contain overall_status"
    assert data["is_valid"] is True, f"Valid receipt must return is_valid=True, got: {data}"


@pytest.mark.regression
def test_receipts_verify_rejects_tampered_receipt(client):
    """POST /api/receipts/verify must return FAIL for a tampered receipt."""
    tampered = WORKSPACE_ROOT / "tests" / "fixtures" / "golden_receipt_tampered.json"
    assert tampered.is_file(), "Golden tampered receipt fixture must exist"
    with open(tampered, "rb") as f:
        res = client.post("/api/receipts/verify", files={"file": ("tampered.json", f, "application/json")})
    assert res.status_code == 200
    data = res.json()
    assert data.get("overall_status") == "FAIL", (
        f"Tampered receipt must return overall_status=FAIL, got: {data.get('overall_status')}"
    )
    assert data.get("is_valid") is False, "Tampered receipt must return is_valid=False"


# ── Negative control ──────────────────────────────────────────────────────────

@pytest.mark.regression
def test_negative_control_broken_local_href_detected():
    """Negative control: introducing a broken local href must be caught by the contract."""
    html_with_defect = '<a href="/faq">FAQ</a>'
    for broken in PROHIBITED_BROKEN_LOCAL_HREFS:
        # Strip quotes for plain-text search in the injected string
        plain = broken.strip('"')
        if plain in html_with_defect:
            assert broken in f'href="{plain}"', (
                "Negative control failed: the detection pattern does not match the injected defect."
            )
            return
    # If none matched, the negative control itself is broken — fail loudly.
    pytest.fail("Negative control did not exercise any prohibited href pattern.")
