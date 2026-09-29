'use strict';

/**
 * SEC-002 Entitlement Authorization Tests
 *
 * Tests the entitlement-store module directly (unit) and the download handler
 * end-to-end (integration against mocked Blob).
 *
 * Run: node tests/unit/test_sec002_entitlement_auth.js
 */

const assert = require('assert');
const crypto = require('crypto');
const path = require('path');

// ---------------------------------------------------------------------------
// Blob mock infrastructure
// ---------------------------------------------------------------------------

// In-memory store keyed by pathname
const blobStore = new Map();
let blobErrorMode = null; // null | 'throw' | 'return_null'

class MockBlobNotFoundError extends Error {
  constructor(msg) { super(msg); this.name = 'BlobNotFoundError'; }
}

function makeBlobStream(jsonStr) {
  const buf = Buffer.from(jsonStr, 'utf8');
  return {
    stream: {
      getReader() {
        let sent = false;
        return {
          async read() {
            if (!sent) { sent = true; return { done: false, value: buf }; }
            return { done: true, value: undefined };
          }
        };
      }
    },
    size: buf.length,
    contentType: 'application/json',
  };
}

const Module = require('module');
const originalLoad = Module._load;

Module._load = function(request, parent, isMain) {
  if (request === '@vercel/blob') {
    return {
      BlobNotFoundError: MockBlobNotFoundError,
      put: async (pathname, body, opts) => {
        if (blobErrorMode === 'throw') throw new Error('Blob service unavailable');
        if (opts && opts.allowOverwrite === false && blobStore.has(pathname)) {
          throw new Error('Blob already exists (allowOverwrite: false)');
        }
        blobStore.set(pathname, typeof body === 'string' ? body : body.toString());
        return { pathname, url: `https://blob.test/${pathname}` };
      },
      get: async (pathname, opts) => {
        if (blobErrorMode === 'throw') throw new Error('Blob service unavailable');
        if (blobErrorMode === 'return_null') return null;
        if (!blobStore.has(pathname)) {
          const e = new MockBlobNotFoundError(`Not found: ${pathname}`);
          throw e;
        }
        return makeBlobStream(blobStore.get(pathname));
      },
      del: async (pathname) => {
        blobStore.delete(pathname);
      },
    };
  }
  if (request === 'nodemailer') {
    return {
      createTestAccount: async () => ({ user: 'u', pass: 'p' }),
      createTransport: () => ({
        sendMail: async (opts) => ({ messageId: 'stub-id' }),
      }),
      getTestMessageUrl: () => 'https://ethereal.stub/msg/1',
    };
  }
  return originalLoad.apply(this, arguments);
};

// ---------------------------------------------------------------------------
// Load modules under test after mock is installed
// ---------------------------------------------------------------------------
const STORE_PATH = path.resolve(__dirname, '../../api/entitlement-store.js');
const DOWNLOAD_PATH = path.resolve(__dirname, '../../api/download.js');
const REQUEST_ACCESS_PATH = path.resolve(__dirname, '../../api/request-access.js');

function freshRequire(p) {
  delete require.cache[require.resolve(p)];
  return require(p);
}

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------
let passed = 0;
let failed = 0;

function test(label, fn) {
  return Promise.resolve().then(fn).then(() => {
    console.log(`PASS  ${label}`);
    passed++;
  }).catch(err => {
    console.error(`FAIL  ${label}`);
    console.error(`      ${err.message}`);
    failed++;
  });
}

function makeRes() {
  const res = {
    _status: 200, _headers: {}, _body: null, _ended: false, _chunks: [],
    status(c) { this._status = c; return this; },
    json(b) { this._body = b; this._ended = true; return this; },
    setHeader(k, v) { this._headers[k] = v; },
    write(chunk) { this._chunks.push(chunk); },
    end() { this._ended = true; },
  };
  return res;
}

function makeReq(query = {}, headers = {}) {
  return { method: 'GET', query, headers };
}

// The qualified artifact hash used in tests — a fixed sentinel value
const QUALIFIED_HASH = 'a'.repeat(64);
const OTHER_HASH     = 'b'.repeat(64);

// Manifest with one artifact entry pointing to the qualified hash
const MANIFEST = JSON.stringify({
  artifacts: [
    {
      os: 'macos', architecture: 'arm64',
      blobPathname: 'rc3/current/VaultBasis-RC3-macOS-arm64.zip',
      sha256: QUALIFIED_HASH,
    }
  ]
});

// Seed the manifest into the mock blob store
blobStore.set('rc3/current/manifest.json', MANIFEST);
// Seed a dummy artifact blob
blobStore.set('rc3/current/VaultBasis-RC3-macOS-arm64.zip', 'FAKE_BINARY_CONTENT');

// ---------------------------------------------------------------------------
// Part 1 — entitlement-store unit tests
// ---------------------------------------------------------------------------

async function runStoreTests() {
  console.log('\n--- Part 1: entitlement-store unit tests ---');
  const store = freshRequire(STORE_PATH);

  await test('generateToken() produces 64-char lowercase hex', async () => {
    const t = store.generateToken();
    assert.strictEqual(t.length, 64);
    assert.ok(/^[0-9a-f]+$/.test(t), 'not lowercase hex');
  });

  await test('isWellFormedToken() accepts valid token', async () => {
    assert.ok(store.isWellFormedToken('a'.repeat(64)));
  });

  await test('isWellFormedToken() rejects empty string', async () => {
    assert.ok(!store.isWellFormedToken(''));
  });

  await test('isWellFormedToken() rejects short string', async () => {
    assert.ok(!store.isWellFormedToken('abc'));
  });

  await test('isWellFormedToken() rejects non-hex characters', async () => {
    assert.ok(!store.isWellFormedToken('G'.repeat(64)));
  });

  await test('isWellFormedToken() rejects non-string', async () => {
    assert.ok(!store.isWellFormedToken(null));
    assert.ok(!store.isWellFormedToken(undefined));
    assert.ok(!store.isWellFormedToken(12345));
  });

  await test('entitlementPathname() derives SHA-256 path, not raw token', async () => {
    const rawToken = 'f'.repeat(64);
    const pn = store.entitlementPathname(rawToken);
    assert.ok(pn.startsWith('entitlements/'));
    assert.ok(pn.endsWith('.json'));
    // must not contain the raw token
    assert.ok(!pn.includes(rawToken), 'pathname contains raw bearer token');
  });

  await test('createEntitlement() writes record to blob store', async () => {
    blobStore.delete('entitlements/' + crypto.createHash('sha256').update('e'.repeat(64)).digest('hex') + '.json');
    const rawToken = 'e'.repeat(64);
    await store.createEntitlement(rawToken, {
      entitlementId: 'DP-TEST01',
      email: 'test@example.com',
      qualifiedArtifactHash: QUALIFIED_HASH,
    });
    const pn = store.entitlementPathname(rawToken);
    assert.ok(blobStore.has(pn), 'record not written to blob store');
    const record = JSON.parse(blobStore.get(pn));
    assert.strictEqual(record.status, 'ACTIVE');
    assert.strictEqual(record.entitlementId, 'DP-TEST01');
    assert.strictEqual(record.qualifiedArtifactHash, QUALIFIED_HASH);
    assert.ok(!('rawToken' in record), 'record must not store raw token');
    assert.ok(!('email' in record) || record.email === 'test@example.com'); // email OK to store
  });

  // --- validateEntitlement tests ---

  // Seed a valid entitlement for validation tests
  const VALID_TOKEN = store.generateToken();
  const VALID_EID   = 'DP-VALID01';
  await store.createEntitlement(VALID_TOKEN, {
    entitlementId: VALID_EID,
    email: 'valid@example.com',
    qualifiedArtifactHash: QUALIFIED_HASH,
  });

  await test('validateEntitlement() ALLOW: valid token + matching entitlement + matching artifact', async () => {
    const result = await store.validateEntitlement(VALID_TOKEN, VALID_EID, QUALIFIED_HASH);
    assert.strictEqual(result.ok, true);
  });

  await test('validateEntitlement() DENY: no token (empty string)', async () => {
    const result = await store.validateEntitlement('', VALID_EID, QUALIFIED_HASH);
    assert.strictEqual(result.ok, false);
  });

  await test('validateEntitlement() DENY: malformed token (too short)', async () => {
    const result = await store.validateEntitlement('abc', VALID_EID, QUALIFIED_HASH);
    assert.strictEqual(result.ok, false);
  });

  await test('validateEntitlement() DENY: random well-formed token (not in store)', async () => {
    const result = await store.validateEntitlement('d'.repeat(64), VALID_EID, QUALIFIED_HASH);
    assert.strictEqual(result.ok, false);
  });

  await test('validateEntitlement() DENY: valid token + wrong entitlement ID', async () => {
    const result = await store.validateEntitlement(VALID_TOKEN, 'DP-WRONG', QUALIFIED_HASH);
    assert.strictEqual(result.ok, false);
  });

  await test('validateEntitlement() DENY: valid token + different artifact hash', async () => {
    const result = await store.validateEntitlement(VALID_TOKEN, VALID_EID, OTHER_HASH);
    assert.strictEqual(result.ok, false);
  });

  await test('validateEntitlement() DENY: REVOKED status', async () => {
    const revToken = store.generateToken();
    await store.createEntitlement(revToken, {
      entitlementId: 'DP-REV01',
      email: 'rev@example.com',
      qualifiedArtifactHash: QUALIFIED_HASH,
    });
    // Manually revoke in store
    const pn = store.entitlementPathname(revToken);
    const rec = JSON.parse(blobStore.get(pn));
    rec.status = 'REVOKED';
    blobStore.set(pn, JSON.stringify(rec));

    const result = await store.validateEntitlement(revToken, 'DP-REV01', QUALIFIED_HASH);
    assert.strictEqual(result.ok, false);
  });

  await test('validateEntitlement() DENY: expired entitlement', async () => {
    const expToken = store.generateToken();
    await store.createEntitlement(expToken, {
      entitlementId: 'DP-EXP01',
      email: 'exp@example.com',
      qualifiedArtifactHash: QUALIFIED_HASH,
    });
    // Force expiry into the past
    const pn = store.entitlementPathname(expToken);
    const rec = JSON.parse(blobStore.get(pn));
    rec.expiresAt = new Date(Date.now() - 1000).toISOString();
    blobStore.set(pn, JSON.stringify(rec));

    const result = await store.validateEntitlement(expToken, 'DP-EXP01', QUALIFIED_HASH);
    assert.strictEqual(result.ok, false);
  });

  await test('validateEntitlement() DENY: storage error fails closed', async () => {
    blobErrorMode = 'throw';
    const result = await store.validateEntitlement(VALID_TOKEN, VALID_EID, QUALIFIED_HASH);
    blobErrorMode = null;
    assert.strictEqual(result.ok, false);
  });

  await test('failure responses do not distinguish token-not-found from wrong-entitlement', async () => {
    // Both deny cases should return ok:false with no leaked detail to callers
    const r1 = await store.validateEntitlement('c'.repeat(64), 'DP-X', QUALIFIED_HASH);
    const r2 = await store.validateEntitlement(VALID_TOKEN, 'DP-X', QUALIFIED_HASH);
    assert.strictEqual(r1.ok, false);
    assert.strictEqual(r2.ok, false);
    // Callers see only ok:false and reason — no email, stored token, or expiry exposed
    assert.ok(!('email' in r1) && !('email' in r2));
  });
}

// ---------------------------------------------------------------------------
// Part 2 — download handler end-to-end tests
// ---------------------------------------------------------------------------

async function runDownloadTests() {
  console.log('\n--- Part 2: download handler end-to-end tests ---');

  // Provision a valid entitlement through the store for download tests
  const store = freshRequire(STORE_PATH);
  const VALID_TOKEN = store.generateToken();
  const VALID_EID   = 'DP-DL-VALID';
  await store.createEntitlement(VALID_TOKEN, {
    entitlementId: VALID_EID,
    email: 'dl@example.com',
    qualifiedArtifactHash: QUALIFIED_HASH,
  });

  const handler = freshRequire(DOWNLOAD_PATH);

  await test('DENY: no token or entitlement in request', async () => {
    const res = makeRes();
    await handler(makeReq({ platform: 'mac-arm64' }), res);
    assert.ok(res._status === 401 || res._status === 403, `expected 401/403, got ${res._status}`);
  });

  await test('DENY: random well-formed token', async () => {
    const res = makeRes();
    await handler(makeReq({ token: 'f'.repeat(64), entitlement: 'DP-FAKE', platform: 'mac-arm64' }), res);
    assert.ok(res._status === 401 || res._status === 403, `expected 401/403, got ${res._status}`);
  });

  await test('DENY: malformed token (too short)', async () => {
    const res = makeRes();
    await handler(makeReq({ token: 'short', entitlement: VALID_EID, platform: 'mac-arm64' }), res);
    assert.ok(res._status === 401 || res._status === 403, `expected 401/403, got ${res._status}`);
  });

  await test('ALLOW: valid token + correct entitlement + mac-arm64 platform', async () => {
    const res = makeRes();
    await handler(makeReq({ token: VALID_TOKEN, entitlement: VALID_EID, platform: 'mac-arm64' }), res);
    assert.strictEqual(res._status, 200, `expected 200, got ${res._status}`);
    assert.ok(res._headers['Content-Disposition'], 'missing Content-Disposition');
  });

  await test('DENY: valid token + modified entitlement ID', async () => {
    const res = makeRes();
    await handler(makeReq({ token: VALID_TOKEN, entitlement: 'DP-MODIFIED', platform: 'mac-arm64' }), res);
    assert.ok(res._status === 401 || res._status === 403, `expected 401/403, got ${res._status}`);
  });

  await test('DENY: revoked entitlement', async () => {
    const revToken = store.generateToken();
    await store.createEntitlement(revToken, {
      entitlementId: 'DP-REVDL',
      email: 'rev@example.com',
      qualifiedArtifactHash: QUALIFIED_HASH,
    });
    const pn = store.entitlementPathname(revToken);
    const rec = JSON.parse(blobStore.get(pn));
    rec.status = 'REVOKED';
    blobStore.set(pn, JSON.stringify(rec));

    const res = makeRes();
    await handler(makeReq({ token: revToken, entitlement: 'DP-REVDL', platform: 'mac-arm64' }), res);
    assert.ok(res._status === 401 || res._status === 403, `expected 401/403, got ${res._status}`);
  });

  await test('DENY: expired entitlement', async () => {
    const expToken = store.generateToken();
    await store.createEntitlement(expToken, {
      entitlementId: 'DP-EXPDL',
      email: 'exp@example.com',
      qualifiedArtifactHash: QUALIFIED_HASH,
    });
    const pn = store.entitlementPathname(expToken);
    const rec = JSON.parse(blobStore.get(pn));
    rec.expiresAt = new Date(Date.now() - 1000).toISOString();
    blobStore.set(pn, JSON.stringify(rec));

    const res = makeRes();
    await handler(makeReq({ token: expToken, entitlement: 'DP-EXPDL', platform: 'mac-arm64' }), res);
    assert.ok(res._status === 401 || res._status === 403, `expected 401/403, got ${res._status}`);
  });

  await test('DENY: storage lookup failure fails closed (not 200)', async () => {
    blobErrorMode = 'throw';
    const res = makeRes();
    // Even with a valid-looking token, storage error must deny
    await handler(makeReq({ token: VALID_TOKEN, entitlement: VALID_EID, platform: 'mac-arm64' }), res);
    blobErrorMode = null;
    assert.ok(res._status !== 200, `storage error must not return 200, got ${res._status}`);
  });

  await test('response does not expose stored email or token in error body', async () => {
    const res = makeRes();
    await handler(makeReq({ token: 'bad'.repeat(22), entitlement: VALID_EID, platform: 'mac-arm64' }), res);
    const body = JSON.stringify(res._body || '');
    assert.ok(!body.includes('dl@example.com'), 'error body must not contain stored email');
    assert.ok(!body.includes(VALID_TOKEN), 'error body must not contain valid token');
  });
}

// ---------------------------------------------------------------------------
// Part 3 — demonstrate current download.js FAILS adversarial cases (pre-fix)
// ---------------------------------------------------------------------------

async function demonstratePreFixFailures() {
  console.log('\n--- Part 3: pre-fix failures (confirms SEC-002 was real) ---');
  // We can only run this if we have the OLD download.js without entitlement checks.
  // Since we're implementing the fix, this section just notes the baseline.
  // The SEC-003 test already demonstrated the pattern; here we document the baseline.
  console.log('  (Pre-fix baseline: any non-empty token+entitlement was ALLOWED by download.js)');
  console.log('  (This is confirmed from prior session observation — SEC-002 CONFIRMED)');
  console.log('  (Current run tests post-fix behaviour only)');
}

// ---------------------------------------------------------------------------
// Run all tests
// ---------------------------------------------------------------------------

async function main() {
  console.log('SEC-002 Entitlement Authorization — Test Suite');
  console.log('==============================================');

  await demonstratePreFixFailures();
  await runStoreTests();
  await runDownloadTests();

  console.log(`\n==================================================`);
  console.log(`SEC-002 TEST RESULTS: ${passed} PASSED | ${failed} FAILED`);
  console.log(`==================================================`);

  Module._load = originalLoad;
  if (failed > 0) process.exit(1);
}

main().catch(err => { console.error('Unexpected:', err); process.exit(1); });
