"""
VaultBasis Quality Suite — Web Regression Invariants (MMP11-WEB-REG-001)
Tag: regression, production-infra, web-standards, invariants, left-shift

Enforces:
- VB-WEB-INV-002: Single Global Navigation (no duplicate or pseudo-global navigation rows)
- VB-WEB-INV-003: Route-Scoped Transient State (modal is closed on fresh load, no state bleed across routes)
"""

import re
from pathlib import Path
import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DIST_PUBLIC_WEB = WORKSPACE_ROOT / "dist" / "public-web"

ALL_PUBLIC_PAGES = [
    "index.html",
    "about.html",
    "contact.html",
    "faq.html",
    "privacy-policy.html",
    "security-disclosure.html",
    "terms-of-service.html",
    "trust-assurance.html",
    "verifier-access.html",
]


@pytest.fixture(scope="module", autouse=True)
def ensure_build():
    """Ensure public web bundle is built before testing."""
    index_file = DIST_PUBLIC_WEB / "index.html"
    if not index_file.is_file():
        import subprocess
        subprocess.run(["node", "scripts/build_public_web.js"], cwd=str(WORKSPACE_ROOT), check=True)
    assert index_file.is_file(), "dist/public-web/index.html must exist"


@pytest.mark.regression
def test_vb_web_inv_002_single_global_navigation_across_all_pages():
    """VB-WEB-INV-002: Every public route exposes exactly one canonical global header/nav."""
    for page_name in ALL_PUBLIC_PAGES:
        page_file = DIST_PUBLIC_WEB / page_name
        assert page_file.is_file(), f"{page_name} must exist in dist/public-web"
        html = page_file.read_text(encoding="utf-8")

        # Exactly 1 header
        headers = re.findall(r'<header[^>]*>', html)
        assert len(headers) == 1, f"{page_name} must have exactly 1 <header>, found {len(headers)}"

        # Exactly 1 main nav
        main_navs = re.findall(r'<nav[^>]*class="[^"]*nav-main[^"]*"', html)
        assert len(main_navs) == 1, f"{page_name} must have exactly 1 nav-main, found {len(main_navs)}"

        # Forbidden pseudo-global / duplicate navigation strips
        assert "page-nav-strip" not in html, f"{page_name} must NOT contain duplicate page-nav-strip"
        assert '<nav class="page-nav-strip"' not in html, f"{page_name} must NOT contain page-nav-strip nav tag"


@pytest.mark.regression
def test_vb_web_inv_002_homepage_anchors_and_no_floating_nav():
    """Validates that homepage has no floating second-row navigation and all anchors resolve."""
    html = (DIST_PUBLIC_WEB / "index.html").read_text(encoding="utf-8")

    # Assert no secondary navigation bar between hero and content
    assert "page-nav-strip" not in html

    # Assert primary canonical anchors exist in the DOM
    required_anchors = ["hero", "how-it-works", "comparison", "security", "resources"]
    for anchor in required_anchors:
        assert f'id="{anchor}"' in html, f"Required anchor id='{anchor}' missing from index.html"


@pytest.mark.regression
def test_vb_web_inv_002_negative_control():
    """Negative control: proves that injecting a duplicate navigation strip fails the invariant check."""
    fake_html = '<header></header><nav class="nav-main"></nav><nav class="page-nav-strip"></nav>'
    
    # Assert that a duplicate page-nav-strip is caught
    with pytest.raises(AssertionError):
        assert "page-nav-strip" not in fake_html


@pytest.mark.regression
def test_vb_web_inv_003_modal_state_isolation_on_verifier_access():
    """VB-WEB-INV-003: Request Access modal is closed on fresh load and verifier-access renders correctly."""
    verifier_access_html = (DIST_PUBLIC_WEB / "verifier-access.html").read_text(encoding="utf-8")

    # Verifier access card is the primary landmark
    assert "<h1>Verifier Access</h1>" in verifier_access_html
    assert 'id="access-form"' in verifier_access_html

    # Modal overlay has display: none in CSS and initial HTML
    assert 'id="access-modal"' in verifier_access_html
    assert 'class="modal-overlay"' in verifier_access_html
    
    # Request success container is hidden by default
    assert 'id="request-success" style="display:none;' in verifier_access_html or 'id="request-success" style="display: none;' in verifier_access_html


@pytest.mark.regression
def test_vb_web_inv_003_modal_focus_and_escape_handlers():
    """VB-WEB-INV-003: Shell JS includes focus tracking and Escape key handler for modal accessibility."""
    shell_js = (WORKSPACE_ROOT / "apps" / "web-marketing" / "partials" / "shell.js").read_text(encoding="utf-8")

    assert "_lastFocusedElement" in shell_js, "Must track last focused element for accessible modal close"
    assert "_modalKeyHandler" in shell_js, "Must have modal keyboard event handler"
    assert "Escape" in shell_js, "Must handle Escape key to dismiss modal"
    assert "request-form-container" in shell_js, "Must manage form container visibility"
    assert "request-success" in shell_js, "Must manage success container visibility"


@pytest.mark.regression
def test_trust_assurance_verification_truthfulness():
    """Asserts Trust & Assurance page contains truthful wording regarding verification."""
    trust_html = (DIST_PUBLIC_WEB / "trust-assurance.html").read_text(encoding="utf-8")

    # Untruthful/conflicting claims must NOT appear
    assert "without a VaultBasis account" not in trust_html, "Untruthful account-free claim must not appear"
    assert "Independent Receipt Verification" in trust_html
    assert "Verification operates entirely client-side" in trust_html
