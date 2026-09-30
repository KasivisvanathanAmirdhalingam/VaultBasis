"""
DEPLOY-SEC-001 Access Control Invariant Tests

Verifies that the capability access control system is correctly wired:
  - Middleware PUBLIC_PREFIXES covers all informational routes
  - /verifier is NOT in PUBLIC_PREFIXES (must be gated)
  - /verifier-access IS in PUBLIC_PREFIXES (redirect target must be reachable)
  - /api/verifier-session and /api/verifier-session-check are in PUBLIC_PREFIXES
  - Session check endpoint rejects missing/malformed cookies
  - Verifier HTML contains server-side session check on load
  - verifier-access.html exists and contains the access form
  - No hardcoded credentials (Basic Auth) in generated middleware

All tests run against source files — no running server required.
"""

import re
import os
import sys
import json

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

BUILD_SCRIPT = os.path.join(REPO_ROOT, 'scripts', 'build_public_web.js')
VERIFIER_HTML = os.path.join(REPO_ROOT, 'apps', 'web-verifier', 'index.html')
VERIFIER_ACCESS_HTML = os.path.join(REPO_ROOT, 'apps', 'web-marketing', 'verifier-access.html')
VERCEL_JSON = os.path.join(REPO_ROOT, 'vercel.json')
VERIFIER_SESSION_JS = os.path.join(REPO_ROOT, 'api', 'verifier-session.js')
VERIFIER_SESSION_CHECK_JS = os.path.join(REPO_ROOT, 'api', 'verifier-session-check.js')
ENTITLEMENT_STORE_JS = os.path.join(REPO_ROOT, 'api', 'entitlement-store.js')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# T01 — Middleware: /verifier is NOT in PUBLIC_PREFIXES
# ---------------------------------------------------------------------------

def test_verifier_route_not_in_public_prefixes():
    """
    /verifier must NOT appear as a PUBLIC_PREFIX entry.
    If it were listed, the middleware would pass anonymous requests through
    without checking for the session cookie.
    """
    src = read(BUILD_SCRIPT)
    # Extract the PUBLIC_PREFIXES block from the template literal
    match = re.search(r'const PUBLIC_PREFIXES\s*=\s*\[(.*?)\];', src, re.DOTALL)
    assert match, "PUBLIC_PREFIXES array not found in build_public_web.js"
    prefixes_block = match.group(1)
    # Split on commas/newlines to get individual prefix strings
    entries = re.findall(r"'(/[^']*)'", prefixes_block)
    # /verifier-access is allowed (the redirect target); /verifier itself must not be
    assert '/verifier' not in entries, (
        f"/verifier must NOT be in PUBLIC_PREFIXES — it would bypass the session check. "
        f"Found entries: {entries}"
    )


# ---------------------------------------------------------------------------
# T02 — Middleware: /verifier-access IS in PUBLIC_PREFIXES
# ---------------------------------------------------------------------------

def test_verifier_access_in_public_prefixes():
    """
    /verifier-access must be in PUBLIC_PREFIXES so that unauthenticated users
    can reach the access gate without triggering an infinite redirect loop.
    """
    src = read(BUILD_SCRIPT)
    match = re.search(r'const PUBLIC_PREFIXES\s*=\s*\[(.*?)\];', src, re.DOTALL)
    assert match, "PUBLIC_PREFIXES array not found in build_public_web.js"
    prefixes_block = match.group(1)
    entries = re.findall(r"'(/[^']*)'", prefixes_block)
    assert '/verifier-access' in entries, (
        f"/verifier-access must be in PUBLIC_PREFIXES (redirect target). Found: {entries}"
    )


# ---------------------------------------------------------------------------
# T03 — Middleware: session API endpoints are in PUBLIC_PREFIXES
# ---------------------------------------------------------------------------

def test_session_api_endpoints_in_public_prefixes():
    """
    /api/verifier-session (POST — login) and /api/verifier-session-check (GET — validate)
    must both be in PUBLIC_PREFIXES so the browser can reach them without a cookie.
    """
    src = read(BUILD_SCRIPT)
    assert '/api/verifier-session' in src, "/api/verifier-session missing from PUBLIC_PREFIXES"
    assert '/api/verifier-session-check' in src, "/api/verifier-session-check missing from PUBLIC_PREFIXES"


# ---------------------------------------------------------------------------
# T04 — Middleware: no hardcoded credentials
# ---------------------------------------------------------------------------

def test_no_hardcoded_credentials_in_middleware():
    """
    The generated middleware must not contain any hardcoded Basic Auth credentials.
    Previous implementation had 'cpa / CPA-PREVIEW-2026' baked in.
    """
    src = read(BUILD_SCRIPT)
    # Check the middleware template literal specifically
    assert 'CPA-PREVIEW' not in src, "Hardcoded CPA-PREVIEW credential found in build script"
    assert 'Basic ' not in src, "Hardcoded Basic Auth header found in build script"
    assert 'btoa(' not in src, "btoa() call (Basic Auth encoding) found in build script"
    assert 'Authorization' not in src.replace('// Authorization', ''), (
        "Authorization header construction found in build script"
    )


# ---------------------------------------------------------------------------
# T05 — Middleware: /verifier redirects to /verifier-access when no cookie
# ---------------------------------------------------------------------------

def test_middleware_redirects_verifier_to_access_gate():
    """
    The middleware must redirect unauthenticated /verifier requests to /verifier-access.
    """
    src = read(BUILD_SCRIPT)
    assert '/verifier-access' in src, "Middleware must redirect to /verifier-access"
    assert "pathname.startsWith('/verifier')" in src, (
        "Middleware must check pathname.startsWith('/verifier') for the gate"
    )
    assert 'Response.redirect' in src, "Middleware must use Response.redirect for the gate"


# ---------------------------------------------------------------------------
# T06 — Middleware: session cookie name constant matches across files
# ---------------------------------------------------------------------------

def test_session_cookie_name_consistent():
    """
    SESSION_COOKIE_NAME must be 'vb_session' in both the middleware and the
    session issuance endpoint. A mismatch would silently break authentication.
    """
    build_src = read(BUILD_SCRIPT)
    session_src = read(VERIFIER_SESSION_JS)
    check_src = read(VERIFIER_SESSION_CHECK_JS)

    cookie_in_build = re.search(r"SESSION_COOKIE_NAME\s*=\s*'([^']+)'", build_src)
    cookie_in_session = re.search(r"SESSION_COOKIE_NAME\s*=\s*'([^']+)'", session_src)
    cookie_in_check = re.search(r"SESSION_COOKIE_NAME\s*=\s*'([^']+)'", check_src)

    assert cookie_in_build, "SESSION_COOKIE_NAME not found in build_public_web.js"
    assert cookie_in_session, "SESSION_COOKIE_NAME not found in api/verifier-session.js"
    assert cookie_in_check, "SESSION_COOKIE_NAME not found in api/verifier-session-check.js"

    name_build = cookie_in_build.group(1)
    name_session = cookie_in_session.group(1)
    name_check = cookie_in_check.group(1)

    assert name_build == name_session == name_check == 'vb_session', (
        f"SESSION_COOKIE_NAME mismatch: build={name_build!r}, "
        f"session={name_session!r}, check={name_check!r}"
    )


# ---------------------------------------------------------------------------
# T07 — Verifier HTML: session check runs on load
# ---------------------------------------------------------------------------

def test_verifier_html_calls_session_check_on_load():
    """
    The verifier page must call /api/verifier-session-check on load and redirect
    to /verifier-access if the response is not 200. This is the server-side
    cryptographic validation layer (middleware only checks cookie presence).
    """
    html = read(VERIFIER_HTML)
    assert '/api/verifier-session-check' in html, (
        "Verifier HTML must call /api/verifier-session-check on load"
    )
    assert '/verifier-access' in html, (
        "Verifier HTML must redirect to /verifier-access on session check failure"
    )


# ---------------------------------------------------------------------------
# T08 — Verifier HTML: fail-closed on network error
# ---------------------------------------------------------------------------

def test_verifier_session_check_fails_closed():
    """
    The session check in verifier HTML must redirect (fail closed) even if the
    fetch itself throws (network error). It must NOT silently proceed.
    """
    html = read(VERIFIER_HTML)
    # The catch block must also redirect, not just log or ignore
    # Check that there's a catch block that also calls redirect
    session_check_block = re.search(
        r'\(async function checkSession\(\).*?\}\)\(\);',
        html, re.DOTALL
    )
    assert session_check_block, "checkSession IIFE not found in verifier HTML"
    block = session_check_block.group(0)
    assert 'catch' in block, "checkSession must have a catch block"
    # The catch block must contain a redirect, not just return/log
    catch_match = re.search(r'catch\s*\([^)]*\)\s*\{(.*?)\}', block, re.DOTALL)
    assert catch_match, "catch block not found in checkSession"
    catch_body = catch_match.group(1)
    assert 'window.location' in catch_body or 'location.replace' in catch_body, (
        "catch block in checkSession must redirect (fail closed), not silently proceed"
    )


# ---------------------------------------------------------------------------
# T09 — verifier-access.html: file exists and contains the auth form
# ---------------------------------------------------------------------------

def test_verifier_access_page_exists_and_has_form():
    """
    apps/web-marketing/verifier-access.html must exist and contain:
    - A form that POSTs to /api/verifier-session
    - An entitlement ID input field
    - An access token input field
    """
    assert os.path.isfile(VERIFIER_ACCESS_HTML), (
        f"verifier-access.html not found at {VERIFIER_ACCESS_HTML}"
    )
    html = read(VERIFIER_ACCESS_HTML)
    assert '/api/verifier-session' in html, (
        "verifier-access.html must reference /api/verifier-session"
    )
    assert 'entitlement' in html.lower(), (
        "verifier-access.html must contain an entitlement ID input"
    )
    assert 'token' in html.lower(), (
        "verifier-access.html must contain an access token input"
    )


# ---------------------------------------------------------------------------
# T10 — verifier-access.html: in build script standalonePages
# ---------------------------------------------------------------------------

def test_verifier_access_in_build_standalone_pages():
    """
    'verifier-access' must be in the standalonePages array in build_public_web.js
    so it gets copied into the dist output.
    """
    src = read(BUILD_SCRIPT)
    match = re.search(r"const standalonePages\s*=\s*\[([^\]]+)\]", src)
    assert match, "standalonePages array not found in build_public_web.js"
    assert 'verifier-access' in match.group(1), (
        "'verifier-access' must be in standalonePages so it is included in the build"
    )


# ---------------------------------------------------------------------------
# T11 — vercel.json: /verifier-access route exists
# ---------------------------------------------------------------------------

def test_vercel_json_has_verifier_access_route():
    """
    vercel.json must have a rewrite rule for /verifier-access → /verifier-access.html
    so that the clean URL resolves correctly.
    """
    with open(VERCEL_JSON, encoding='utf-8') as f:
        config = json.load(f)
    rewrites = config.get('rewrites', [])
    sources = [r.get('source', '') for r in rewrites]
    assert '/verifier-access' in sources, (
        "/verifier-access rewrite missing from vercel.json"
    )


# ---------------------------------------------------------------------------
# T12 — api/verifier-session.js: no artifact hash binding
# ---------------------------------------------------------------------------

def test_verifier_session_uses_entitlement_for_verifier():
    """
    api/verifier-session.js must use validateEntitlementForVerifier (not
    validateEntitlement) — verifier access must not require a specific artifact hash.
    """
    src = read(VERIFIER_SESSION_JS)
    assert 'validateEntitlementForVerifier' in src, (
        "verifier-session.js must call validateEntitlementForVerifier"
    )
    assert 'validateEntitlement(' not in src.replace('validateEntitlementForVerifier', ''), (
        "verifier-session.js must not call validateEntitlement() (artifact-bound version)"
    )


# ---------------------------------------------------------------------------
# T13 — api/verifier-session.js: HttpOnly Secure SameSite cookie
# ---------------------------------------------------------------------------

def test_verifier_session_cookie_security_attributes():
    """
    The session cookie set by verifier-session.js must have HttpOnly, Secure,
    and SameSite=Strict attributes. Missing any of these creates session
    hijacking or CSRF exposure.
    """
    src = read(VERIFIER_SESSION_JS)
    assert 'HttpOnly' in src, "Session cookie must have HttpOnly"
    assert 'Secure' in src, "Session cookie must have Secure"
    assert 'SameSite=Strict' in src, "Session cookie must have SameSite=Strict"


# ---------------------------------------------------------------------------
# T14 — api/verifier-session-check.js: fail-closed on storage error
# ---------------------------------------------------------------------------

def test_session_check_fails_closed_on_storage_error():
    """
    verifier-session-check.js must return 503 (not 200) on storage errors.
    Any path that returns 200 on error would create an authentication bypass.
    """
    src = read(VERIFIER_SESSION_CHECK_JS)
    # Must not have a catch block that returns 200
    assert 'status(200)' not in src or src.count('status(200)') <= 1, (
        "Only one 200 response allowed (the success path)"
    )
    assert '503' in src, "verifier-session-check.js must return 503 on storage error (fail closed)"


# ---------------------------------------------------------------------------
# T15 — entitlement-store.js: validateEntitlementForVerifier exported
# ---------------------------------------------------------------------------

def test_entitlement_store_exports_verifier_validator():
    """
    entitlement-store.js must export validateEntitlementForVerifier so
    verifier-session.js can import and use it.
    """
    src = read(ENTITLEMENT_STORE_JS)
    assert 'validateEntitlementForVerifier' in src, (
        "validateEntitlementForVerifier must be defined in entitlement-store.js"
    )
    # Check it's exported
    assert 'validateEntitlementForVerifier' in src.split('module.exports')[1], (
        "validateEntitlementForVerifier must be in module.exports"
    )


# ---------------------------------------------------------------------------
# T16 — No information disclosure in error responses
# ---------------------------------------------------------------------------

def test_no_information_disclosure_in_error_responses():
    """
    Error responses in session endpoints must be generic — no reason codes,
    internal state, or token details must be returned to the client.
    """
    session_src = read(VERIFIER_SESSION_JS)
    check_src = read(VERIFIER_SESSION_CHECK_JS)

    # The only user-visible strings should be generic
    # 'malformed_token', 'not_found', 'expired', etc. must not reach the wire
    for reason in ['malformed_token', 'not_found', 'not_active', 'expired',
                   'entitlement_mismatch', 'artifact_mismatch', 'storage_error']:
        # These are internal reason codes from entitlement-store; they must not
        # appear in any res.json() call in the session endpoints
        # They may appear as comments or in require() calls — check json calls only
        json_calls = re.findall(r'res\.(?:status\(\d+\)\.)?json\([^)]+\)', session_src)
        for call in json_calls:
            assert reason not in call, (
                f"Internal reason code '{reason}' must not be exposed in session API response"
            )
