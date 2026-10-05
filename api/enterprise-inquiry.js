'use strict';

/**
 * VaultBasis — Enterprise Commercial Inquiry API (MMP15-PROD-BILL-001)
 *
 * Handles custom / high-capacity firm requests.
 * Explicitly separated from self-serve credit card checkout.
 */

const crypto = require('crypto');
const { put } = require('@vercel/blob');

const _memoryInquiries = new Map();

function _hasBlobStorage() {
  return Boolean(process.env.BLOB_READ_WRITE_TOKEN);
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { name, email, firm, estimatedCases, notes } = req.body || {};

  if (!name || !email) {
    return res.status(400).json({ error: 'Name and work email are required.' });
  }

  const inquiryId = `INQ-${new Date().getUTCFullYear()}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;
  const now = new Date().toISOString();

  const inquiryRecord = {
    inquiryId,
    customerName: name.trim(),
    customerEmail: email.trim().toLowerCase(),
    firmName: firm ? firm.trim() : null,
    estimatedCases: estimatedCases || '250+',
    notes: notes ? notes.trim() : null,
    status: 'RECEIVED',
    createdAt: now,
  };

  try {
    if (_hasBlobStorage()) {
      await put(`inquiries/${inquiryId}.json`, JSON.stringify(inquiryRecord), {
        access: 'private',
        contentType: 'application/json',
        addRandomSuffix: false,
        allowOverwrite: false,
      });
    } else {
      _memoryInquiries.set(inquiryId, inquiryRecord);
    }

    return res.status(200).json({
      status: 'success',
      inquiryId,
      message: 'Enterprise inquiry received. Our commercial team will provide an IT security pack and custom quote.',
    });
  } catch (error) {
    console.error('[enterprise-inquiry] Error recording inquiry:', error);
    return res.status(500).json({ error: 'Failed to record enterprise inquiry.' });
  }
};
