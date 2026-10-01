'use strict';
// Low-volume operational intake, separate from every capability store.
const crypto = require('crypto');
const blob = require('@vercel/blob');
const DAY = 86400000;
const RETENTION_MS = 90 * DAY;
function config() {
  const namespace = process.env.ACCESS_REQUEST_NAMESPACE;
  const secret = process.env.ACCESS_REQUEST_SECRET;
  if (!/^[a-z0-9-]{3,64}$/.test(namespace || '') || !secret || secret.length < 32) throw new Error('Intake configuration unavailable');
  return { pathname: `access-requests/${namespace}/ledger.json`, secret };
}
function digest(value) { return crypto.createHmac('sha256', config().secret).update(value).digest('hex'); }
async function read() {
  let result;
  try { result = await blob.get(config().pathname, { access: 'private', useCache: false }); }
  catch (e) { if (e.name !== 'BlobNotFoundError') throw e; }
  if (!result) return { data: { version: 1, requests: [], limits: {} }, etag: null };
  const data = JSON.parse(await new Response(result.stream).text());
  if (data.version !== 1 || !Array.isArray(data.requests) || !data.limits || !result.blob?.etag) throw new Error('Invalid intake storage');
  return { data, etag: result.blob.etag };
}
async function transact(change) {
  for (let attempt = 0; attempt < 6; attempt++) {
    const { data, etag } = await read();
    const now = Date.now();
    data.requests = data.requests.filter(r => now - Date.parse(r.createdAt) < RETENTION_MS);
    for (const [key, limit] of Object.entries(data.limits)) if (limit.until <= now) delete data.limits[key];
    const result = change(data, now);
    try {
      await blob.put(config().pathname, JSON.stringify(data), {
        access: 'private', contentType: 'application/json', addRandomSuffix: false,
        ...(etag ? { ifMatch: etag } : { allowOverwrite: false }),
      });
      return result;
    } catch (_) {
      // Re-read and recompute after concurrent writes or unknown outcomes.
      // Never overwrite another writer or claim an unpersisted success.
      if (attempt === 5) throw new Error('Intake storage unavailable');
    }
  }
}
function validate(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) return null;
  const { name, email, context = '', requestId } = body;
  if (![name, email, context, requestId].every(v => typeof v === 'string')) return null;
  const normalized = { name: name.trim(), email: email.trim().toLowerCase(), context: context.trim() };
  if (!normalized.name || normalized.name.length > 200 || normalized.email.length > 254 ||
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalized.email) || normalized.context.length > 500 ||
      /[\x00-\x1f\x7f]/.test(normalized.name + normalized.email + normalized.context) ||
      !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(requestId)) return null;
  return { ...normalized, requestId };
}
async function submit(input, clientIp) {
  const retryKey = digest(`retry:${input.requestId}`);
  const fingerprint = digest(JSON.stringify([input.name, input.email, input.context]));
  return transact((data, now) => {
    const previous = data.requests.find(r => r.retryKey === retryKey);
    if (previous) return { code: previous.fingerprint === fingerprint ? 202 : 409 };
    const buckets = [['global', 60, DAY], [digest(`ip:${clientIp}`), 5, 3600000], [digest(`email:${input.email}`), 2, DAY]];
    for (const [key, max] of buckets) {
      const item = data.limits[key];
      if (item && item.count >= max) return { code: 429, retryAfter: Math.ceil((item.until - now) / 1000) };
    }
    for (const [key, , duration] of buckets) {
      data.limits[key] ||= { count: 0, until: now + duration };
      data.limits[key].count++;
    }
    // Email is operational contact data, never identity proof or consent.
    if (data.requests.some(r => r.email === input.email && ['PENDING_REVIEW', 'PROVISIONING', 'APPROVED'].includes(r.state))) return { code: 202 };
    if (data.requests.length >= 500) return { code: 503 };
    data.requests.push({ id: crypto.randomUUID(), retryKey, fingerprint, name: input.name,
      email: input.email, context: input.context, createdAt: new Date(now).toISOString(), state: 'PENDING_REVIEW' });
    return { code: 202 };
  });
}
module.exports = { read, transact, validate, submit, RETENTION_MS };
