'use strict';

/**
 * ACCESS-INV-001 — Removable Preview Access Boundary
 *
 * This file is the access-policy boundary for the Web Verifier. It is
 * deliberately isolated from the verifier's verification semantics.
 *
 * The preview access requirement is a distribution/access policy, not a
 * VaultBasis product semantic. This implementation MUST NOT be modified to
 * embed authentication into:
 *   - receipt parsing, canonicalization, or signing
 *   - deterministic reconciliation or outcome computation
 *   - receipt schema or verification logic
 *   - Edge packaging or runtime
 *   - SEC-002 artifact integrity/binding semantics
 *
 * Required future access-mode transitions must be achievable by changing
 * routing/policy at this boundary only:
 *   VERIFIER_CONTROLLED + EDGE_CONTROLLED  (current)
 *   VERIFIER_PUBLIC     + EDGE_CONTROLLED  (post-CPA-validation target)
 *   VERIFIER_PUBLIC     + EDGE_COMMERCIAL  (future)
 *
 * Web Verifier access policy and Edge download authorization are independently
 * configurable. Removing verifier access control must not affect Edge download
 * authorization, and vice versa.
 *
 * Do not implement future public/commercial modes now. Preserve this seam.
 */

/**
 * GET /api/verifier-page
 *
 * Server-authoritative gateway for the Web Verifier application.
 *
 * This function validates the session cookie BEFORE returning the verifier
 * HTML. An unauthenticated or invalid session never receives the verifier
 * application — not even a static file to redirect from.
 *
 * Request flow:
 *   1. Read vb_session cookie from request headers
 *   2. Load session record from private Blob (hash-keyed)
 *   3. Verify session is ACTIVE and unexpired
 *   4. Load the underlying preview-access record (stored pathname in session)
 *   5. Verify preview-access is still ACTIVE and unexpired
 *      — this propagates revocation: revoking the preview-access credential
 *        immediately invalidates all sessions it authorized, regardless of
 *        the session's own 4-hour TTL.
 *   6a. Both valid → serve verifier HTML
 *   6b. Any check fails → 302 redirect to /verifier-access
 *
 * The verifier HTML is stored in private Blob at verifier-app/index.html
 * so it is not accessible as a public static file.
 *
 * Security properties:
 *   - Server-side validation is authoritative (not defense-in-depth)
 *   - Unauthenticated requests never receive verifier application code
 *   - Revocation propagates: preview-access REVOKED → session denied immediately
 *   - Fail-closed: storage error → 503, never serve verifier
 */

const crypto = require('crypto');
const { get } = require('@vercel/blob');
const fs = require('fs');
const path = require('path');

const PREVIEW_ACCESS_NAMESPACE = 'preview-access/';

const SESSION_COOKIE_NAME = 'vb_session';
const SESSION_NAMESPACE = 'sessions/';

// Path in private Blob where the verifier HTML is stored.
const VERIFIER_HTML_BLOB_PATHNAME = 'verifier-app/index.html';

// Fallback: path to verifier HTML relative to repo root (for local dev / Vercel build).
// In production the Blob copy is used; this fallback allows local testing.
const VERIFIER_HTML_LOCAL_PATH = path.join(__dirname, '..', 'apps', 'web-verifier', 'index.html');

function parseCookies(cookieHeader) {
  const cookies = {};
  if (!cookieHeader) return cookies;
  cookieHeader.split(';').forEach((part) => {
    const [name, ...rest] = part.trim().split('=');
    cookies[name.trim()] = rest.join('=').trim();
  });
  return cookies;
}

function sessionPathname(rawSessionToken) {
  const digest = crypto.createHash('sha256').update(rawSessionToken, 'utf8').digest('hex');
  return `${SESSION_NAMESPACE}${digest}.json`;
}

function isWellFormedSessionToken(token) {
  return (
    typeof token === 'string' &&
    token.length === 64 &&
    /^[0-9a-f]+$/.test(token)
  );
}

async function readBlobText(pathname) {
  const result = await get(pathname, { access: 'private', useCache: false });
  if (!result) return null;
  const chunks = [];
  const reader = result.stream.getReader();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
  }
  return Buffer.concat(chunks.map(c => Buffer.from(c))).toString('utf8');
}

module.exports = async (req, res) => {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed.' });
  }

  const cookies = parseCookies(req.headers.cookie);
  const sessionToken = cookies[SESSION_COOKIE_NAME];

  if (!sessionToken || !isWellFormedSessionToken(sessionToken)) {
    return res.redirect(302, '/verifier-access?next=/verifier');
  }

  // Cryptographic session validation against Blob storage.
  let record;
  try {
    const pathname = sessionPathname(sessionToken);
    const raw = await readBlobText(pathname);
    if (!raw) {
      return res.redirect(302, '/verifier-access?next=/verifier');
    }
    record = JSON.parse(raw);
  } catch (e) {
    if (e && e.name === 'BlobNotFoundError') {
      return res.redirect(302, '/verifier-access?next=/verifier');
    }
    console.error('[verifier-page] session lookup error:', e.message);
    return res.status(503).send('Service temporarily unavailable. Please try again.');
  }

  if (record.status !== 'ACTIVE') {
    return res.redirect(302, '/verifier-access?next=/verifier');
  }

  if (Date.now() > new Date(record.expiresAt).getTime()) {
    return res.redirect(302, '/verifier-access?next=/verifier');
  }

  // Revocation propagation: load the underlying preview-access record and
  // verify it is still ACTIVE. This ensures that revoking the preview-access
  // credential immediately invalidates all sessions it authorized, rather than
  // allowing up to 4h of continued access after revocation.
  if (!record.previewAccessBlobPathname ||
      !record.previewAccessBlobPathname.startsWith(PREVIEW_ACCESS_NAMESPACE)) {
    // Malformed session record — session predates revocation-check or is corrupt.
    console.error('[verifier-page] session record missing previewAccessBlobPathname');
    return res.redirect(302, '/verifier-access?next=/verifier');
  }

  try {
    const paRaw = await readBlobText(record.previewAccessBlobPathname);
    if (!paRaw) {
      return res.redirect(302, '/verifier-access?next=/verifier');
    }
    const paRecord = JSON.parse(paRaw);
    if (paRecord.status !== 'ACTIVE') {
      return res.redirect(302, '/verifier-access?next=/verifier');
    }
    if (Date.now() > new Date(paRecord.expiresAt).getTime()) {
      return res.redirect(302, '/verifier-access?next=/verifier');
    }
  } catch (e) {
    if (e && e.name === 'BlobNotFoundError') {
      // Preview-access record deleted — treat as revoked.
      return res.redirect(302, '/verifier-access?next=/verifier');
    }
    console.error('[verifier-page] preview-access lookup error:', e.message);
    return res.status(503).send('Service temporarily unavailable. Please try again.');
  }

  // Serve the exact deployed source after authorization; never a mutable
  // shared Blob HTML pointer from another candidate.
  let verifierHtml;
  try { verifierHtml = require('./web-presentation').renderVerifier(); }
  catch (_) { return res.status(503).send('Verifier application is temporarily unavailable.'); }

  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  return res.status(200).send(verifierHtml);
};
