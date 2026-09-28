/**
 * VaultBasis Edge — JavaScript Normative Canonicalization Test Suite (RC2-L1.2)
 * Verifies JS implementation against TC-CANON-01..12 frozen test vectors.
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function canonicalizeJson(obj) {
  if (obj === null || typeof obj !== 'object') {
    return JSON.stringify(obj);
  }
  if (Array.isArray(obj)) {
    return '[' + obj.map(canonicalizeJson).join(',') + ']';
  }
  // Sort keys using Unicode code point order (matching Python and VB-CJCS-0.1)
  const keys = Object.keys(obj).sort((a, b) => {
    if (a < b) return -1;
    if (a > b) return 1;
    return 0;
  });
  return '{' + keys.map(k => JSON.stringify(k) + ':' + canonicalizeJson(obj[k])).join(',') + '}';
}

function runTests() {
  const vectorFilePath = path.join(__dirname, '..', 'fixtures', 'canonical_vectors_v0.1.json');
  const rawData = fs.readFileSync(vectorFilePath, 'utf8');
  const data = JSON.parse(rawData);

  let passed = 0;
  let failed = 0;

  console.log('Running JavaScript VB-CJCS-0.1 Normative Vector Suite...');

  for (const vec of data.vectors) {
    const actualJsonStr = canonicalizeJson(vec.input);
    const actualBytes = Buffer.from(actualJsonStr, 'utf8');
    const expectedJsonStr = vec.expected_canonical_json;
    const expectedSha256 = vec.expected_sha256;
    const actualSha256 = crypto.createHash('sha256').update(actualBytes).digest('hex');

    // 1. Check String / Byte equality
    if (actualJsonStr !== expectedJsonStr) {
      console.error(`❌ FAIL: ${vec.id} (${vec.description}) - String mismatch`);
      console.error(`   Expected: ${expectedJsonStr}`);
      console.error(`   Actual:   ${actualJsonStr}`);
      failed++;
      continue;
    }

    // 2. Check SHA-256 Digest
    if (actualSha256 !== expectedSha256) {
      console.error(`❌ FAIL: ${vec.id} (${vec.description}) - Hash mismatch`);
      console.error(`   Expected: ${expectedSha256}`);
      console.error(`   Actual:   ${actualSha256}`);
      failed++;
      continue;
    }

    console.log(`✓ PASS: ${vec.id} - ${vec.description}`);
    passed++;
  }

  console.log(`\n==================================================`);
  console.log(`JS CANONICALIZATION TEST RESULTS: ${passed} PASSED | ${failed} FAILED`);
  console.log(`==================================================`);

  if (failed > 0) {
    process.exit(1);
  }
}

runTests();
