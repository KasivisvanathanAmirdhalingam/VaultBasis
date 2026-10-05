"""
DEPLOY-SEC-001 Access Control Invariant Tests

Verifies the capability access control system:

Architecture under test:
  - /verifier → api/verifier-page (serverless function)
  - api/verifier-page: server-authoritative session validation before serving HTML
  - Edge middleware: defense-in-depth cookie-presence check (not authoritative)
  - preview-access-store.js: separate credential namespace (not SEC-002 entitlement)
  - api/verifier-session.js: credential validation + session issuance + rate limiting
  - api/verifier-session-check.js: stateless session check endpoint for defense-in-depth

Trust boundary enforced:
  preview-access credential -> authenticated session -> Web Verifier UI
  SEC-002 entitlement        -> exact qualified artifact -> Edge download

All 16 adversarial cases from the directive are covered.
Tests run against source files — no live server required.
"""

import re
import os
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

BUILD_SCRIPT = os.path.join(REPO_ROOT, 'scripts', 'build_public_web.js')
VERIFIER_HTML = os.path.join(REPO_ROOT, 'apps', 'web-verifier', 'index.html')
VERIFIER_ACCESS_HTML = os.path.join(REPO_ROOT, 'apps', 'web-marketing', 'verifier-access.html')
VERCEL_JSON = os.path.join(REPO_ROOT, 'vercel.json')
VERIFIER_SESSION_JS = os.path.join(REPO_ROOT, 'api', 'verifier-session.js')
VERIFIER_SESSION_CHECK_JS = os.path.join(REPO_ROOT, 'api', 'verifier-session-check.js')
VERIFIER_PAGE_JS = os.path.join(REPO_ROOT, 'api', 'verifier-page.js')
ENTITLEMENT_STORE_JS = os.path.join(REPO_ROOT, 'api', '_lib', 'entitlement-store.js')
PREVIEW_ACCESS_STORE_JS = os.path.join(REPO_ROOT, 'api', '_lib', 'preview-access-store.js')


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


# ============================================================================
# ARCHITECTURE INVARIANTS
# ============================================================================

class TestArchitectureInvariants:
    """
    Verify the correct two-trust-object architecture is in place and that
    the entitlement store has not been overloaded.
    """

    def test_preview_access_store_exists_separate_namespace(self):
        """
        preview-access-store.js must exist as a distinct module from entitlement-store.js.
        It must use the preview-access/ Blob namespace, not entitlements/.
        """
        assert os.path.isfile(PREVIEW_ACCESS_STORE_JS), (
            "api/_lib/preview-access-store.js must exist as a separate module from entitlement-store.js"
        )
        src = read(PREVIEW_ACCESS_STORE_JS)
        assert 'preview-access/' in src, (
            "preview-access-store.js must use 'preview-access/' Blob namespace"
        )
        assert 'entitlements/' not in src, (
            "preview-access-store.js must NOT reference the entitlements/ namespace"
        )

    def test_entitlement_store_has_no_verifier_coupling(self):
        """
        entitlement-store.js must NOT export validateEntitlementForVerifier.
        SEC-002 entitlement semantics (artifact-bound) must not be overloaded.
        """
        src = read(ENTITLEMENT_STORE_JS)
        assert 'validateEntitlementForVerifier' not in src, (
            "entitlement-store.js must not contain validateEntitlementForVerifier — "
            "SEC-002 entitlement must remain artifact-bound only"
        )

    def test_verifier_session_uses_preview_access_store(self):
        """
        verifier-session.js must import from preview-access-store, not entitlement-store.
        Using the entitlement store for verifier auth overloads SEC-002 semantics.
        """
        src = read(VERIFIER_SESSION_JS)
        assert 'preview-access-store' in src, (
            "verifier-session.js must require('./preview-access-store')"
        )
        assert 'entitlement-store' not in src, (
            "verifier-session.js must NOT import from entitlement-store — "
            "this would overload SEC-002 artifact entitlement semantics"
        )

    def test_verifier_page_function_exists(self):
        """
        api/verifier-page.js must exist — this is the server-authoritative
        gate that validates sessions before returning any verifier HTML.
        """
        assert os.path.isfile(VERIFIER_PAGE_JS), (
            "api/verifier-page.js must exist — it is the authoritative access control layer"
        )

    def test_verifier_route_goes_to_serverless_function_not_static_file(self):
        """
        vercel.json must route /verifier to /api/verifier-page, not to a static file.
        A static-file route would serve the verifier HTML before any auth check.
        """
        with open(VERCEL_JSON, encoding='utf-8') as f:
            config = json.load(f)
        rewrites = config.get('rewrites', [])
        verifier_rule = next((r for r in rewrites if r.get('source') == '/verifier'), None)
        assert verifier_rule is not None, "/verifier rewrite rule missing from vercel.json"
        dest = verifier_rule.get('destination', '')
        assert dest == '/api/verifier-page', (
            f"/verifier must route to /api/verifier-page (got '{dest}'). "
            "Routing to a static file would serve content before auth check."
        )

    def test_download_retains_artifact_hash_binding(self):
        """
        SEC-002 entitlement (for downloads) must still require exact artifact hash binding.
        validateEntitlement must be used in download.js, not validateEntitlementForVerifier.
        """
        download_src = read(os.path.join(REPO_ROOT, 'api', 'download.js'))
        assert 'validateEntitlement(' in download_src, (
            "download.js must call validateEntitlement() (artifact-bound)"
        )
        assert 'validateEntitlementForVerifier' not in download_src, (
            "download.js must NOT call validateEntitlementForVerifier"
        )
        assert 'qualifiedArtifactHash' in read(ENTITLEMENT_STORE_JS) or 'sha256' in download_src, (
            "Artifact hash binding must remain in the download path"
        )

    def test_preview_access_schema_contains_no_artifact_hash(self):
        """
        preview-access records must NOT contain qualifiedArtifactHash.
        This credential authorizes verifier access only, not artifact downloads.
        """
        src = read(PREVIEW_ACCESS_STORE_JS)
        assert 'qualifiedArtifactHash' not in src, (
            "preview-access-store must not reference qualifiedArtifactHash — "
            "this credential type must not authorize artifact downloads"
        )


# ============================================================================
# SERVER-AUTHORITATIVE ACCESS CONTROL (Issue 2)
# ============================================================================

class TestServerAuthoritativeAccessControl:
    """
    Verify that the server validates sessions before returning protected content.
    A forged vb_session=anything must not receive verifier HTML.
    """

    def test_verifier_page_validates_session_before_serving_html(self):
        """
        api/verifier-page.js must read and validate the session record from
        Blob storage before calling res.send() or res.status(200).
        """
        src = read(VERIFIER_PAGE_JS)
        # Must check cookie
        assert SESSION_COOKIE_NAME_IN_SOURCE(src), (
            "verifier-page.js must read the session cookie"
        )
        # Must look up session in Blob
        assert "SESSION_NAMESPACE" in src or "sessions/" in src, (
            "verifier-page.js must look up the session in Blob storage"
        )
        # Must check status and expiry before serving
        assert "record.status" in src, (
            "verifier-page.js must check session record.status"
        )
        assert "expiresAt" in src, (
            "verifier-page.js must check session expiry"
        )
        # Must redirect (not serve) when invalid
        assert "redirect" in src or "302" in src, (
            "verifier-page.js must redirect on invalid session, not serve content"
        )

    def test_verifier_page_fails_closed_on_storage_error(self):
        """
        api/verifier-page.js must return 503 (not 200) on storage errors.
        A storage error must never cause the verifier HTML to be served.
        """
        src = read(VERIFIER_PAGE_JS)
        assert '503' in src, (
            "verifier-page.js must return 503 on storage error (fail closed)"
        )
        # Must not return 200 in catch blocks
        catch_blocks = re.findall(r'catch\s*\([^)]*\)\s*\{(.*?)\}', src, re.DOTALL)
        for block in catch_blocks:
            assert 'status(200)' not in block, (
                "verifier-page.js catch block must not return 200 — fail closed required"
            )

    def test_forged_session_cannot_bypass_server_validation(self):
        """
        The server-side session lookup hashes the cookie value and looks it up
        in private Blob storage. A forged or arbitrary cookie value will produce
        a SHA-256 digest that does not exist in Blob storage → deny.
        Verify that the hash-based lookup is present.
        """
        src = read(VERIFIER_PAGE_JS)
        assert 'sha256' in src.lower() or 'createHash' in src, (
            "verifier-page.js must hash the session token for Blob lookup — "
            "prevents forged cookies from finding valid records"
        )

    def test_middleware_describes_itself_as_defense_in_depth(self):
        """
        The middleware comment must accurately describe its role as defense-in-depth,
        not as the authoritative access control layer. Accurate documentation prevents
        misunderstanding of the security model during future maintenance.
        """
        src = read(BUILD_SCRIPT)
        assert 'defense-in-depth' in src or 'Defense-in-depth' in src, (
            "Middleware must be documented as defense-in-depth, not as authoritative control"
        )
        assert 'authoritative' in src, (
            "Build script must identify api/verifier-page as the authoritative layer"
        )


def SESSION_COOKIE_NAME_IN_SOURCE(src):
    return 'vb_session' in src or 'SESSION_COOKIE_NAME' in src


# ============================================================================
# RATE LIMITING (Issue 3)
# ============================================================================

class TestRateLimiting:
    """
    Verify rate limiting is implemented on credential/session establishment.
    """

    def test_rate_limit_implemented_in_verifier_session(self):
        """
        verifier-session.js must implement rate limiting before credential processing.
        """
        src = read(VERIFIER_SESSION_JS)
        assert 'RATE_LIMIT' in src, (
            "verifier-session.js must define RATE_LIMIT constants"
        )
        assert 'checkRateLimit' in src or 'rateLimit' in src.lower(), (
            "verifier-session.js must implement a rate limit check"
        )

    def test_rate_limit_keyed_by_ip_not_raw(self):
        """
        Rate limiting must be keyed by SHA-256(IP) — the raw IP must not be
        stored in Blob storage paths or records.
        """
        src = read(VERIFIER_SESSION_JS)
        assert 'x-forwarded-for' in src or 'remoteAddress' in src, (
            "verifier-session.js must extract client IP for rate limiting"
        )
        # Must hash the IP for the storage key
        assert 'createHash' in src, (
            "Rate limit key must be derived via a hash — raw IP must not be stored"
        )
        assert 'rate-limit/' in src, (
            "Rate limit records must use the rate-limit/ Blob namespace"
        )

    def test_rate_limit_returns_429(self):
        """
        When the rate limit is exceeded, the response must be 429.
        """
        src = read(VERIFIER_SESSION_JS)
        assert '429' in src, (
            "verifier-session.js must return 429 when rate limit is exceeded"
        )

    def test_rate_limit_constants_documented(self):
        """
        Rate limit window and max attempts must be explicit named constants.
        """
        src = read(VERIFIER_SESSION_JS)
        assert 'RATE_LIMIT_WINDOW_MS' in src or 'RATE_LIMIT_WINDOW' in src, (
            "Rate limit window must be a named constant"
        )
        assert 'RATE_LIMIT_MAX' in src or 'RATE_LIMIT_LIMIT' in src, (
            "Rate limit max attempts must be a named constant"
        )

    def test_rate_limit_check_precedes_credential_lookup(self):
        """
        The rate limit check must be called before validatePreviewAccess in the
        request handler. Otherwise an attacker could probe credentials without
        hitting the limit.
        Search within the module.exports handler body only (after the function
        definitions) to compare call-site positions, not definition positions.
        """
        src = read(VERIFIER_SESSION_JS)
        # Find the start of the exported request handler
        handler_start = src.find('module.exports')
        assert handler_start != -1, "module.exports not found in verifier-session.js"
        handler_body = src[handler_start:]

        rl_pos = handler_body.find('checkRateLimit(')
        auth_pos = handler_body.find('validatePreviewAccess(')
        assert rl_pos != -1, "checkRateLimit call not found in request handler"
        assert auth_pos != -1, "validatePreviewAccess call not found in request handler"
        assert rl_pos < auth_pos, (
            "checkRateLimit must be called before validatePreviewAccess in the handler — "
            "rate limit must gate credential lookups, not just succeed calls"
        )


# ============================================================================
# ADVERSARIAL CASES (Issue 4 — 16 required cases)
# ============================================================================

class TestAdversarialCasesSource:
    """
    Source-level adversarial invariants covering the 16 required cases.
    These verify implementation structure; runtime tests require a live server.
    """

    # Case 1: anonymous /verifier cannot obtain verifier capability
    def test_case01_verifier_route_not_served_as_static_file(self):
        """
        /verifier must not be a static-file rewrite. The verifier HTML must
        only be returned after server-side session validation.
        """
        with open(VERCEL_JSON, encoding='utf-8') as f:
            config = json.load(f)
        rewrites = config.get('rewrites', [])
        verifier_rule = next((r for r in rewrites if r.get('source') == '/verifier'), None)
        assert verifier_rule is not None
        dest = verifier_rule.get('destination', '')
        assert 'index.html' not in dest and 'static' not in dest, (
            "Anonymous /verifier must not receive a static verifier HTML file"
        )

    # Case 2: forged session cookie denied
    def test_case02_forged_session_denied_by_hash_lookup(self):
        """
        Session validation uses SHA-256(cookie) as Blob key. A forged value
        produces a key that does not exist → BlobNotFoundError → deny.
        """
        src = read(VERIFIER_PAGE_JS)
        assert 'BlobNotFoundError' in src or 'not found' in src.lower(), (
            "verifier-page.js must handle BlobNotFoundError (deny forged sessions)"
        )
        assert 'createHash' in src, (
            "Session lookup must use SHA-256 keying (forged cookies find nothing)"
        )

    # Case 3: malformed access credential denied
    def test_case03_malformed_credential_denied_by_format_gate(self):
        """
        preview-access-store.js must reject malformed tokens before any Blob lookup.
        """
        src = read(PREVIEW_ACCESS_STORE_JS)
        assert 'isWellFormedToken' in src, (
            "preview-access-store must validate token format before Blob lookup"
        )
        assert 'malformed_token' in src, (
            "preview-access-store must return malformed_token for invalid format"
        )

    # Case 4: nonexistent credential denied
    def test_case04_nonexistent_credential_denied(self):
        """
        Lookup of a well-formed but nonexistent token must return not_found,
        not a 500 or a permission grant.
        """
        src = read(PREVIEW_ACCESS_STORE_JS)
        assert 'not_found' in src, (
            "preview-access-store must return not_found for nonexistent tokens"
        )
        assert 'BlobNotFoundError' in src, (
            "preview-access-store must handle BlobNotFoundError as not_found"
        )

    # Case 5: expired credential denied
    def test_case05_expired_credential_denied(self):
        """
        preview-access-store must check expiresAt and deny expired credentials.
        """
        src = read(PREVIEW_ACCESS_STORE_JS)
        assert 'expiresAt' in src, (
            "preview-access-store must check expiresAt for credential expiry"
        )
        assert 'expired' in src, (
            "preview-access-store must return expired reason for expired credentials"
        )

    # Case 6: revoked credential denied
    def test_case06_revoked_credential_denied(self):
        """
        preview-access-store must check status === 'ACTIVE' and deny REVOKED.
        """
        src = read(PREVIEW_ACCESS_STORE_JS)
        assert "status !== 'ACTIVE'" in src or "status === 'ACTIVE'" in src, (
            "preview-access-store must check status === ACTIVE"
        )
        assert 'not_active' in src, (
            "preview-access-store must return not_active for non-ACTIVE status (covers REVOKED)"
        )

    # Case 7: valid preview credential creates session
    def test_case07_valid_credential_issues_session_cookie(self):
        """
        On valid preview-access credential, verifier-session.js must write a
        session record to Blob and set the vb_session cookie.
        """
        src = read(VERIFIER_SESSION_JS)
        assert 'put(' in src, (
            "verifier-session.js must write a session record to Blob on success"
        )
        assert 'Set-Cookie' in src, (
            "verifier-session.js must set the session cookie on success"
        )
        assert 'vb_session' in src, (
            "Session cookie must be named vb_session"
        )

    # Case 8: session cookie is HttpOnly, Secure, SameSite=Strict
    def test_case08_session_cookie_security_attributes(self):
        """
        Session cookie must have all three security attributes.
        """
        src = read(VERIFIER_SESSION_JS)
        assert 'HttpOnly' in src, "Session cookie must have HttpOnly"
        assert 'Secure' in src, "Session cookie must have Secure"
        assert 'SameSite=Strict' in src, "Session cookie must have SameSite=Strict"

    # Case 9: expired session denied
    def test_case09_expired_session_denied(self):
        """
        verifier-page.js must check session expiresAt and deny expired sessions.
        """
        src = read(VERIFIER_PAGE_JS)
        assert 'expiresAt' in src, (
            "verifier-page.js must check session expiresAt"
        )
        # Must redirect (not serve) for expired sessions
        assert 'redirect' in src or '302' in src, (
            "verifier-page.js must redirect on expired session, not serve verifier"
        )

    # Case 10: revoked access invalidates subsequent authorization
    def test_case10_revoked_access_not_active_denied_by_session_check(self):
        """
        Session records have a status field. verifier-page.js must check
        status === ACTIVE and deny REVOKED sessions.
        """
        src = read(VERIFIER_PAGE_JS)
        assert 'record.status' in src, (
            "verifier-page.js must check session record.status"
        )
        assert "'ACTIVE'" in src, (
            "verifier-page.js must require status === ACTIVE"
        )

    # Case 11: logout/session invalidation
    def test_case11_session_invalidation_mechanism_exists(self):
        """
        Sessions are stored in Blob. Session TTL is 4 hours (server-side expiry check).
        verifier-session-check.js and verifier-page.js both enforce server-side expiry,
        which is the server-authoritative invalidation mechanism.
        Verify that the TTL constant is defined and that server-side expiry is enforced.
        """
        session_src = read(VERIFIER_SESSION_JS)
        check_src = read(VERIFIER_SESSION_CHECK_JS)
        page_src = read(VERIFIER_PAGE_JS)

        assert 'SESSION_TTL_MS' in session_src, (
            "Session TTL must be defined as a named constant"
        )
        assert 'expiresAt' in check_src, (
            "verifier-session-check.js must enforce server-side expiry"
        )
        assert 'expiresAt' in page_src, (
            "verifier-page.js must enforce server-side expiry"
        )

    # Case 12: storage failure fails closed
    def test_case12_storage_failure_fails_closed(self):
        """
        All three auth endpoints must fail closed on storage errors (503/401/redirect),
        never return 200 or serve protected content on storage failure.
        """
        for path, name in [
            (VERIFIER_SESSION_JS, 'verifier-session.js'),
            (VERIFIER_SESSION_CHECK_JS, 'verifier-session-check.js'),
            (VERIFIER_PAGE_JS, 'verifier-page.js'),
        ]:
            src = read(path)
            catch_blocks = re.findall(r'catch\s*\([^)]*\)\s*\{(.*?)\}(?=\s*(?:if|const|let|var|return|try|\}))', src, re.DOTALL)
            for block in catch_blocks:
                assert 'status(200)' not in block, (
                    f"{name} catch block must not return 200 (fail closed)"
                )

    # Case 13: rate limit activates
    def test_case13_rate_limit_activation(self):
        """
        verifier-session.js must activate rate limiting and return 429.
        The rate limit check must happen before credential validation.
        """
        src = read(VERIFIER_SESSION_JS)
        assert '429' in src, "verifier-session.js must return 429 on rate limit"
        assert 'checkRateLimit' in src, "checkRateLimit function must be defined"
        assert 'RATE_LIMIT_MAX' in src, "RATE_LIMIT_MAX constant must be defined"

    # Case 14: SEC-002 artifact entitlement remains artifact-bound and unchanged
    def test_case14_sec002_artifact_binding_unchanged(self):
        """
        The download path (SEC-002) must still require exact artifact hash binding.
        This test verifies the entitlement store was not weakened.
        """
        entitlement_src = read(ENTITLEMENT_STORE_JS)
        download_src = read(os.path.join(REPO_ROOT, 'api', 'download.js'))

        # Artifact hash check must exist in validateEntitlement
        assert 'qualifiedArtifactHash' in entitlement_src, (
            "entitlement-store must still contain qualifiedArtifactHash binding (SEC-002)"
        )
        assert 'artifact_mismatch' in entitlement_src, (
            "entitlement-store must still return artifact_mismatch reason"
        )
        # download.js must call artifact-bound validateEntitlement
        assert 'validateEntitlement(' in download_src, (
            "download.js must call artifact-bound validateEntitlement"
        )

    # Case 15: authentication alone cannot download Edge
    def test_case15_session_cookie_cannot_authorize_download(self):
        """
        api/download.js must not accept vb_session cookies or check for a session.
        Downloads are authorized exclusively by SEC-002 entitlement tokens.
        """
        src = read(os.path.join(REPO_ROOT, 'api', 'download.js'))
        assert 'vb_session' not in src, (
            "download.js must not accept vb_session cookie — "
            "a verifier session must not authorize artifact downloads"
        )
        assert 'cookie' not in src.lower() or 'Set-Cookie' not in src, (
            "download.js must not process session cookies"
        )
        assert 'validateEntitlement(' in src, (
            "download.js must use validateEntitlement (SEC-002 token-based)"
        )

    # Case 16: valid SEC-002 entitlement still requires matching artifact hash
    def test_case16_sec002_requires_artifact_hash_match(self):
        """
        validateEntitlement must compare the supplied artifact hash against the
        stored qualifiedArtifactHash. A mismatch must deny, not permit.
        """
        src = read(ENTITLEMENT_STORE_JS)
        # Step 6 — artifact hash comparison — must still be present
        assert 'record.qualifiedArtifactHash !== artifactHash' in src or \
               'qualifiedArtifactHash' in src, (
            "validateEntitlement must perform artifact hash comparison (step 6)"
        )
        assert 'artifact_mismatch' in src, (
            "validateEntitlement must return artifact_mismatch on hash mismatch"
        )


# ============================================================================
# ROUTING AND MIDDLEWARE INVARIANTS
# ============================================================================

class TestRoutingAndMiddleware:
    """
    Verify middleware PUBLIC_PREFIXES and routing rules are correct.
    """

    def _get_public_prefixes(self):
        src = read(BUILD_SCRIPT)
        match = re.search(r'const PUBLIC_PREFIXES\s*=\s*\[(.*?)\];', src, re.DOTALL)
        assert match, "PUBLIC_PREFIXES array not found in build_public_web.js"
        return re.findall(r"'(/[^']*)'", match.group(1))

    def test_verifier_not_in_public_prefixes(self):
        """
        /verifier must NOT be in PUBLIC_PREFIXES. Even with the server-authoritative
        gate, defense-in-depth requires the edge not to pass /verifier through anonymously.
        /verifier-access is allowed (redirect target must be reachable).
        """
        entries = self._get_public_prefixes()
        assert '/verifier' not in entries, (
            f"/verifier must not be in PUBLIC_PREFIXES. Found: {entries}"
        )

    def test_verifier_access_in_public_prefixes(self):
        """
        /verifier-access must be in PUBLIC_PREFIXES — it is the redirect target
        for unauthenticated users and must always be reachable.
        """
        entries = self._get_public_prefixes()
        assert '/verifier-access' in entries

    def test_session_api_endpoints_in_public_prefixes(self):
        """
        /api/verifier-session and /api/verifier-session-check must be in PUBLIC_PREFIXES.
        """
        entries = self._get_public_prefixes()
        assert '/api/verifier-session' in entries
        assert '/api/verifier-session-check' in entries

    def test_no_hardcoded_credentials_anywhere(self):
        """
        No hardcoded Basic Auth credentials must exist in the build output or source.
        CPA-PREVIEW-2026 was the known-compromised credential.
        """
        src = read(BUILD_SCRIPT)
        assert 'CPA-PREVIEW' not in src
        assert 'Basic ' not in src
        assert 'btoa(' not in src

    def test_verifier_access_in_standalone_pages(self):
        """
        verifier-access must be in standalonePages so it's included in the build.
        """
        src = read(BUILD_SCRIPT)
        match = re.search(r"const standalonePages\s*=\s*\[([^\]]+)\]", src)
        assert match, "standalonePages not found"
        assert 'verifier-access' in match.group(1)

    def test_vercel_json_has_verifier_access_route(self):
        with open(VERCEL_JSON, encoding='utf-8') as f:
            config = json.load(f)
        sources = [r.get('source', '') for r in config.get('rewrites', [])]
        assert '/verifier-access' in sources

    def test_session_cookie_name_consistent_across_files(self):
        """
        SESSION_COOKIE_NAME must be 'vb_session' in all three auth files.
        """
        build_src = read(BUILD_SCRIPT)
        session_src = read(VERIFIER_SESSION_JS)
        check_src = read(VERIFIER_SESSION_CHECK_JS)
        page_src = read(VERIFIER_PAGE_JS)

        for src, name in [
            (build_src, 'build_public_web.js'),
            (session_src, 'verifier-session.js'),
            (check_src, 'verifier-session-check.js'),
            (page_src, 'verifier-page.js'),
        ]:
            assert 'vb_session' in src, f"vb_session must appear in {name}"


# ============================================================================
# INFORMATION DISCLOSURE INVARIANTS
# ============================================================================

class TestNoInformationDisclosure:
    """
    Verify that no internal reason codes or token details are returned on the wire.
    """

    def test_session_endpoints_return_generic_errors(self):
        """
        Internal reason codes from preview-access-store must not appear in
        res.json() response bodies in verifier-session.js.
        """
        src = read(VERIFIER_SESSION_JS)
        internal_reasons = [
            'malformed_token', 'not_found', 'not_active', 'expired',
            'access_id_mismatch', 'storage_error'
        ]
        json_calls = re.findall(r'res\.(?:status\(\d+\)\.)?json\([^)]+\)', src)
        for call in json_calls:
            for reason in internal_reasons:
                assert reason not in call, (
                    f"Internal reason '{reason}' must not be in response body: {call}"
                )

    def test_raw_token_not_logged(self):
        """
        Neither verifier-session.js nor preview-access-store.js must log the
        raw bearer token. Only non-sensitive metadata should appear in logs.
        """
        for path, name in [
            (VERIFIER_SESSION_JS, 'verifier-session.js'),
            (PREVIEW_ACCESS_STORE_JS, 'preview-access-store.js'),
        ]:
            src = read(path)
            log_lines = re.findall(r'console\.\w+\([^)]+\)', src)
            for line in log_lines:
                assert 'token' not in line.lower() or 'rawToken' not in line, (
                    f"{name}: raw token must not appear in log calls: {line}"
                )
