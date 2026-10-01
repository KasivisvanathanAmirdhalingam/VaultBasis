'use strict';

/**
 * GET /api/verifier-session-check
 *
 * Server-side session validation for the Web Verifier (defense-in-depth layer).
 * Called by the verifier page JS on load. The authoritative gate is
 * api/verifier-page.js which validates before serving any content.
 *
 * Validation steps (matches verifier-page.js):
 *   1. Read vb_session cookie
 *   2. Load session record from private Blob (hash-keyed)
 *   3. Verify session ACTIVE and unexpired
 *   4. Load underlying preview-access record (stored pathname in session)
 *   5. Verify preview-access still ACTIVE and unexpired
 *      — propagates revocation to existing sessions
 *
 * Returns 200 { ok: true } if fully valid.
 * Returns 401 { error: 'Session invalid or expired.' } otherwise.
 * Returns 503 on storage errors (fail-closed).
 */

const crypto = require('crypto');
const { get } = require('@vercel/blob');

const SESSION_COOKIE_NAME = 'vb_session';
const SESSION_NAMESPACE = 'sessions/';
const PREVIEW_ACCESS_NAMESPACE = 'preview-access/';

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

async function readBlobJson(pathname) {
  const result = await get(pathname, { access: 'private', useCache: false });
  if (!result) return null;
  const chunks = [];
  const reader = result.stream.getReader();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
  }
  return JSON.parse(Buffer.concat(chunks.map(c => Buffer.from(c))).toString('utf8'));
}

module.exports = async (req, res) => {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed.' });
  }

  const cookies = parseCookies(req.headers.cookie);
  const sessionToken = cookies[SESSION_COOKIE_NAME];

  if (!sessionToken || !isWellFormedSessionToken(sessionToken)) {
    return res.status(401).json({ error: 'Session invalid or expired.' });
  }

  // Step 1: load and validate session record.
  let record;
  try {
    record = await readBlobJson(sessionPathname(sessionToken));
    if (!record) {
      return res.status(401).json({ error: 'Session invalid or expired.' });
    }
  } catch (e) {
    if (e && e.name === 'BlobNotFoundError') {
      return res.status(401).json({ error: 'Session invalid or expired.' });
    }
    console.error('[verifier-session-check] session lookup error:', e.message);
    return res.status(503).json({ error: 'Session check could not be completed.' });
  }

  if (record.status !== 'ACTIVE') {
    return res.status(401).json({ error: 'Session invalid or expired.' });
  }

  if (Date.now() > new Date(record.expiresAt).getTime()) {
    return res.status(401).json({ error: 'Session invalid or expired.' });
  }

  // Step 2: revocation propagation — verify the underlying preview-access
  // credential is still ACTIVE. This ensures revoking a preview-access
  // immediately denies any session it authorized.
  if (!record.previewAccessBlobPathname ||
      !record.previewAccessBlobPathname.startsWith(PREVIEW_ACCESS_NAMESPACE)) {
    return res.status(401).json({ error: 'Session invalid or expired.' });
  }

  try {
    const paRecord = await readBlobJson(record.previewAccessBlobPathname);
    if (!paRecord) {
      return res.status(401).json({ error: 'Session invalid or expired.' });
    }
    if (paRecord.status !== 'ACTIVE') {
      return res.status(401).json({ error: 'Session invalid or expired.' });
    }
    if (Date.now() > new Date(paRecord.expiresAt).getTime()) {
      return res.status(401).json({ error: 'Session invalid or expired.' });
    }
  } catch (e) {
    if (e && e.name === 'BlobNotFoundError') {
      return res.status(401).json({ error: 'Session invalid or expired.' });
    }
    console.error('[verifier-session-check] preview-access lookup error:', e.message);
    return res.status(503).json({ error: 'Session check could not be completed.' });
  }

  return res.status(200).json({ ok: true });
};
