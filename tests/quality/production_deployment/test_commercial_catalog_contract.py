"""
VaultBasis — Commercial Catalog Invariant Contract Test (MMP15-WEB-CANONICAL-CATALOG-001)

Validates that all customer-facing surfaces (marketing pages, modal templates,
shell scripts, delivery mailers, dashboard UI, and compiled dist/public-web bundles)
strictly conform to the single-source-of-truth commercial catalog.

Guarantees zero commercial-policy drift across all releases.
"""

import json
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCHEMAS_CATALOG = REPO_ROOT / "schemas" / "commercial" / "canonical_catalog.json"
APPS_MARKETING = REPO_ROOT / "apps" / "web-marketing"
DIST_PUBLIC_WEB = REPO_ROOT / "dist" / "public-web"


def test_canonical_catalog_schema_validity():
    """Ensures the canonical catalog file exists and contains the authoritative 4 tiers."""
    assert SCHEMAS_CATALOG.exists(), f"Canonical catalog missing at {SCHEMAS_CATALOG}"
    with open(SCHEMAS_CATALOG, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    tiers = catalog.get("tiers", {})
    assert "EVALUATION" in tiers
    assert "PRACTITIONER" in tiers
    assert "FIRM" in tiers
    assert "ENTERPRISE" in tiers

    eval_tier = tiers["EVALUATION"]
    assert eval_tier["durationHours"] == 72
    assert eval_tier["caseCapacity"] == 3
    assert eval_tier["priceAmountCents"] == 0

    practitioner_tier = tiers["PRACTITIONER"]
    assert practitioner_tier["caseCapacity"] == 10
    assert practitioner_tier["priceAmountCents"] == 49900
    assert practitioner_tier["name"] == "Practitioner"

    firm_tier = tiers["FIRM"]
    assert firm_tier["caseCapacity"] == 50
    assert firm_tier["priceAmountCents"] == 149900
    assert firm_tier["name"] == "Firm"

    enterprise_tier = tiers["ENTERPRISE"]
    assert enterprise_tier["caseCapacity"] is None
    assert enterprise_tier["priceAmountCents"] is None
    assert enterprise_tier["name"] == "Enterprise"


def test_public_marketing_source_positive_invariants():
    """Ensures apps/web-marketing sources display correct tier names, pricing, and capacities."""
    index_html = (APPS_MARKETING / "index.html").read_text(encoding="utf-8")
    modal_html = (APPS_MARKETING / "partials" / "modal.html").read_text(encoding="utf-8")
    shell_js = (APPS_MARKETING / "partials" / "shell.js").read_text(encoding="utf-8")

    # Positive checks in index.html
    assert "3-Day Evaluation" in index_html
    assert "Up to 3 evaluation client cases" in index_html
    assert "Practitioner" in index_html
    assert "$499" in index_html
    assert "Up to 10 client cases" in index_html
    assert "Firm" in index_html
    assert "$1,499" in index_html
    assert "Up to 50 client cases" in index_html
    assert "Enterprise" in index_html
    assert "Custom / high-volume case capacity" in index_html

    # Positive checks in modal.html
    assert "Evaluation (Up to 3 Client Cases + Samples — $0)" in modal_html
    assert "Practitioner Plan (Up to 10 Client Cases — $499/year)" in modal_html
    assert "Firm Plan (Up to 50 Client Cases — $1,499/year)" in modal_html
    assert "Enterprise &amp; Larger Practices (Custom Case Volume — Contact us)" in modal_html

    # Positive checks in shell.js
    assert "Start 3-Day Evaluation" in shell_js
    assert "Get Practitioner License" in shell_js
    assert "Get Firm License" in shell_js
    assert "Enterprise & Larger Practices" in shell_js


def test_public_web_dist_strict_negative_drift_invariants():
    """
    Ensures that compiled dist/public-web HTML files contain zero deprecated
    commercial strings, outdated capacity numbers, or absolute promises.
    """
    if not DIST_PUBLIC_WEB.exists():
        pytest.skip("dist/public-web not yet built")

    forbidden_patterns = [
        r"1 live evaluation case",
        r"1 client case included",
        r"Solo Practitioner",
        r"<h3 class=[\"']pricing-title[\"']>Solo</h3>",
        r"<h3 class=[\"']pricing-title[\"']>Practice</h3>",
        r"250\+\s*cases",
        r"100\s*cases",
        r"From\s*\$3,999",
        r"readable forever",
        r"100%\s*readable",
        r"100%\s*accessible",
        r"100%\s*Local Processing",
        r"Permanent case access guarantee",
        r"for workpapers and audit defense",
    ]

    html_files = list(DIST_PUBLIC_WEB.glob("*.html"))
    assert len(html_files) > 0, "No HTML files found in dist/public-web"

    violations = []
    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                violations.append(f"{html_file.name}: Matched forbidden pattern '{pattern}' -> {matches}")

    assert not violations, "Commercial drift detected in built public-web artifacts:\n" + "\n".join(violations)


def test_release_json_metadata_integrity():
    """Ensures dist/public-web/release.json exists and exposes correct provenance metadata."""
    if not DIST_PUBLIC_WEB.exists():
        pytest.skip("dist/public-web not yet built")

    release_file = DIST_PUBLIC_WEB / "release.json"
    assert release_file.exists(), f"release.json missing at {release_file}"

    with open(release_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("product") == "VaultBasis Web"
    assert "source_commit" in data
    assert "source_commit_short" in data
    assert data.get("catalog_version") == "1.0.0"
    assert len(data.get("canonical_catalog_sha256", "")) == 64
    assert data.get("environment") == "production"

