'use strict';
const crypto = require('crypto');
const blob = require('@vercel/blob');
const intake = require('../../api/access-request-store');
const preview = require('../../api/preview-access-store');
const entitlement = require('../../api/entitlement-store');
function publicOrigin(value = process.env.PUBLIC_BASE_URL) {
  const url = new URL(value);
  if (url.protocol !== 'https:' || url.username || url.password || url.pathname !== '/' || url.search || url.hash) throw new Error('Explicit HTTPS public origin required');
  return url.origin;
}
function downloadUrl(origin, token, id, platform) {
  const url = new URL('/api/download', publicOrigin(origin));
  url.search = new URLSearchParams({ token, entitlement: id, platform }).toString();
  return url.href;
}
async function blobJson(pathname) {
  const result = await blob.get(pathname, { access: 'private', useCache: false });
  if (!result) throw new Error('Required record unavailable');
  return { record: JSON.parse(await new Response(result.stream).text()), etag: result.blob.etag };
}
async function issue({ id, operator, platform, qualification }, persistPrivatePacket) {
  if (!/^[A-Za-z0-9 ._@-]{1,100}$/.test(operator || '')) throw new Error('Operator attribution required');
  const origin = publicOrigin();
  let artifact;
  if (platform) {
    const mapping = { 'mac-arm64': ['macos', 'arm64', 'DISTRIBUTION_QUALIFIED_MAC'], 'windows-x64': ['windows', 'x64', 'DISTRIBUTION_QUALIFIED_WINDOWS'] }[platform];
    if (!mapping || qualification?.state !== mapping[2] || !/^[a-f0-9]{64}$/.test(qualification.sha256 || '') || !qualification.evidence || !qualification.sourceSha?.match(/^[a-f0-9]{40}$/)) throw new Error('Exact recipient-path qualification evidence required');
    const { record: manifest } = await blobJson('rc3/current/manifest.json');
    artifact = manifest.artifacts?.find(a => a.os === mapping[0] && a.architecture === mapping[1] && a.sha256 === qualification.sha256);
    if (!artifact) throw new Error('Qualified artifact does not match current distribution');
  }
  const token = crypto.randomBytes(32).toString('hex');
  const operation = crypto.randomUUID();
  const kind = platform ? `artifact:${platform}` : 'preview';
  const credentialId = `${platform ? 'DP' : 'VA'}-${crypto.randomBytes(8).toString('hex').toUpperCase()}`;
  const pathname = platform ? entitlement.entitlementPathname(token) : preview.previewAccessPathname(token);
  // Output is reserved privately before capability creation. A failed operation
  // is NOT retried automatically: the packet enables explicit revocation.
  let applicant;
  await intake.transact((data, now) => {
    const r = data.requests.find(r => r.id === id);
    if (!r || !['PENDING_REVIEW', 'APPROVED'].includes(r.state) || r.grants?.some(g => g.kind === kind)) throw new Error('Request unavailable or grant already attempted');
    applicant = r;
    r.grants ||= [];
    r.grants.push({ kind, operation, pathname, credentialId, operator, state: 'PROVISIONING', at: new Date(now).toISOString(), ...(qualification ? { qualification } : {}) });
    r.state = 'PROVISIONING';
  });
  const packet = { requestId: id, operation, state: 'PREPARED_NOT_DELIVERED', email: applicant.email,
    expiresWithinHours: 72, ...(platform ? { platform, artifactSha256: artifact.sha256,
      downloadUrl: downloadUrl(origin, token, credentialId, platform) } : { verifierAccessUrl: `${origin}/verifier-access`, accessId: credentialId, token }) };
  await persistPrivatePacket(packet);
  if (platform) await entitlement.createEntitlement(token, { entitlementId: credentialId, email: applicant.email, qualifiedArtifactHash: artifact.sha256 });
  else await preview.createPreviewAccess(token, { accessId: credentialId, email: applicant.email });
  await intake.transact((data) => {
    const r = data.requests.find(r => r.id === id);
    const grant = r?.grants?.find(g => g.operation === operation);
    if (!grant || grant.state !== 'PROVISIONING') throw new Error('Issuance requires operator recovery');
    grant.state = 'ISSUED'; r.state = 'APPROVED';
  });
  // Never mark delivery: the operator must contact the applicant separately.
  return { ...packet, state: 'ISSUED_NOT_DELIVERED' };
}
async function revoke(id, operator) {
  if (!operator) throw new Error('Operator attribution required');
  const { data } = await intake.read();
  const r = data.requests.find(r => r.id === id);
  if (!r) throw new Error('Request unavailable');
  for (const grant of r.grants || []) {
    let existing;
    try { existing = await blobJson(grant.pathname); }
    catch (e) { if (e.name === 'BlobNotFoundError') continue; throw e; }
    await blob.put(grant.pathname, JSON.stringify({ ...existing.record, status: 'REVOKED' }), {
      access: 'private', addRandomSuffix: false, contentType: 'application/json', ifMatch: existing.etag,
    });
  }
  await intake.transact(({ requests }) => {
    const request = requests.find(r => r.id === id);
    request.state = 'CLOSED'; request.closedBy = operator;
    for (const grant of request.grants || []) grant.state = 'REVOKED';
  });
}
module.exports = { publicOrigin, downloadUrl, issue, revoke };
