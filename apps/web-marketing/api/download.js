const path = require('path');
const fs = require('fs');

// Canonical platform identifiers. Filenames come from the manifest — not hardcoded here.
const PLATFORM_MAP = {
  'mac-arm64':   { os: 'macos',   architecture: 'arm64' },
  'windows-x64': { os: 'windows', architecture: 'x64'   },
};

const SUPPORTED_DISPLAY = ['macOS arm64 (Apple Silicon)', 'Windows x64'];

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

  // Explicit ?platform= param takes precedence over User-Agent inference.
  const ua = req.headers['user-agent'] || '';
  const platformKey = platformParam || detectPlatformFromUA(ua);

  if (!platformKey || !PLATFORM_MAP[platformKey]) {
    return res.status(503).json({
      error: 'VaultBasis preview is not yet available for this platform.',
      supported: SUPPORTED_DISPLAY,
      hint: 'Use ?platform=mac-arm64 or ?platform=windows-x64 to select explicitly.',
    });
  }

  // Read manifest from api/ directory (co-located with this function at runtime).
  const manifestPath = path.join(__dirname, 'manifest.json');
  if (!fs.existsSync(manifestPath)) {
    console.error('manifest.json missing from api directory');
    return res.status(503).json({ error: 'Release manifest unavailable. Try again shortly.' });
  }

  let manifest;
  try {
    manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  } catch (e) {
    console.error('Failed to parse manifest.json:', e.message);
    return res.status(503).json({ error: 'Release manifest could not be read.' });
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
    console.error(`Artifact missing on disk: ${entry.filename}`);
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
