const path = require('path');
const fs = require('fs');

module.exports = async (req, res) => {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { token, entitlement } = req.query;

  // Real auth validation goes here. For UAT, we ensure they have tokens.
  if (!token || !entitlement) {
    return res.status(401).json({ error: 'Unauthorized: Invalid or missing distribution token.' });
  }

  // RC3 macOS arm64 candidate — only qualified platform currently available.
  // Windows x64 will be added to this resolver once RC3-WIN passes qualification.
  const artifactFilename = 'VaultBasis-RC3-macOS-arm64.zip';
  const artifactPath = path.join(__dirname, 'data', artifactFilename);

  if (!fs.existsSync(artifactPath)) {
    return res.status(404).json({ error: 'Distribution artifact not found or temporarily unavailable.' });
  }

  const stat = fs.statSync(artifactPath);

  res.writeHead(200, {
    'Content-Type': 'application/zip',
    'Content-Length': stat.size,
    'Content-Disposition': `attachment; filename="${artifactFilename}"`
  });

  const readStream = fs.createReadStream(artifactPath);
  readStream.pipe(res);
};
