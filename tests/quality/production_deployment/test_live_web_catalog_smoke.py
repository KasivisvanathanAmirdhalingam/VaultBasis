#!/usr/bin/env python3
"""
VaultBasis — Live/Preview Deployment Commercial Catalog Smoke Test
(MMP15-WEB-CANONICAL-CATALOG-001)

Validates that any live Vercel Preview deployment or Production URL
(e.g., https://www.vaultbasis.com or https://*-vaultbasis.vercel.app)
strictly serves the canonical catalog copy and /release.json identity.

Usage:
  python3 tests/quality/production_deployment/test_live_web_catalog_smoke.py --url https://www.vaultbasis.com
  VAULTBASIS_LIVE_URL=https://preview-url.vercel.app pytest tests/quality/production_deployment/test_live_web_catalog_smoke.py
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
import argparse
import pytest

FORBIDDEN_PATTERNS = [
    (r"1 live evaluation case", "Obsolete 1-case evaluation copy"),
    (r"1 client case included", "Obsolete 1-case wording"),
    (r"<h3[^>]*>Solo</h3>", "Deprecated Solo tier heading"),
    (r"<h3[^>]*>Practice</h3>", "Deprecated Practice tier heading"),
    (r"250\+\s*cases", "Deprecated 250+ enterprise case capacity"),
    (r"100\s*cases", "Deprecated hardcoded 100 enterprise cases"),
    (r"From\s*\$3,999", "Deprecated enterprise price floor"),
    (r"readable forever", "Deprecated permanent access guarantee"),
    (r"Permanent case access guarantee", "Deprecated permanent access guarantee"),
    (r"for workpapers and audit defense", "Deprecated legal guarantee wording"),
]

REQUIRED_SUBSTRINGS = [
    "3-Day Evaluation",
    "Up to 3 evaluation client cases",
    "Practitioner",
    "$499",
    "Up to 10 client cases",
    "Firm",
    "$1,499",
    "Up to 50 client cases",
    "Enterprise",
    "Custom / high-volume case capacity",
]


def verify_live_url(base_url: str) -> dict:
    """Performs HTTP GET against the target URL and asserts catalog invariants."""
    base_url = base_url.rstrip("/")
    results = {
        "url": base_url,
        "release_json_checked": False,
        "release_metadata": None,
        "html_checked": False,
        "passed": False,
        "errors": []
    }

    # 1. Fetch and verify /release.json
    release_url = f"{base_url}/release.json"
    try:
        req = urllib.request.Request(
            release_url,
            headers={"User-Agent": "VaultBasis-Catalog-Smoke/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                raw_data = resp.read().decode("utf-8")
                metadata = json.loads(raw_data)
                results["release_json_checked"] = True
                results["release_metadata"] = metadata
                if metadata.get("product") != "VaultBasis Web":
                    results["errors"].append(f"Invalid product name in release.json: {metadata.get('product')}")
                if not metadata.get("source_commit"):
                    results["errors"].append("Missing source_commit in release.json")
                if not metadata.get("canonical_catalog_sha256"):
                    results["errors"].append("Missing canonical_catalog_sha256 in release.json")
            else:
                results["errors"].append(f"/release.json returned HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        results["errors"].append(f"/release.json HTTP error: {e.code} {e.reason}")
    except Exception as e:
        results["errors"].append(f"/release.json connection error: {str(e)}")

    # 1.1 Check Assets: /favicon.ico and /favicon.svg
    for asset in ["/favicon.ico", "/favicon.svg"]:
        asset_url = f"{base_url}{asset}"
        try:
            req = urllib.request.Request(
                asset_url,
                headers={"User-Agent": "VaultBasis-Catalog-Smoke/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    results["errors"].append(f"{asset} returned HTTP {resp.status}")
        except Exception as e:
            results["errors"].append(f"{asset} asset request failed: {str(e)}")

    # 2. Fetch and verify root /
    try:
        req = urllib.request.Request(
            f"{base_url}/",
            headers={"User-Agent": "VaultBasis-Catalog-Smoke/1.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                html = resp.read().decode("utf-8")
                results["html_checked"] = True

                # Assert Document Title
                title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
                if not title_match or "VaultBasis" not in title_match.group(1):
                    results["errors"].append(f"Document title missing or does not contain 'VaultBasis': {title_match.group(1) if title_match else 'None'}")

                # Assert required positive strings (DOM & dynamic modal script)
                for req_str in REQUIRED_SUBSTRINGS:
                    if req_str not in html:
                        results["errors"].append(f"Missing required canonical string: '{req_str}'")

                # Assert dynamic modal JS & DOM select options
                modal_invariants = [
                    (r"Up to 3 Client Cases", "Evaluation modal option 3 cases invariant"),
                    (r"Up to 10 Client Cases", "Practitioner modal option 10 cases invariant"),
                    (r"Up to 50 Client Cases", "Firm modal option 50 cases invariant"),
                    (r"Custom Case Volume|Custom / high-volume", "Enterprise modal Custom invariant"),
                    (r"TRIAL['\"].*?3\s*(?:evaluation\s*)?client\s*cases", "Evaluation JS modal description 3 cases invariant"),
                    (r"ESSENTIAL['\"].*?10\s*client\s*cases", "Practitioner JS modal description 10 cases invariant"),
                    (r"PRACTICE['\"].*?50\s*client\s*cases", "Firm JS modal description 50 cases invariant"),
                    (r"ENTERPRISE['\"].*?Custom", "Enterprise JS modal description Custom invariant"),
                ]
                for pattern, desc in modal_invariants:
                    if not re.search(pattern, html, re.IGNORECASE | re.DOTALL):
                        results["errors"].append(f"Dynamic modal missing invariant: {desc}")

                # Assert forbidden negative patterns
                for pattern, desc in FORBIDDEN_PATTERNS:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    if matches:
                        results["errors"].append(f"Detected forbidden pattern: {desc} ('{pattern}') -> {matches}")
            else:
                results["errors"].append(f"Root URL returned HTTP {resp.status}")
    except Exception as e:
        results["errors"].append(f"Root HTML connection error: {str(e)}")

    results["passed"] = len(results["errors"]) == 0
    return results


def test_live_domain_commercial_catalog():
    """
    Pytest test case for live deployment validation.
    Runs when VAULTBASIS_LIVE_URL environment variable is supplied.
    """
    live_url = os.environ.get("VAULTBASIS_LIVE_URL")
    if not live_url:
        pytest.skip("VAULTBASIS_LIVE_URL not set; skipping live remote smoke test.")

    res = verify_live_url(live_url)
    assert res["passed"], f"Live catalog smoke test failed on {live_url}:\n" + "\n".join(res["errors"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VaultBasis Live Catalog Smoke Test")
    parser.add_argument("--url", default=os.environ.get("VAULTBASIS_LIVE_URL", "https://www.vaultbasis.com"),
                        help="Target base URL to verify (e.g. https://www.vaultbasis.com or preview URL)")
    args = parser.parse_args()

    print(f"Testing target deployment: {args.url}")
    result = verify_live_url(args.url)

    if result["release_metadata"]:
        print(f"✓ /release.json verified:")
        print(f"  Source Commit:  {result['release_metadata'].get('source_commit')}")
        print(f"  Catalog SHA256: {result['release_metadata'].get('canonical_catalog_sha256')}")
        print(f"  Built At:       {result['release_metadata'].get('built_at')}")
    else:
        print(f"⚠️ /release.json could not be verified.")

    if result["passed"]:
        print(f"\n✅ PASS: Deployment at {args.url} conforms 100% to Canonical Commercial Catalog.")
        sys.exit(0)
    else:
        print(f"\n❌ FAIL: Deployment at {args.url} violated canonical catalog invariants:")
        for err in result["errors"]:
            print(f"  - {err}")
        sys.exit(1)
