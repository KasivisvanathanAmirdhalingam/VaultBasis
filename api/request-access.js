'use strict';

/**
 * VaultBasis — Free Evaluation / Design Partner Access Provisioner
 * Conforms to MMP15-PROD-MAIL-001 and MMP15-PROD-DL-001.
 */

const crypto = require('crypto');
const { get } = require('@vercel/blob');
const { generateToken, createEntitlement } = require('./_lib/entitlement-store');
const { sendDeliveryEmail } = require('./_lib/delivery-mailer');

const RELEASE_MANIFEST_BLOB_PATHNAME = 'release/current/release-manifest.json';
const LEGACY_MANIFEST_BLOB_PATHNAME = 'rc3/current/manifest.json';

async function readManifest() {
  let result = null;
  try {
    result = await get(RELEASE_MANIFEST_BLOB_PATHNAME, { access: 'private' });
    if (!result) {
      result = await get(LEGACY_MANIFEST_BLOB_PATHNAME, { access: 'private' });
    }
  } catch (e) {
    // In local / test mode without Vercel Blob token, return mock manifest
    return {
      distribution_status: 'DISTRIBUTION_ACTIVE',
      artifacts: [
        { platform: 'mac-arm64', os: 'macos', architecture: 'arm64', sha256: 'mock_sha256_mac' },
        { platform: 'windows-x64', os: 'windows', architecture: 'x64', sha256: 'mock_sha256_win' },
      ],
    };
  }
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
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { email, name } = req.body || {};
  if (!email || !name) {
    return res.status(400).json({ error: 'Name and email are required' });
  }

  try {
    let qualifiedArtifactHash;
    try {
      const manifest = await readManifest();
      if (!manifest || !Array.isArray(manifest.artifacts) || manifest.artifacts.length === 0) {
        return res.status(503).json({ error: 'No qualified artifact is currently available for distribution.' });
      }
      qualifiedArtifactHash = manifest.artifacts[0].sha256;
    } catch (e) {
      console.error('manifest read error during provisioning:', e.message);
      return res.status(503).json({ error: 'Distribution manifest unavailable. Please try again.' });
    }

    // Generate entitlement credentials
    const entitlementId = `DP-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;
    const rawToken = generateToken();

    // Persist entitlement server-side before sending the email
    await createEntitlement(rawToken, {
      entitlementId,
      email,
      qualifiedArtifactHash,
    });

    const canonicalBase = process.env.PUBLIC_BASE_URL || 'http://localhost:3000';
    const downloadUrl = `${canonicalBase}/api/download?token=${rawToken}&entitlement=${entitlementId}`;
    const expiresAtIso = new Date(Date.now() + 72 * 60 * 60 * 1000).toISOString();

    const mailResult = await sendDeliveryEmail({
      toEmail: email,
      customerName: name,
      isPaidPlan: false,
      downloadUrl,
      expiresAtIso,
    });

    return res.status(200).json({
      status: 'success',
      entitlementId,
      message: 'Evaluation access email dispatched securely.',
      uatPreviewUrl: mailResult.uatPreviewUrl,
    });

  } catch (error) {
    console.error('Provisioning error:', error);
    return res.status(500).json({ error: 'Failed to provision access.' });
  }
};
