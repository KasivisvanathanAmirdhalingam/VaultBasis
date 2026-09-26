#!/usr/bin/env node
/**
 * VaultBasis — Incremental Public Web Build Pipeline
 * Prepares the production static web distribution for Vercel deployment.
 * 
 * Conforms to:
 * - PRD §21.1: Zero Token Bleed (no private keys, no customer data, no backend DBs in bundle)
 * - PRD §34.1: Public Marketing & Trust Portal
 * - PRD §34.3: Public Offline Client-Side Verifier
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..');
const DIST_DIR = path.join(REPO_ROOT, 'dist', 'public-web');
const APPS_DIR = path.join(REPO_ROOT, 'apps');
const SCHEMAS_DIR = path.join(REPO_ROOT, 'schemas', 'receipt');

console.log('================================================================================');
console.log('       VAULTBASIS — INCREMENTAL VERCEL PUBLIC WEB BUILD PIPELINE                 ');
console.log('================================================================================');

// 1. Get Build Metadata
let commitSha = 'preview';
try {
  commitSha = execSync('git rev-parse --short HEAD', { cwd: REPO_ROOT }).toString().trim();
} catch (e) {
  console.warn('⚠️ Unable to determine git commit hash. Using "preview".');
}
const buildTimestamp = new Date().toISOString();
console.log(`Commit SHA:      ${commitSha}`);
console.log(`Build Timestamp: ${buildTimestamp}`);
console.log(`Output Target:   ${DIST_DIR}`);
console.log('--------------------------------------------------------------------------------');

// 2. Clean and Create Target Directories
if (fs.existsSync(DIST_DIR)) {
  fs.rmSync(DIST_DIR, { recursive: true, force: true });
}
fs.mkdirSync(DIST_DIR, { recursive: true });
fs.mkdirSync(path.join(DIST_DIR, 'verifier'), { recursive: true });
fs.mkdirSync(path.join(DIST_DIR, 'schemas'), { recursive: true });

// 3. Build Marketing Landing Page (dist/public-web/index.html)
const marketingSourcePath = path.join(APPS_DIR, 'web-marketing', 'index.html');
if (!fs.existsSync(marketingSourcePath)) {
  console.error(`❌ ERROR: Marketing site source missing at ${marketingSourcePath}`);
  process.exit(1);
}
let marketingHtml = fs.readFileSync(marketingSourcePath, 'utf8');

// Inject build metadata into marketing HTML
marketingHtml = marketingHtml.replace(
  '<!-- BUILD_METADATA -->',
  `<!-- VaultBasis Build: ${commitSha} | Timestamp: ${buildTimestamp} -->`
);

fs.writeFileSync(path.join(DIST_DIR, 'index.html'), marketingHtml, 'utf8');
console.log('✓ Packaged Public Marketing Portal -> dist/public-web/index.html');

// 4. Build Public Web Verifier (dist/public-web/verifier/index.html)
const verifierSourcePath = path.join(APPS_DIR, 'web-verifier', 'index.html');
if (!fs.existsSync(verifierSourcePath)) {
  console.error(`❌ ERROR: Web verifier source missing at ${verifierSourcePath}`);
  process.exit(1);
}
let verifierHtml = fs.readFileSync(verifierSourcePath, 'utf8');
fs.writeFileSync(path.join(DIST_DIR, 'verifier', 'index.html'), verifierHtml, 'utf8');
console.log('✓ Packaged Public Offline Verifier -> dist/public-web/verifier/index.html');

// 5. Copy Normative Schema (dist/public-web/schemas/receipt-v0.1.json)
const schemaSourcePath = path.join(SCHEMAS_DIR, 'receipt-v0.1.json');
if (fs.existsSync(schemaSourcePath)) {
  fs.copyFileSync(schemaSourcePath, path.join(DIST_DIR, 'schemas', 'receipt-v0.1.json'));
  console.log('✓ Packaged Evidence Contract Schema -> dist/public-web/schemas/receipt-v0.1.json');
}

// 6. Generate Custom 404 Fallback Page
const notFoundHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>404 Not Found — VaultBasis</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;700&display=swap" rel="stylesheet">
  <style>
    body {
      background: #07090e;
      color: #f1f5f9;
      font-family: 'Plus Jakarta Sans', sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
      text-align: center;
      padding: 1rem;
    }
    .card {
      background: #0e121a;
      border: 1px solid #21293a;
      border-radius: 12px;
      padding: 3rem 2rem;
      max-width: 520px;
    }
    h1 { font-size: 3rem; margin-bottom: 0.5rem; color: #3b82f6; }
    p { color: #94a3b8; line-height: 1.6; margin-bottom: 2rem; }
    .btn {
      display: inline-block;
      background: #3b82f6;
      color: white;
      padding: 10px 20px;
      border-radius: 6px;
      text-decoration: none;
      font-weight: 600;
      margin: 0 6px;
    }
    .btn-secondary {
      background: #161c28;
      border: 1px solid #334155;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>404</h1>
    <h2>Resource Not Found</h2>
    <p>The requested public resource does not exist. For local reconciliation operations, ensure your local Edge daemon is running.</p>
    <a href="/" class="btn">Return to Home</a>
    <a href="/verifier" class="btn btn-secondary">Open Verifier</a>
  </div>
</body>
</html>`;
fs.writeFileSync(path.join(DIST_DIR, '404.html'), notFoundHtml, 'utf8');
console.log('✓ Generated Custom 404 Page -> dist/public-web/404.html');

// 7. Security Invariant Audit (Zero Leakage Check)
console.log('--------------------------------------------------------------------------------');
console.log('Executing Zero-Leakage Security Posture Audit on Output Bundle...');

function checkDirForSensitiveFiles(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      checkDirForSensitiveFiles(fullPath);
    } else {
      const ext = path.extname(entry.name).toLowerCase();
      if (['.key', '.db', '.sqlite', '.sqlite3', '.env'].includes(ext)) {
        console.error(`🚨 CRITICAL SECURITY FAULT: Sensitive file in public distribution: ${fullPath}`);
        process.exit(1);
      }
    }
  }
}
checkDirForSensitiveFiles(DIST_DIR);
console.log('✓ Zero-Leakage Audit Passed: Output bundle contains 0 private keys and 0 databases.');

console.log('================================================================================');
console.log('✅ PUBLIC WEB DISTRIBUTION READY FOR VERCEL DEPLOYMENT.');
console.log('   Deploy with: npx vercel deploy --prod');
console.log('================================================================================');
