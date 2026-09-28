const path = require('path');
const fs = require('fs');

// Platform routing — explicit ?platform= param takes precedence over User-Agent.
// Architecture is never inferred: Mac User-Agent → recommend mac-arm64 only,
// but the explicit selector on the download page is authoritative.
const PLATFORM_MAP = {
  'mac-arm64':   { os: 'macos',   architecture: 'arm64' },
  'windows-x64': { os: 'windows', architecture: 'x64'   },
};

const SUPPORTED_DISPLAY = ['macOS Apple Silicon (arm64)', 'Windows x64'];

function detectPlatformFromUA(ua) {
  if (!ua) return null;
  const lower = ua.toLowerCase();
  // User-Agent detection is advisory only — the download page always shows
  // an explicit platform selector. UA detection never silently routes to a
  // specific architecture when uncertain.
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

  // Read manifest — if absent, no artifact is served (no RC1 fallback).
  const manifestPath = path.join(__dirname, 'manifest.json');
  if (!fs.existsSync(manifestPath)) {
    return res.status(503).json({
      error: 'VaultBasis preview download is temporarily being updated. Please try again shortly.',
      supported: SUPPORTED_DISPLAY,
    });
  }

  let manifest;
  try {
    manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  } catch (e) {
    console.error('manifest.json parse error:', e.message);
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

  const artifactPath = path.join(__dirname, 'data', entry.filename);
  if (!fs.existsSync(artifactPath)) {
    console.error(`Artifact not on disk: ${entry.filename}`);
    return res.status(503).json({ error: 'Artifact temporarily unavailable.' });
  }

  const stat = fs.statSync(artifactPath);
  res.writeHead(200, {
    'Content-Type': 'application/zip',
    'Content-Length': stat.size,
    'Content-Disposition': `attachment; filename="${entry.filename}"`,
  });
  fs.createReadStream(artifactPath).pipe(res);
};
