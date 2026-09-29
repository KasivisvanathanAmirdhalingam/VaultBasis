'use strict';

const nodemailer = require('nodemailer');
const crypto = require('crypto');
const { get } = require('@vercel/blob');
const { generateToken, createEntitlement } = require('./entitlement-store');

// External CPA email delivery: NOT PRODUCTION-QUALIFIED.
// Ethereal is a UAT SMTP sink — emails are captured at ethereal.email for
// review, not delivered to real inboxes. Separate blocker before CPA distribution.

const MANIFEST_BLOB_PATHNAME = 'rc3/current/manifest.json';

async function readManifest() {
  const result = await get(MANIFEST_BLOB_PATHNAME, { access: 'private' });
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

  const { email, name } = req.body;
  if (!email || !name) {
    return res.status(400).json({ error: 'Name and email are required' });
  }

  try {
    // Read the promotion manifest to bind the entitlement to the current
    // qualified artifact hash. Authorization later requires this binding:
    // a provisioned entitlement cannot silently grant a different artifact.
    let qualifiedArtifactHash;
    try {
      const manifest = await readManifest();
      if (!manifest || !Array.isArray(manifest.artifacts) || manifest.artifacts.length === 0) {
        return res.status(503).json({ error: 'No qualified artifact is currently available for distribution.' });
      }
      // Use the first artifact's hash as the binding; both platforms share
      // the same promotion event, so either hash would be equally valid here.
      // The download handler validates per-platform artifact hash at download time.
      qualifiedArtifactHash = manifest.artifacts[0].sha256;
    } catch (e) {
      console.error('manifest read error during provisioning:', e.message);
      return res.status(503).json({ error: 'Distribution manifest unavailable. Please try again.' });
    }

    // Generate entitlement credentials
    const entitlementId = `DP-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;
    const rawToken = generateToken();

    // Persist the entitlement server-side before sending the email.
    // If this fails, the email is not sent — no orphaned credentials.
    await createEntitlement(rawToken, {
      entitlementId,
      email,
      qualifiedArtifactHash,
    });

    // SEC-003 fix: canonical origin from explicit env var only.
    const canonicalBase = process.env.PUBLIC_BASE_URL || 'http://localhost:3000';
    const downloadUrl = `${canonicalBase}/api/download?token=${rawToken}&entitlement=${entitlementId}`;

    const testAccount = await nodemailer.createTestAccount();
    const transporter = nodemailer.createTransport({
      host: 'smtp.ethereal.email',
      port: 587,
      secure: false,
      auth: { user: testAccount.user, pass: testAccount.pass },
    });

    const htmlContent = `
      <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="color: #3b82f6;">VaultBasis Design-Partner Access</h2>
        <p>Hello ${name},</p>
        <p>Your Design-Partner entitlement has been approved and provisioned.</p>
        <div style="background: #f8fafc; padding: 15px; border-radius: 6px; margin: 20px 0;">
          <strong>Entitlement ID:</strong> ${entitlementId}<br/>
          <strong>Access Level:</strong> RC3 Design Partner Preview
        </div>
        <p><strong>Your Secure Artifact Download:</strong></p>
        <a href="${downloadUrl}" style="display: inline-block; background: #3b82f6; color: white; text-decoration: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;">Download VaultBasis Edge (.zip)</a>
        <p style="margin-top: 20px; font-size: 0.9em; color: #64748b;">
          * This link is uniquely tied to your entitlement and expires in 72 hours. Do not forward it.<br/>
          * Quick Start and Troubleshooting guides are included inside the downloaded package.
        </p>
      </div>
    `;

    const info = await transporter.sendMail({
      from: '"VaultBasis Provisioning" <no-reply@vaultbasis.com>',
      to: email,
      subject: 'Your VaultBasis Access & Download Link',
      html: htmlContent,
    });

    return res.status(200).json({
      status: 'success',
      entitlementId,
      message: 'Email dispatched securely.',
      uatPreviewUrl: nodemailer.getTestMessageUrl(info),
    });

  } catch (error) {
    console.error('Provisioning error:', error);
    return res.status(500).json({ error: 'Failed to provision access.' });
  }
};
