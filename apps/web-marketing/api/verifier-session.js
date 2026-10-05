'use strict';

/**
 * POST /api/verifier-session
 *
 * Validates a preview-access credential and issues a short-lived HttpOnly
 * session cookie granting access to the VaultBasis Web Verifier.
 *
 * Request body (JSON): { token: string, accessId: string }
 *
 * Trust boundary:
 *   preview-access credential → authenticated session → Web Verifier UI
 *   SEC-002 entitlement        → exact qualified artifact → Edge download
 *
 *   These are separate. A preview-access credential cannot authorize a
 *   download; a SEC-002 entitlement is not reused here.
 *
 * Security properties:
 *   - Preview-access credential must be ACTIVE, unexpired, and ID-bound
 *   - Rate limited: max RATE_LIMIT_MAX attempts per IP per RATE_LIMIT_WINDOW_MS
 *   - Session token is cryptographically random (32 bytes)
 *   - Session token stored hashed (SHA-256) in private Blob under sessions/
 *   - Cookie: HttpOnly, Secure, SameSite=Strict, Max-Age=4h
 *   - Raw bearer token never appears in logs, storage paths, or responses
 *   - Generic error responses — no reason codes on the wire
 *   - Fail-closed: storage errors → 503, never permit
 *
 * Rate limiting:
 *   - Key: SHA-256(derived IP) — IP never stored raw
 *   - Window: 15 minutes; Limit: 10 attempts per window per IP
 *   - Stored as rate-limit/<hash>.json in private Blob
 *   - Limit exceeded → 429 with Retry-After header
 *   - NOT a strict distributed rate-limit guarantee: @vercel/blob provides no
 *     atomic compare-and-swap, so concurrent requests may both read the same
 *     counter and both increment. This is best-effort abuse throttling.
 *     The primary brute-force defense is the high-entropy 32-byte credential.
 */

const crypto = require('crypto');
const { put, get } = require('@vercel/blob');
const { isWellFormedToken, validatePreviewAccess, previewAccessPathname } = require('./preview-access-store');

const SESSION_COOKIE_NAME = 'vb_session';
const SESSION_TTL_MS = 4 * 60 * 60 * 1000;
const SESSION_MAX_AGE_S = 4 * 60 * 60;
const SESSION_NAMESPACE = 'sessions/';
const SESSION_BYTE_LENGTH = 32;

const RATE_LIMIT_NAMESPACE = 'rate-limit/';
const RATE_LIMIT_WINDOW_MS = 15 * 60 * 1000; // 15 minutes
const RATE_LIMIT_MAX = 10;

function sessionPathname(rawSessionToken) {
  const digest = crypto.createHash('sha256').update(rawSessionToken, 'utf8').digest('hex');
  return `${SESSION_NAMESPACE}${digest}.json`;
}

function generateSessionToken() {
  return crypto.randomBytes(SESSION_BYTE_LENGTH).toString('hex');
}

function deny(res) {
  return res.status(401).json({ error: 'Access denied.' });
}

function getClientIp(req) {
  // The rightmost X-Forwarded-For entry is used as the IP signal. This is
  // advisory input for best-effort abuse throttling only and MUST NOT
  // participate in authentication, authorization, session validity, entitlement
  // validity, or artifact authorization. An imperfect IP signal is acceptable
  // because the high-entropy 32-byte credential is the primary brute-force defense.
  const forwarded = req.headers['x-forwarded-for'];
  if (forwarded) {
    const parts = forwarded.split(',');
    return parts[parts.length - 1].trim();
  }
  return req.socket?.remoteAddress || 'unknown';
}

function rateLimitPathname(ip) {
  const digest = crypto.createHash('sha256').update(ip, 'utf8').digest('hex');
  return `${RATE_LIMIT_NAMESPACE}${digest}.json`;
}

/**
 * Check and increment the rate-limit counter for this IP.
 * Returns { allowed: true } or { allowed: false }.
 * Fail-open: if Blob storage is unavailable, allow (don't block legitimate
 * users due to storage faults — the credential check still applies).
 */
async function checkRateLimit(ip) {
  const pathname = rateLimitPathname(ip);
  const now = Date.now();

  let record = { windowStart: now, count: 0 };
  try {
    const result = await get(pathname, { access: 'private' });
    if (result) {
      const chunks = [];
      const reader = result.stream.getReader();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
      }
      const existing = JSON.parse(Buffer.concat(chunks.map(c => Buffer.from(c))).toString('utf8'));
      if (now - existing.windowStart < RATE_LIMIT_WINDOW_MS) {
        record = existing;
      }
    }
  } catch (e) {
    if (e && e.name !== 'BlobNotFoundError') {
      console.error('[verifier-session] rate-limit read error:', e.message);
    }
    // Fail-open on storage error — credential validation still applies
    return { allowed: true };
  }

  record.count += 1;

  // Write back (fire and forget — don't block the response on this)
  put(pathname, JSON.stringify(record), {
    access: 'private',
    contentType: 'application/json',
    addRandomSuffix: false,
    allowOverwrite: true,
  }).catch((e) => console.error('[verifier-session] rate-limit write error:', e.message));

  if (record.count > RATE_LIMIT_MAX) {
    return { allowed: false };
  }
  return { allowed: true };
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed.' });
  }

  const ip = getClientIp(req);

  // Rate limit check — before any credential processing.
  const rl = await checkRateLimit(ip);
  if (!rl.allowed) {
    res.setHeader('Retry-After', String(Math.ceil(RATE_LIMIT_WINDOW_MS / 1000)));
    return res.status(429).json({ error: 'Too many attempts. Please try again later.' });
  }

  let body;
  try {
    body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
  } catch {
    return deny(res);
  }

  const { token, accessId } = body || {};

  // Format gate before any Blob lookup.
  if (!token || !accessId || !isWellFormedToken(token)) {
    return deny(res);
  }

  // Validate preview-access credential — separate from SEC-002 entitlements.
  const authResult = await validatePreviewAccess(token, accessId);
  if (!authResult.ok) {
    return deny(res);
  }

  // Issue a session token.
  const sessionToken = generateSessionToken();
  const now = Date.now();
  const sessionRecord = {
    accessId: authResult.record.accessId,
    email: authResult.record.email,
    // previewAccessBlobPathname is the SHA-256-keyed Blob path of the preview-access
    // record that authorized this session. verifier-page.js and verifier-session-check.js
    // load this on every protected request to verify the underlying access is still
    // ACTIVE — ensuring revocation of the preview-access propagates to existing sessions.
    previewAccessBlobPathname: previewAccessPathname(token),
    createdAt: new Date(now).toISOString(),
    expiresAt: new Date(now + SESSION_TTL_MS).toISOString(),
    status: 'ACTIVE',
  };

  try {
    await put(sessionPathname(sessionToken), JSON.stringify(sessionRecord), {
      access: 'private',
      contentType: 'application/json',
      addRandomSuffix: false,
      allowOverwrite: false,
    });
  } catch (e) {
    console.error('[verifier-session] session store error:', e.message);
    return res.status(503).json({ error: 'Session could not be created. Please try again.' });
  }

  res.setHeader(
    'Set-Cookie',
    `${SESSION_COOKIE_NAME}=${sessionToken}; HttpOnly; Secure; SameSite=Strict; Max-Age=${SESSION_MAX_AGE_S}; Path=/`
  );
  return res.status(200).json({ ok: true });
};
