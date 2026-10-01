'use strict';

/**
 * Blob-backed entitlement store for design-partner access control.
 *
 * Trust namespace: entitlements/  (never mixed with rc3/ artifact namespace)
 * Key derivation:  entitlements/sha256(rawToken).json
 *   — bearer token is never used as a Blob pathname, keeping it out of logs
 *     and administrative views.
 *
 * Security contract:
 *   - Expiring: entitlements have a server-set expiresAt; past-expiry = deny
 *   - Revocable: status REVOKED = deny, regardless of expiry
 *   - Artifact-bound: entitlement records the qualifiedArtifactHash that was
 *     current at provisioning time; serving a different artifact = deny
 *   - Not guaranteed single-use: @vercel/blob has no atomic CAS; concurrent
 *     requests may both succeed within the validity window. Documented limit.
 *   - Fail-closed: any storage error → deny, never allow
 */

const crypto = require('crypto');
const { put, get, BlobNotFoundError } = require('@vercel/blob');

const ENTITLEMENT_SCHEMA_VERSION = '1';
const ENTITLEMENT_TTL_MS = 72 * 60 * 60 * 1000; // 72 hours
const TOKEN_BYTE_LENGTH = 32;
const TOKEN_HEX_LENGTH = TOKEN_BYTE_LENGTH * 2; // 64 hex chars

/**
 * Derive the private Blob pathname for a raw bearer token.
 * SHA-256 of the token keeps the bearer credential out of storage paths.
 */
function entitlementPathname(rawToken) {
  const digest = crypto.createHash('sha256').update(rawToken, 'utf8').digest('hex');
  return `entitlements/${digest}.json`;
}

/**
 * Generate a new cryptographically random bearer token.
 * Returns a 64-character lowercase hex string.
 */
function generateToken() {
  return crypto.randomBytes(TOKEN_BYTE_LENGTH).toString('hex');
}

/**
 * Validate that a token string has the expected format.
 * Rejects anything that couldn't be a legitimately generated token
 * before making any storage lookup.
 */
function isWellFormedToken(token) {
  return (
    typeof token === 'string' &&
    token.length === TOKEN_HEX_LENGTH &&
    /^[0-9a-f]+$/.test(token)
  );
}

/**
 * Write a new entitlement record to private Blob storage.
 *
 * @param {string} rawToken - The bearer token (64 hex chars)
 * @param {object} fields
 * @param {string} fields.entitlementId  - e.g. "DP-AABBCCDD"
 * @param {string} fields.email          - Recipient email
 * @param {string} fields.qualifiedArtifactHash - SHA-256 of the artifact at provisioning time
 * @returns {Promise<void>}
 */
async function createEntitlement(rawToken, { entitlementId, email, qualifiedArtifactHash }) {
  const now = Date.now();
  const record = {
    schemaVersion: ENTITLEMENT_SCHEMA_VERSION,
    entitlementId,
    email,
    createdAt: new Date(now).toISOString(),
    expiresAt: new Date(now + ENTITLEMENT_TTL_MS).toISOString(),
    status: 'ACTIVE',
    qualifiedArtifactHash,
  };

  const pathname = entitlementPathname(rawToken);
  await put(pathname, JSON.stringify(record), {
    access: 'private',
    contentType: 'application/json',
    addRandomSuffix: false,
    allowOverwrite: false, // never silently overwrite an existing entitlement
  });
}

/**
 * Look up and validate an entitlement.
 *
 * Returns { ok: true, record } on success.
 * Returns { ok: false, reason } on any failure — callers must treat all
 * failures identically (generic 401/403) to avoid information disclosure.
 *
 * @param {string} rawToken        - Supplied bearer token
 * @param {string} entitlementId   - Supplied entitlement ID (from query param)
 * @param {string} artifactHash    - SHA-256 of the artifact about to be served
 */
async function validateEntitlement(rawToken, entitlementId, artifactHash) {
  // 1. Format gate — reject before any Blob lookup
  if (!isWellFormedToken(rawToken)) {
    return { ok: false, reason: 'malformed_token' };
  }

  // 2. Blob lookup — missing key = token does not exist
  let record;
  try {
    const pathname = entitlementPathname(rawToken);
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
    // Any other storage error → fail closed
    console.error('[entitlement-store] lookup error:', e.message);
    return { ok: false, reason: 'storage_error' };
  }

  // 3. Status check
  if (record.status !== 'ACTIVE') {
    return { ok: false, reason: 'not_active' };
  }

  // 4. Expiry check
  if (Date.now() > new Date(record.expiresAt).getTime()) {
    return { ok: false, reason: 'expired' };
  }

  // 5. Entitlement ID binding — timing-safe compare on the stored ID
  //    (entitlementId is not the high-entropy secret, but compare safely anyway)
  const storedIdBuf = Buffer.from(record.entitlementId, 'utf8');
  const suppliedIdBuf = Buffer.from(String(entitlementId), 'utf8');
  const idMatch =
    storedIdBuf.length === suppliedIdBuf.length &&
    crypto.timingSafeEqual(storedIdBuf, suppliedIdBuf);
  if (!idMatch) {
    return { ok: false, reason: 'entitlement_mismatch' };
  }

  // 6. Artifact binding — entitlement must match the artifact being served
  if (record.qualifiedArtifactHash !== artifactHash) {
    return { ok: false, reason: 'artifact_mismatch' };
  }

  return { ok: true, record };
}

module.exports = {
  generateToken,
  isWellFormedToken,
  createEntitlement,
  validateEntitlement,
  entitlementPathname,
  TOKEN_HEX_LENGTH,
  ENTITLEMENT_TTL_MS,
};
