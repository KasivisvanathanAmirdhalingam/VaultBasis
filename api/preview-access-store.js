'use strict';

/**
 * Blob-backed preview-access credential store for Web Verifier authentication.
 *
 * Trust namespace: preview-access/  (distinct from the SEC-002 and sessions/ namespaces)
 *
 * Key derivation: preview-access/sha256(rawToken).json
 *   — bearer token is never used as a Blob pathname
 *
 * Security contract:
 *   - Expiring: credentials have a server-set expiresAt; past-expiry = deny
 *   - Revocable: status REVOKED = deny, regardless of expiry
 *   - NOT artifact-bound: authorizes Web Verifier access only, never downloads
 *   - Fail-closed: any storage error → deny, never allow
 *
 * Trust boundary:
 *   preview-access credential → authenticated session → Web Verifier UI
 *   SEC-002 entitlement        → exact qualified artifact → Edge download
 *
 *   These are deliberately separate. A preview-access credential cannot
 *   authorize a download, and an artifact entitlement is not reused here.
 */

const crypto = require('crypto');
const { put, get } = require('@vercel/blob');

const PREVIEW_ACCESS_SCHEMA_VERSION = '1';
const PREVIEW_ACCESS_TTL_MS = 72 * 60 * 60 * 1000; // 72 hours
const TOKEN_BYTE_LENGTH = 32;
const TOKEN_HEX_LENGTH = TOKEN_BYTE_LENGTH * 2; // 64 hex chars
const PREVIEW_ACCESS_NAMESPACE = 'preview-access/';

function previewAccessPathname(rawToken) {
  const digest = crypto.createHash('sha256').update(rawToken, 'utf8').digest('hex');
  return `${PREVIEW_ACCESS_NAMESPACE}${digest}.json`;
}

function generateToken() {
  return crypto.randomBytes(TOKEN_BYTE_LENGTH).toString('hex');
}

function isWellFormedToken(token) {
  return (
    typeof token === 'string' &&
    token.length === TOKEN_HEX_LENGTH &&
    /^[0-9a-f]+$/.test(token)
  );
}

/**
 * Write a new preview-access record to private Blob storage.
 *
 * @param {string} rawToken
 * @param {object} fields
 * @param {string} fields.accessId  - e.g. "VA-AABBCCDD"
 * @param {string} fields.email
 * @returns {Promise<void>}
 */
async function createPreviewAccess(rawToken, { accessId, email }) {
  const now = Date.now();
  const record = {
    schemaVersion: PREVIEW_ACCESS_SCHEMA_VERSION,
    accessId,
    email,
    createdAt: new Date(now).toISOString(),
    expiresAt: new Date(now + PREVIEW_ACCESS_TTL_MS).toISOString(),
    status: 'ACTIVE',
  };
  const pathname = previewAccessPathname(rawToken);
  await put(pathname, JSON.stringify(record), {
    access: 'private',
    contentType: 'application/json',
    addRandomSuffix: false,
    allowOverwrite: false,
  });
}

/**
 * Validate a preview-access credential.
 *
 * Returns { ok: true, record } on success.
 * Returns { ok: false, reason } on any failure — callers must return generic
 * denial responses (no reason codes on the wire).
 *
 * @param {string} rawToken   - Supplied bearer token
 * @param {string} accessId   - Supplied access ID (from request body)
 */
async function validatePreviewAccess(rawToken, accessId) {
  if (!isWellFormedToken(rawToken)) {
    return { ok: false, reason: 'malformed_token' };
  }

  let record;
  try {
    const pathname = previewAccessPathname(rawToken);
    const result = await get(pathname, { access: 'private', useCache: false });
    if (!result) {
      return { ok: false, reason: 'not_found' };
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
      return { ok: false, reason: 'not_found' };
    }
    console.error('[preview-access-store] lookup error:', e.message);
    return { ok: false, reason: 'storage_error' };
  }

  if (record.status !== 'ACTIVE') {
    return { ok: false, reason: 'not_active' };
  }

  if (Date.now() > new Date(record.expiresAt).getTime()) {
    return { ok: false, reason: 'expired' };
  }

  // Timing-safe compare on accessId
  const storedIdBuf = Buffer.from(record.accessId, 'utf8');
  const suppliedIdBuf = Buffer.from(String(accessId), 'utf8');
  const idMatch =
    storedIdBuf.length === suppliedIdBuf.length &&
    crypto.timingSafeEqual(storedIdBuf, suppliedIdBuf);
  if (!idMatch) {
    return { ok: false, reason: 'access_id_mismatch' };
  }

  return { ok: true, record };
}

module.exports = {
  generateToken,
  isWellFormedToken,
  createPreviewAccess,
  validatePreviewAccess,
  previewAccessPathname,
  TOKEN_HEX_LENGTH,
  PREVIEW_ACCESS_TTL_MS,
};
