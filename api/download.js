const { get } = require('@vercel/blob');

// Platform routing — explicit ?platform= param takes precedence over User-Agent.
// Architecture is never inferred: Mac User-Agent → recommend mac-arm64 only,
// but the explicit selector on the download page is authoritative.
const PLATFORM_MAP = {
  'mac-arm64':   { os: 'macos',   architecture: 'arm64' },
  'windows-x64': { os: 'windows', architecture: 'x64'   },
};

const SUPPORTED_DISPLAY = ['macOS Apple Silicon (arm64)', 'Windows x64'];

// Stable pointer in private Blob — overwritten on each RC3 promotion,
// always resolves to the latest BUILD_VERIFIED manifest.
const MANIFEST_BLOB_PATHNAME = 'rc3/current/manifest.json';

function detectPlatformFromUA(ua) {
  if (!ua) return null;
  const lower = ua.toLowerCase();
  if (lower.includes('windows')) return 'windows-x64';
  if (lower.includes('macintosh') || lower.includes('mac os')) return 'mac-arm64';
  return null;
}

module.exports = async (req, res) => {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { token, entitlement, platform: platformParam } = req.query;

  if (!token || !entitlement) {
    return res.status(401).json({ error: 'Unauthorized: Invalid or missing distribution token.' });
  }

  // Read promotion manifest from private Blob — if absent, no artifact is served.
  let manifest;
  try {
    const manifestResult = await get(MANIFEST_BLOB_PATHNAME, { access: 'private' });
    if (!manifestResult) {
      return res.status(503).json({
        error: 'VaultBasis preview download is temporarily being updated. Please try again shortly.',
        supported: SUPPORTED_DISPLAY,
      });
    }
    const chunks = [];
    const reader = manifestResult.stream.getReader();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
    }
    const manifestJson = Buffer.concat(chunks.map(c => Buffer.from(c))).toString('utf8');
    manifest = JSON.parse(manifestJson);
  } catch (e) {
    console.error('manifest read/parse error:', e.message);
    return res.status(503).json({ error: 'Release manifest could not be read.' });
  }

  const ua = req.headers['user-agent'] || '';
  const platformKey = platformParam || detectPlatformFromUA(ua);

  if (!platformKey || !PLATFORM_MAP[platformKey]) {
    return res.status(503).json({
      error: 'VaultBasis preview is not yet available for this platform.',
      supported: SUPPORTED_DISPLAY,
      hint: 'Use ?platform=mac-arm64 or ?platform=windows-x64',
    });
  }

  const target = PLATFORM_MAP[platformKey];
  const entry = manifest.artifacts.find(
    (a) => a.os === target.os && a.architecture === target.architecture
  );

  if (!entry) {
    return res.status(503).json({
      error: 'VaultBasis preview is not yet available for this platform.',
      supported: SUPPORTED_DISPLAY,
    });
  }

  // Stream the artifact directly from private Blob storage through this function.
  // issueSignedToken + presignUrl require a scope not available under OIDC-only
  // project connections. Streaming via get() uses the same OIDC path as the
  // manifest read, which is confirmed working.
  try {
    const blobResult = await get(entry.blobPathname, { access: 'private' });
    if (!blobResult) {
      return res.status(503).json({ error: 'Artifact not found in distribution storage.' });
    }

    const filename = entry.blobPathname.split('/').pop();
    res.setHeader('Content-Type', 'application/zip');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    res.setHeader('Cache-Control', 'no-store');

    // Pipe the Blob stream to the response
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
