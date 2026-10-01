'use strict';
const { validate, submit } = require('./access-request-store');
module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') { res.setHeader('Allow', 'POST'); return res.status(405).json({ error: 'Method not allowed.' }); }
  if (!(req.headers['content-type'] || '').startsWith('application/json')) return res.status(415).json({ error: 'JSON request required.' });
  const input = validate(req.body);
  if (!input) return res.status(400).json({ error: 'Check your name, business email and request details.' });
  try {
    // Only the platform-owned forwarding header is used on Vercel.
    const ip = process.env.VERCEL === '1' ? req.headers['x-vercel-forwarded-for'] : req.socket?.remoteAddress;
    if (typeof ip !== 'string' || !ip || ip.length > 128) throw new Error('Missing network boundary');
    const result = await submit(input, ip);
    if (result.code === 202) return res.status(202).json({ status: 'pending_review' });
    if (result.code === 429) { res.setHeader('Retry-After', String(result.retryAfter)); return res.status(429).json({ error: 'Too many requests. Please try again later.' }); }
    if (result.code === 409) return res.status(409).json({ error: 'This request changed. Please start a new request.' });
    return res.status(503).json({ error: 'Requests are temporarily unavailable. Please try again later.' });
  } catch (_) {
    // No PII, tokens, SDK errors or request bodies in logs.
    console.error('[access-request] storage_or_configuration_unavailable');
    return res.status(503).json({ error: 'We could not confirm your request. Please retry using the same form.' });
  }
};
