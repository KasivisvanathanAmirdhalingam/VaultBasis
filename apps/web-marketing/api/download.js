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

  // The artifact is packaged securely outside the public folder (in the 'data' directory inside api)
  const artifactPath = path.join(__dirname, 'data', 'VaultBasis-RC1-DesignPartner.zip');
  
  if (!fs.existsSync(artifactPath)) {
    return res.status(404).json({ error: 'Distribution artifact not found or temporarily unavailable.' });
  }

  const stat = fs.statSync(artifactPath);

  res.writeHead(200, {
    'Content-Type': 'application/zip',
    'Content-Length': stat.size,
    'Content-Disposition': `attachment; filename="VaultBasis-RC1-DesignPartner.zip"`
  });

  const readStream = fs.createReadStream(artifactPath);
  readStream.pipe(res);
};
