'use strict';
// SEC-003 now guards the only URL-producing path: trusted manual provisioning.
// Intake no longer sends email or constructs credential URLs.
const assert = require('node:assert/strict');
const { publicOrigin, downloadUrl } = require('../../scripts/lib/manual-provisioning');
let passed = 0;
for (const malicious of ['evil.example','https://evil.example','vaultbasis.com.evil.example']) {
 process.env.PUBLIC_BASE_URL='https://vaultbasis.com';
 const url=downloadUrl(process.env.PUBLIC_BASE_URL,'a'.repeat(64),'DP-TEST','windows-x64',{'host':malicious,'x-forwarded-host':malicious});
 assert.equal(new URL(url).origin,'https://vaultbasis.com');assert.equal(new URL(url).searchParams.get('platform'),'windows-x64');passed++;
}
delete process.env.PUBLIC_BASE_URL;
assert.throws(()=>publicOrigin());passed++;
for(const value of ['http://localhost:3000','https://user:pass@vaultbasis.com','https://vaultbasis.com/path','https://vaultbasis.com/?host=evil']) assert.throws(()=>publicOrigin(value));passed++;
assert.equal(require('../../apps/web-marketing/api/request-access'),require('../../api/request-access'));passed++;
console.log(`SEC-003 TRUSTED ORIGIN TEST RESULTS: ${passed} PASSED | 0 FAILED`);
