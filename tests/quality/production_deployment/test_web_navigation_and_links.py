"""
VaultBasis Quality Suite — Web Navigation, Header/Footer & Endpoint Integrity Test
Tag: regression, production-infra, web-standards, left-shift

Validates:
1. Standard header & footer across all web surfaces (marketing, verifier, dashboard).
2. All anchor links (#problem, #how-it-works, #security, #evidence-contract, #documentation) have matching DOM IDs.
3. External and internal routes (/verifier, /schemas/receipt-v0.1.json, /sample-receipt.json, /docs).
4. Interactive testing capabilities in the Web Verifier (instant golden valid and tampered testing).
5. FastAPI local daemon route endpoints serving schemas and sample receipts without 404s.
"""

import json
import re
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from edge.api.app import app

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.regression
def test_marketing_site_header_footer_and_anchor_links():
    """Validates marketing site headers, footers, and internal anchor integrity."""
    marketing_file = WORKSPACE_ROOT / "apps" / "web-marketing" / "index.html"
    assert marketing_file.is_file(), "apps/web-marketing/index.html must exist"
    html = marketing_file.read_text(encoding="utf-8")

    # 1. Header Navigation elements
    assert "The 1099-DA Dilemma" in html
    assert "How It Works" in html
    assert "Security Boundary" in html
    assert "Evidence Contract" in html
    assert "Public Verifier" in html
    assert "Launch Local Edge" in html

    # 2. Extract all href="#..." anchors and assert matching id="..." exists
    anchors = set(re.findall(r'href="#([a-zA-Z0-9_\-]+)"', html))
    assert len(anchors) >= 4, f"Expected multiple section anchors, found: {anchors}"
    for anchor in anchors:
        assert f'id="{anchor}"' in html, f"Broken link: href='#{anchor}' found but id='{anchor}' does not exist in DOM"

    # 3. Standard multi-column footer presence
    assert 'class="site-footer"' in html
    assert "STATUTORY LIMITATION NOTICE" in html
    assert "PRD §27" in html or "PRD §44.6" in html
    assert "TecTixBase" in html
    assert "System Status: Edge Runtime Operational" in html

    # 4. Sticky header clearance (scroll-padding-top and scroll-margin-top)
    assert "scroll-padding-top" in html, "scroll-padding-top required for sticky header anchor clearance"
    assert "scroll-margin-top" in html, "scroll-margin-top required for section anchor clearance"
    assert "scrollTo" in html, "smooth scroll offset logic required"


@pytest.mark.regression
def test_web_verifier_interactive_controls_and_footer():
    """Validates web verifier header, footer, and interactive one-click testing controls."""
    verifier_file = WORKSPACE_ROOT / "apps" / "web-verifier" / "index.html"
    assert verifier_file.is_file(), "apps/web-verifier/index.html must exist"
    html = verifier_file.read_text(encoding="utf-8")

    # Header navigation
    assert "VaultBasis Verifier" in html
    assert "← Why VaultBasis?" in html
    assert "Evidence Schema" in html

    # Interactive sample testing controls
    assert "loadSampleGoldenValid" in html
    assert "loadSampleGoldenTampered" in html
    assert "Test with Valid Sample Receipt" in html
    assert "Test with Tampered Receipt" in html

    # Results card checklist
    assert "JSON Schema Conformance" in html
    assert "Evidence Contract Version" in html
    assert "Declared Key Fingerprint Consistency" in html
    assert "Ed25519 Cryptographic Signature" in html

    # Standard footer
    assert 'class="site-footer"' in html
    assert "STATUTORY LIMITATION NOTICE" in html


@pytest.mark.regression
def test_web_dashboard_header_and_industrial_footer():
    """Validates dashboard header navigation and industrial airgap footer."""
    dashboard_file = WORKSPACE_ROOT / "apps" / "web-dashboard" / "index.html"
    assert dashboard_file.is_file(), "apps/web-dashboard/index.html must exist"
    html = dashboard_file.read_text(encoding="utf-8")

    # Header nav
    assert "Cases" in html
    assert "Why VaultBasis? ↗" in html
    assert "Independent Verifier ↗" in html
    assert "Evidence Schema ↗" in html

    # Industrial footer
    assert "Local Edge · Active" in html
    assert "Customer-controlled assurance processing" in html
    assert "Zero Transaction-Data Egress" in html


@pytest.mark.regression
def test_edge_daemon_serves_all_web_routes(client):
    """Asserts local FastAPI edge daemon serves all UI, schema, and sample receipt routes with HTTP 200."""
    # 1. Dashboard
    res = client.get("/")
    assert res.status_code == 200
    assert "VaultBasis Edge" in res.text

    # 2. Verifier
    res = client.get("/verifier")
    assert res.status_code == 200
    assert "VaultBasis Verifier" in res.text

    # 3. Marketing / About
    res = client.get("/about")
    assert res.status_code == 200
    assert "The 1099-DA Dilemma" in res.text

    # 4. Normative Schema
    res = client.get("/schemas/receipt-v0.1.json")
    assert res.status_code == 200
    schema_data = res.json()
    assert schema_data.get("title") == "VaultBasis Outcome Receipt v0.1"

    # 5. Golden Sample Valid Receipt
    res = client.get("/sample-receipt.json")
    assert res.status_code == 200
    sample_data = res.json()
    assert sample_data.get("receipt_version") == "v0.1"
    assert "signature" in sample_data

    # 6. Golden Sample Tampered Receipt
    res = client.get("/sample-receipt-tampered.json")
    assert res.status_code == 200
    tampered_data = res.json()
    assert tampered_data.get("receipt_version") == "v0.1"

    # 7. Health endpoint
    res = client.get("/api/health")
    assert res.status_code == 200
    health = res.json()
    assert health.get("status") == "HEALTHY"
    assert health.get("egress_policy") == "STRICT_LOCAL_ONLY"
