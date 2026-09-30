'use strict';

/**
 * POST /api/verifier-session
 *
 * Validates a design-partner entitlement token and issues a short-lived
 * HttpOnly session cookie granting access to the VaultBasis Web Verifier.
 *
 * Request body (JSON): { token: string, entitlementId: string }
 *
 * The session cookie value is a fresh 64-hex-char random token stored
 * server-side in the Blob-backed session namespace. The supplied entitlement
 * token is validated using the existing SEC-002 entitlement store before any
 * session is created.
 *
 * Security properties:
 *   - Entitlement must be ACTIVE, unexpired, and correctly bound
 *   - Session token is cryptographically random (32 bytes)
 *   - Session token is stored hashed (SHA-256) in private Blob storage
 *   - Cookie: HttpOnly, Secure, SameSite=Strict, Max-Age=4h
 *   - Raw bearer token never appears in logs, storage paths, or responses
 *   - Generic error responses — no information disclosure on failure reason
 *   - Rate limiting: enforced via Vercel Edge (see middleware) + fail-closed
 */

const crypto = require('crypto');
const { put, get } = require('@vercel/blob');
const { isWellFormedToken } = require('./entitlement-store');

const SESSION_COOKIE_NAME = 'vb_session';
const SESSION_TTL_MS = 4 * 60 * 60 * 1000; // 4 hours
const SESSION_MAX_AGE_S = 4 * 60 * 60;      // seconds for Max-Age
const SESSION_NAMESPACE = 'sessions/';
const SESSION_BYTE_LENGTH = 32;

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

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed.' });
  }

  let body;
  try {
    body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
  } catch {
    return deny(res);
  }

  const { token, entitlementId } = body || {};

  // Format gate before any Blob lookup.
  if (!token || !entitlementId || !isWellFormedToken(token)) {
    return deny(res);
  }

  // Validate the entitlement — reuse existing SEC-002 store but without
  // artifact binding (verifier access does not require a specific artifact).
  // We perform a direct entitlement lookup without artifact-hash check.
  const { validateEntitlementForVerifier } = require('./entitlement-store');
  const authResult = await validateEntitlementForVerifier(token, entitlementId);
  if (!authResult.ok) {
    return deny(res);
  }

  // Issue a session token.
  const sessionToken = generateSessionToken();
  const now = Date.now();
  const sessionRecord = {
    entitlementId: authResult.record.entitlementId,
    email: authResult.record.email,
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

  // Set session cookie — HttpOnly, Secure, SameSite=Strict.
  res.setHeader(
    'Set-Cookie',
    `${SESSION_COOKIE_NAME}=${sessionToken}; HttpOnly; Secure; SameSite=Strict; Max-Age=${SESSION_MAX_AGE_S}; Path=/`
  );
  return res.status(200).json({ ok: true });
};
