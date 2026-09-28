const nodemailer = require('nodemailer');
const crypto = require('crypto');

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { email, name } = req.body;
  if (!email || !name) {
    return res.status(400).json({ error: 'Name and email are required' });
  }

  try {
    // Generate an entitlement/license token
    const entitlementId = `DP-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;
    const token = crypto.randomBytes(16).toString('hex');

    // Create a Nodemailer test account (Ethereal) to safely simulate email sending in UAT
    const testAccount = await nodemailer.createTestAccount();
    const transporter = nodemailer.createTransport({
      host: "smtp.ethereal.email",
      port: 587,
      secure: false, 
      auth: {
        user: testAccount.user, 
        pass: testAccount.pass, 
      },
    });

    const host = req.headers['x-forwarded-host'] || req.headers.host;
    const protocol = host.includes('localhost') ? 'http' : 'https';
    const downloadUrl = `${protocol}://${host}/api/download?token=${token}&entitlement=${entitlementId}`;

    const htmlContent = `
      <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="color: #3b82f6;">VaultBasis Design-Partner Access</h2>
        <p>Hello ${name},</p>
        <p>Your Design-Partner entitlement has been approved and provisioned.</p>
        <div style="background: #f8fafc; padding: 15px; border-radius: 6px; margin: 20px 0;">
          <strong>Entitlement ID:</strong> ${entitlementId}<br/>
          <strong>Access Level:</strong> RC1 Preview
        </div>
        <p><strong>Your Secure Artifact Download:</strong></p>
        <a href="${downloadUrl}" style="display: inline-block; background: #3b82f6; color: white; text-decoration: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;">Download VaultBasis Edge (.zip)</a>
        <p style="margin-top: 20px; font-size: 0.9em; color: #64748b;">
          * Note: This link is uniquely tied to your entitlement. Do not forward it.<br/>
          * Attached: VaultBasis User Guide & Quick Start instructions are inside the downloaded package.
        </p>
      </div>
    `;

    // Send the email
    const info = await transporter.sendMail({
      from: '"VaultBasis Provisioning" <no-reply@vaultbasis.com>',
      to: email,
      subject: "Your VaultBasis Access & Download Link",
      html: htmlContent,
    });

    // In a real prod setup, we would save the token to a DB. 
    // For UAT, we rely on the token validation in the download endpoint.

    return res.status(200).json({
      status: 'success',
      entitlementId,
      message: 'Email dispatched securely.',
      uatPreviewUrl: nodemailer.getTestMessageUrl(info) // Expose Ethereal URL so associate can view the email without a real inbox
    });

  } catch (error) {
    console.error('Email dispatch error:', error);
    return res.status(500).json({ error: 'Failed to provision access.' });
  }
};
