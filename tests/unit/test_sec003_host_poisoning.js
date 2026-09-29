/**
 * SEC-003 Regression Test — Host-Header Poisoning in request-access.js
 *
 * Vulnerability: request-access.js line 31 trusts `X-Forwarded-Host` directly,
 * allowing an attacker to inject an arbitrary host into the provisioning email
 * download URL.
 *
 * This test:
 *  - Verifies the CURRENT (pre-fix) behaviour: the download URL host is taken
 *    from the attacker-supplied X-Forwarded-Host header.           [FAIL before fix]
 *  - Verifies the POST-FIX behaviour: the download URL host is always the
 *    canonical PUBLIC_BASE_URL, never a header-supplied value.     [PASS after fix]
 *
 * Run with:  node tests/unit/test_sec003_host_poisoning.js
 */

'use strict';

const assert = require('assert');
const path = require('path');

// ---------------------------------------------------------------------------
// Minimal stub helpers
// ---------------------------------------------------------------------------

/**
 * Build a mock req/res pair sufficient to exercise the URL-construction path
 * without actually sending email.  We override nodemailer so the async path
 * completes and we can inspect the generated downloadUrl.
 */
function makeMockReq({ xForwardedHost, host } = {}) {
  return {
    method: 'POST',
    body: { email: 'test@example.com', name: 'Test User' },
    headers: {
      ...(xForwardedHost !== undefined ? { 'x-forwarded-host': xForwardedHost } : {}),
      ...(host !== undefined ? { host } : {}),
    },
  };
}

function makeMockRes() {
  const res = {
    _status: null,
    _body: null,
    status(code) { this._status = code; return this; },
    json(body)  { this._body = body; return this; },
  };
  return res;
}

// ---------------------------------------------------------------------------
// Intercept nodemailer so tests never hit the network
// ---------------------------------------------------------------------------
const Module = require('module');
const originalLoad = Module._load;

let capturedDownloadUrl = null;

// Minimal blob stub — entitlement-store now reads the manifest before URL generation.
const STUB_MANIFEST = JSON.stringify({
  artifacts: [{ os: 'macos', architecture: 'arm64',
    blobPathname: 'rc3/current/VaultBasis-RC3-macOS-arm64.zip',
    sha256: 'a'.repeat(64) }]
});
const stubBlobStore = new Map([['rc3/current/manifest.json', STUB_MANIFEST]]);
function makeStubBlobStream(str) {
  const buf = Buffer.from(str, 'utf8');
  return { stream: { getReader() { let s=false; return { async read() {
    if (!s) { s=true; return { done: false, value: buf }; }
    return { done: true, value: undefined };
  }}; }}};
}
class StubBlobNotFoundError extends Error {
  constructor(m) { super(m); this.name = 'BlobNotFoundError'; }
}

Module._load = function (request, parent, isMain) {
  if (request === '@vercel/blob') {
    return {
      BlobNotFoundError: StubBlobNotFoundError,
      get: async (pathname) => {
        if (!stubBlobStore.has(pathname)) throw new StubBlobNotFoundError(pathname);
        return makeStubBlobStream(stubBlobStore.get(pathname));
      },
      put: async (pathname, body) => {
        stubBlobStore.set(pathname, typeof body === 'string' ? body : body.toString());
        return { pathname };
      },
    };
  }
  if (request === 'nodemailer') {
    return {
      createTestAccount: async () => ({ user: 'u', pass: 'p' }),
      createTransport: () => ({
        sendMail: async (opts) => {
          // Extract the href of the download link from the HTML body
          const match = opts.html.match(/href="([^"]+\/api\/download[^"]*)"/);
          if (match) capturedDownloadUrl = match[1];
          return { messageId: 'stub' };
        },
      }),
      getTestMessageUrl: () => 'http://ethereal.stub/msg/1',
    };
  }
  return originalLoad.apply(this, arguments);
};

// ---------------------------------------------------------------------------
// Load the handler under test (relative to worktree root)
// ---------------------------------------------------------------------------
const HANDLER_PATHS = [
  path.resolve(__dirname, '../../apps/web-marketing/api/request-access.js'),
  path.resolve(__dirname, '../../api/request-access.js'),
];

async function runTests() {
  let passed = 0;
  let failed = 0;

  for (const handlerPath of HANDLER_PATHS) {
    // Reset module cache so each file gets a fresh require
    delete require.cache[require.resolve(handlerPath)];
    capturedDownloadUrl = null;

    const handler = require(handlerPath);
    const label = handlerPath.includes('apps/web-marketing') ? 'apps/web-marketing/api/request-access.js' : 'api/request-access.js';

    // ------------------------------------------------------------------
    // TEST 1 — Pre-fix failure demonstration
    // A request with X-Forwarded-Host: attacker.example CURRENTLY causes
    // the download URL to use attacker.example as the host.
    // After the fix this test case should be superseded by Test 2.
    // ------------------------------------------------------------------
    {
      capturedDownloadUrl = null;
      const req = makeMockReq({ xForwardedHost: 'attacker.example', host: 'vaultbasis.com' });
      const res = makeMockRes();
      await handler(req, res);

      const url = capturedDownloadUrl || '';
      const urlHost = url ? new URL(url).hostname : '';

      // After the fix, the host MUST NOT be attacker.example.
      // Before the fix, urlHost === 'attacker.example' — this assertion then FAILS.
      try {
        assert.notStrictEqual(
          urlHost,
          'attacker.example',
          `[${label}] SECURITY: download URL must not use X-Forwarded-Host (attacker.example). Got: ${url}`
        );
        console.log(`PASS [${label}] Test 1 — X-Forwarded-Host is NOT used as the download URL host`);
        passed++;
      } catch (err) {
        console.error(`FAIL [${label}] Test 1 — X-Forwarded-Host poisoning reproduced: ${err.message}`);
        failed++;
      }
    }

    // ------------------------------------------------------------------
    // TEST 2 — Post-fix requirement
    // The download URL must use the canonical origin from PUBLIC_BASE_URL
    // (or the localhost fallback), never from any request header.
    // ------------------------------------------------------------------
    {
      capturedDownloadUrl = null;
      const savedEnv = process.env.PUBLIC_BASE_URL;
      process.env.PUBLIC_BASE_URL = 'https://vaultbasis.com';

      // Reset module cache so the env var is picked up by the fresh require
      delete require.cache[require.resolve(handlerPath)];
      const freshHandler = require(handlerPath);

      const req = makeMockReq({ xForwardedHost: 'attacker.example', host: 'should-not-appear.example' });
      const res = makeMockRes();
      await freshHandler(req, res);

      const url = capturedDownloadUrl || '';
      const urlOrigin = url ? `${new URL(url).protocol}//${new URL(url).host}` : '';

      if (savedEnv === undefined) delete process.env.PUBLIC_BASE_URL;
      else process.env.PUBLIC_BASE_URL = savedEnv;

      try {
        assert.strictEqual(
          urlOrigin,
          'https://vaultbasis.com',
          `[${label}] SECURITY: download URL must use PUBLIC_BASE_URL. Got: ${url}`
        );
        console.log(`PASS [${label}] Test 2 — download URL uses PUBLIC_BASE_URL canonical origin`);
        passed++;
      } catch (err) {
        console.error(`FAIL [${label}] Test 2 — canonical origin not used: ${err.message}`);
        failed++;
      }
    }

    // ------------------------------------------------------------------
    // TEST 3 — Localhost fallback (no PUBLIC_BASE_URL set)
    // ------------------------------------------------------------------
    {
      capturedDownloadUrl = null;
      const savedEnv = process.env.PUBLIC_BASE_URL;
      delete process.env.PUBLIC_BASE_URL;

      delete require.cache[require.resolve(handlerPath)];
      const freshHandler = require(handlerPath);

      const req = makeMockReq({ xForwardedHost: 'attacker.example', host: 'vaultbasis.com' });
      const res = makeMockRes();
      await freshHandler(req, res);

      const url = capturedDownloadUrl || '';
      const urlOrigin = url ? `${new URL(url).protocol}//${new URL(url).host}` : '';

      if (savedEnv !== undefined) process.env.PUBLIC_BASE_URL = savedEnv;

      try {
        assert.strictEqual(
          urlOrigin,
          'http://localhost:3000',
          `[${label}] SECURITY: without PUBLIC_BASE_URL, download URL must fall back to http://localhost:3000. Got: ${url}`
        );
        console.log(`PASS [${label}] Test 3 — localhost:3000 fallback when PUBLIC_BASE_URL is unset`);
        passed++;
      } catch (err) {
        console.error(`FAIL [${label}] Test 3 — localhost fallback not used: ${err.message}`);
        failed++;
      }
    }
  }

  console.log(`\n==================================================`);
  console.log(`SEC-003 HOST POISONING TEST RESULTS: ${passed} PASSED | ${failed} FAILED`);
  console.log(`==================================================`);

  // Restore original module loader
  Module._load = originalLoad;

  if (failed > 0) process.exit(1);
}

runTests().catch(err => { console.error('Unexpected error:', err); process.exit(1); });
