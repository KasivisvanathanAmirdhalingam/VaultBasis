"""
VaultBasis Quality Suite — Production Deployment & Vercel Incremental Build Test
Tag: regression, production-infra, vercel, left-shift

Validates:
1. vercel.json configuration integrity, security headers, and rewrite routes.
2. package.json deployment and validation scripts.
3. Deterministic execution of scripts/build_public_web.js.
4. Output distribution directory (dist/public-web) contents.
5. Zero private-key or database leakage into production deployment artifacts.
6. Public Web bridge awareness preserving PRD §21.1 (Zero Token Bleed / Zero Transaction Egress).
"""

import json
import os
import subprocess
from pathlib import Path
import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@pytest.mark.regression
def test_vercel_configuration_validity():
    """Validates that vercel.json exists, conforms to Vercel schema, and has strict security headers."""
    vercel_path = WORKSPACE_ROOT / "vercel.json"
    assert vercel_path.is_file(), "vercel.json must exist at repository root for incremental deployment"

    with open(vercel_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    assert config.get("version") == 2, "vercel.json version must be 2"
    assert config.get("outputDirectory") == "dist/public-web", "outputDirectory must point to dist/public-web"
    assert "build_public_web.js" in config.get("buildCommand", ""), "buildCommand must invoke build_public_web.js"
    assert config.get("cleanUrls") is True, "cleanUrls must be enabled"

    # Verify rewrites
    rewrites = {r.get("source"): r.get("destination") for r in config.get("rewrites", [])}
    assert "/verifier" in rewrites, "/verifier route must be rewritten"
    assert rewrites["/verifier"] == "/api/verifier-page", (
        "/verifier must route to /api/verifier-page (server-authoritative session gate), "
        "not a static file"
    )
    assert "/about" in rewrites
    assert "/marketing" in rewrites

    # Verify headers
    headers_list = config.get("headers", [])
    assert len(headers_list) > 0, "Security headers must be declared"
    root_header = next((h for h in headers_list if h.get("source") == "/(.*)"), None)
    assert root_header is not None, "Universal security headers must be applied to /(.*)"
    
    header_map = {kv["key"].lower(): kv["value"] for kv in root_header.get("headers", [])}
    assert "x-content-type-options" in header_map
    assert header_map["x-content-type-options"] == "nosniff"
    assert "x-frame-options" in header_map
    assert header_map["x-frame-options"] == "DENY"
    assert "strict-transport-security" in header_map


@pytest.mark.regression
def test_package_json_scripts():
    """Validates that package.json contains required build and deployment scripts."""
    pkg_path = WORKSPACE_ROOT / "package.json"
    assert pkg_path.is_file(), "package.json must exist at root"

    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    scripts = pkg.get("scripts", {})
    assert "build" in scripts, "build script required"
    assert "validate" in scripts, "validate script required"
    assert "deploy:preview" in scripts, "deploy:preview script required"
    assert "deploy:prod" in scripts, "deploy:prod script required"
    assert "build_public_web.js" in scripts["build"]


@pytest.mark.regression
def test_incremental_build_execution_and_artifacts():
    """Executes build_public_web.js and asserts all public distribution artifacts are produced."""
    build_script = WORKSPACE_ROOT / "scripts" / "build_public_web.js"
    assert build_script.is_file(), "scripts/build_public_web.js must exist"

    result = subprocess.run(
        ["node", str(build_script)],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"build_public_web.js failed:\n{result.stderr}\n{result.stdout}"
    assert "PUBLIC WEB DISTRIBUTION READY FOR VERCEL DEPLOYMENT" in result.stdout

    dist_dir = WORKSPACE_ROOT / "dist" / "public-web"
    assert dist_dir.is_dir(), "dist/public-web directory must be created"

    # 1. Marketing Portal
    marketing_index = dist_dir / "index.html"
    assert marketing_index.is_file(), "dist/public-web/index.html must exist"
    marketing_html = marketing_index.read_text(encoding="utf-8")
    assert "VaultBasis" in marketing_html
    assert "Evidence Receipt" in marketing_html
    assert "Try VaultBasis Free" in marketing_html

    # 2. Web Verifier must NOT be a static file in outputDirectory.
    # Vercel serves static files before rewrites — placing verifier/index.html
    # here would bypass the /api/verifier-page auth gate (ACCESS-INV-001).
    # The verifier HTML is served exclusively by api/verifier-page.js.
    verifier_index = dist_dir / "verifier" / "index.html"
    assert not verifier_index.exists(), (
        "dist/public-web/verifier/index.html must NOT exist — "
        "placing the verifier HTML in outputDirectory bypasses the server-side "
        "auth gate in api/verifier-page.js (Vercel serves static files before rewrites)"
    )
    # Verify the verifier source exists (api/verifier-page.js reads it at runtime)
    verifier_source = WORKSPACE_ROOT / "apps" / "web-verifier" / "index.html"
    assert verifier_source.is_file(), "apps/web-verifier/index.html must exist (served by api/verifier-page.js)"

    # 3. Normative Schema
    schema_file = dist_dir / "schemas" / "receipt-v0.1.json"
    assert schema_file.is_file(), "dist/public-web/schemas/receipt-v0.1.json must exist"
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_json = json.load(f)
    assert schema_json.get("title") == "VaultBasis Outcome Receipt v0.1"

    # 4. Custom 404 Page
    custom_404 = dist_dir / "404.html"
    assert custom_404.is_file(), "dist/public-web/404.html must exist"


@pytest.mark.regression
def test_zero_egress_and_secret_leak_in_build_artifacts():
    """Ensures production build distribution contains zero private keys, SQLite databases, or credentials."""
    dist_dir = WORKSPACE_ROOT / "dist" / "public-web"
    assert dist_dir.is_dir()

    forbidden_extensions = {".key", ".pem", ".db", ".sqlite", ".sqlite3", ".env", ".log"}
    found_forbidden = []

    for item in dist_dir.rglob("*"):
        if item.is_file():
            if item.suffix.lower() in forbidden_extensions or "vaultbasis.db" in item.name.lower():
                found_forbidden.append(str(item))

    assert len(found_forbidden) == 0, f"SECURITY VIOLATION: Forbidden sensitive files found in Vercel bundle: {found_forbidden}"


@pytest.mark.regression
def test_dual_tier_localhost_bridge_integrity():
    """Verifies that the public marketing page safely mediates access without leaking sensitive client data."""
    marketing_file = WORKSPACE_ROOT / "apps" / "web-marketing" / "index.html"
    content = marketing_file.read_text(encoding="utf-8")

    # Asserts that no sensitive form inputs post to unauthorized remote servers
    assert "action=\"http" not in content.lower()
    # Asserts that the access request modal is present
    assert "openAccessModal" in content
