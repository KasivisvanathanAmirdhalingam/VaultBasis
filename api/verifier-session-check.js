'use strict';

/**
 * GET /api/verifier-session-check
 *
 * Server-side session validation for the Web Verifier.
 * Called by the verifier page on load to confirm the session cookie
 * is valid before rendering the verifier UI.
 *
 * Returns 200 { ok: true } if the session is valid and unexpired.
 * Returns 401 { error: 'Session invalid or expired.' } otherwise.
 *
 * The middleware cookie-presence check is a first layer only.
 * This endpoint performs the cryptographic server-side validation.
 */

const crypto = require('crypto');
const { get } = require('@vercel/blob');

const SESSION_COOKIE_NAME = 'vb_session';
const SESSION_NAMESPACE = 'sessions/';

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

module.exports = async (req, res) => {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed.' });
  }

  const cookies = parseCookies(req.headers.cookie);
  const sessionToken = cookies[SESSION_COOKIE_NAME];

  if (!sessionToken || !isWellFormedSessionToken(sessionToken)) {
    return res.status(401).json({ error: 'Session invalid or expired.' });
  }

  let record;
  try {
    const pathname = sessionPathname(sessionToken);
    const result = await get(pathname, { access: 'private' });
    if (!result) {
      return res.status(401).json({ error: 'Session invalid or expired.' });
    }
    const chunks = [];
    const reader = result.stream.getReader();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
    }
    record = JSON.parse(Buffer.concat(chunks.map(c => Buffer.from(c))).toString('utf8'));
  } catch (e) {
    if (e && e.name === 'BlobNotFoundError') {
      return res.status(401).json({ error: 'Session invalid or expired.' });
    }
    console.error('[verifier-session-check] error:', e.message);
    return res.status(503).json({ error: 'Session check could not be completed.' });
  }

  if (record.status !== 'ACTIVE') {
    return res.status(401).json({ error: 'Session invalid or expired.' });
  }

  if (Date.now() > new Date(record.expiresAt).getTime()) {
    return res.status(401).json({ error: 'Session invalid or expired.' });
  }

  return res.status(200).json({ ok: true });
};
