'use strict';

const { get } = require('@vercel/blob');
const { validateEntitlement, isWellFormedToken } = require('./_lib/entitlement-store');

// Platform routing — explicit ?platform= param takes precedence over User-Agent.
const PLATFORM_MAP = {
  'mac-arm64':   { os: 'macos',   architecture: 'arm64' },
  'windows-x64': { os: 'windows', architecture: 'x64'   },
};

const SUPPORTED_DISPLAY = ['macOS Apple Silicon (arm64)', 'Windows x64'];

// Canonical release manifest path in private Blob storage.
const RELEASE_MANIFEST_BLOB_PATHNAME = 'release/current/release-manifest.json';
const LEGACY_MANIFEST_BLOB_PATHNAME = 'rc3/current/manifest.json';

// Generic denial response — never reveal why a specific token/entitlement was denied.
function deny(res) {
  return res.status(403).json({ error: 'Access denied.' });
}

function detectPlatformFromUA(ua) {
  if (!ua) return null;
  const lower = ua.toLowerCase();
  if (lower.includes('windows')) return 'windows-x64';
  if (lower.includes('macintosh') || lower.includes('mac os')) return 'mac-arm64';
  return null;
}

async function readBlobJson(pathname) {
  const result = await get(pathname, { access: 'private' });
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
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { token, entitlement, platform: platformParam } = req.query;

  // Quick format gate before any Blob lookup.
  if (!token || !entitlement || !isWellFormedToken(token)) {
    return deny(res);
  }

  // Resolve the release manifest — must exist before any authorization.
  let manifest;
  try {
    manifest = await readBlobJson(RELEASE_MANIFEST_BLOB_PATHNAME);
    if (!manifest) {
      manifest = await readBlobJson(LEGACY_MANIFEST_BLOB_PATHNAME);
    }
    if (!manifest) {
      return res.status(503).json({
        error: 'VaultBasis release download is temporarily being updated. Please try again shortly.',
        supported: SUPPORTED_DISPLAY,
      });
    }
  } catch (e) {
    console.error('release manifest read/parse error:', e.message);
    return res.status(503).json({ error: 'Release manifest could not be read.' });
  }

  // Release State Lifecycle Gate
  // Canonical release authority derives from distribution_status (or release_state).
  // Valid lifecycle: BUILD_CREATED | FUNCTIONALLY_QUALIFIED | TRUST_QUALIFIED | RELEASE_MANIFEST_FROZEN | DISTRIBUTION_ACTIVE | SUPERSEDED | REVOKED
  const releaseState = (manifest.distribution_status || manifest.release_state || 'UNSPECIFIED').toUpperCase();

  // Canonical Authority Invariant: If legacy active boolean exists, enforce state == DISTRIBUTION_ACTIVE <=> active == true.
  if (typeof manifest.active === 'boolean') {
    const isStateActive = (releaseState === 'DISTRIBUTION_ACTIVE');
    if (manifest.active !== isStateActive) {
      console.error('Release authority conflict: state/active boolean divergence detected.');
      return res.status(403).json({ error: 'This release manifest has a conflicting authorization state.' });
    }
  }

  if (releaseState === 'REVOKED') {
    return res.status(410).json({ error: 'This release has been revoked for security or integrity reasons.' });
  }
  if (releaseState === 'SUPERSEDED') {
    return res.status(403).json({ error: 'This release is superseded. Please request the currently active release.' });
  }
  if (releaseState !== 'DISTRIBUTION_ACTIVE') {
    return res.status(403).json({ error: 'This release is not currently authorized for distribution.' });
  }

  // Resolve platform and artifact entry.
  const ua = req.headers['user-agent'] || '';
  const platformKey = platformParam || detectPlatformFromUA(ua);

  if (!platformKey || !PLATFORM_MAP[platformKey]) {
    return res.status(503).json({
      error: 'VaultBasis is not yet available for this platform.',
      supported: SUPPORTED_DISPLAY,
      hint: 'Use ?platform=mac-arm64 or ?platform=windows-x64',
    });
  }

  const target = PLATFORM_MAP[platformKey];
  let entry;
  if (Array.isArray(manifest.artifacts)) {
    entry = manifest.artifacts.find(
      (a) => (a.os === target.os && a.architecture === target.architecture) || a.platform === platformKey
    );
  } else if (manifest.artifacts && typeof manifest.artifacts === 'object') {
    entry = manifest.artifacts[platformKey] || manifest.artifacts[`${target.os}-${target.architecture}`];
  }

  if (!entry || !entry.sha256) {
    return res.status(503).json({
      error: 'VaultBasis is not yet available for this platform.',
      supported: SUPPORTED_DISPLAY,
    });
  }

  // SEC-002: validate against server-side entitlement record.
  // Checks: token exists, ACTIVE, not expired, entitlement ID matches,
  // artifact hash matches the qualified artifact being served.
  const authResult = await validateEntitlement(token, entitlement, entry.sha256);
  if (!authResult.ok) {
    return deny(res);
  }

  // Stream the authorized artifact.
  try {
    const blobResult = await get(entry.blobPathname, { access: 'private' });
    if (!blobResult) {
      return res.status(503).json({ error: 'Artifact not found in distribution storage.' });
    }

    const filename = entry.blobPathname.split('/').pop();
    res.setHeader('Content-Type', 'application/zip');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    res.setHeader('Cache-Control', 'no-store');
    if (blobResult.size) {
      res.setHeader('Content-Length', String(blobResult.size));
    }

    const reader = blobResult.stream.getReader();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      res.write(Buffer.from(value));
    }
    res.end();
  } catch (e) {
    console.error('artifact stream error:', e.message);
    return res.status(503).json({ error: 'Download could not be completed. Please try again.' });
  }
};
