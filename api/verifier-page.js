'use strict';

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
 *   2. Validate session cryptographically against private Blob storage
 *      (same logic as verifier-session-check.js)
 *   3a. Valid session → read verifier HTML from Blob, stream to client
 *   3b. Invalid/missing session → 302 redirect to /verifier-access
 *
 * The verifier HTML is stored in private Blob at verifier-app/index.html
 * so it is not accessible as a public static file.
 *
 * The build pipeline (build_public_web.js) uploads the verifier HTML to
 * private Blob at deploy time — it is NOT placed in outputDirectory.
 *
 * Security properties:
 *   - Server-side session validation is authoritative (not defense-in-depth)
 *   - Unauthenticated requests never receive verifier application code
 *   - Session must be ACTIVE and unexpired (server-side clock)
 *   - Fail-closed: storage error → 503, never serve verifier
 */

const crypto = require('crypto');
const { get } = require('@vercel/blob');
const fs = require('fs');
const path = require('path');

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
  const result = await get(pathname, { access: 'private' });
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

  // Session is valid — serve the verifier application.
  // Try private Blob first; fall back to local filesystem for dev/build environments.
  let verifierHtml;
  try {
    verifierHtml = await readBlobText(VERIFIER_HTML_BLOB_PATHNAME);
  } catch (e) {
    if (e && e.name !== 'BlobNotFoundError') {
      console.error('[verifier-page] verifier HTML blob read error:', e.message);
    }
    verifierHtml = null;
  }

  if (!verifierHtml) {
    // Fallback: serve from local filesystem (dev environment / first deploy before upload).
    try {
      verifierHtml = fs.readFileSync(VERIFIER_HTML_LOCAL_PATH, 'utf8');
    } catch (e) {
      console.error('[verifier-page] verifier HTML local read error:', e.message);
      return res.status(503).send('Verifier application is temporarily unavailable.');
    }
  }

  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  return res.status(200).send(verifierHtml);
};
