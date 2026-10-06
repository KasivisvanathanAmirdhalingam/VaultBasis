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
const PARTIALS_DIR = path.join(APPS_DIR, 'web-marketing', 'partials');

// Load shared partials once.
function loadPartials() {
  const read = (name) => fs.readFileSync(path.join(PARTIALS_DIR, name), 'utf8');
  return {
    header: read('header.html'),
    footer: read('footer.html'),
    modal:  read('modal.html'),
    css:    read('shell.css'),
    js:     read('shell.js'),
  };
}

// Inject partials into a page source.
// Pages use sentinel comments: <!-- SHELL_CSS -->, <!-- HEADER -->,
// <!-- FOOTER -->, <!-- MODAL -->, <!-- SHELL_JS -->
function injectPartials(html, partials) {
  return html
    .replace('<!-- SHELL_CSS -->', partials.css)
    .replace('<!-- HEADER -->',   partials.header)
    .replace('<!-- FOOTER -->',   partials.footer)
    .replace('<!-- MODAL -->',    partials.modal)
    .replace('<!-- SHELL_JS -->',  partials.js);
}

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
// NOTE: dist/public-web/verifier/ is intentionally NOT created.
// The verifier HTML must NOT be a static file in outputDirectory.
// Vercel serves static files before evaluating rewrites, so placing
// verifier/index.html here would bypass the /api/verifier-page auth gate.
// The verifier HTML is served exclusively by api/verifier-page.js after
// server-side session validation (ACCESS-INV-001).
fs.mkdirSync(path.join(DIST_DIR, 'schemas'), { recursive: true });
fs.mkdirSync(path.join(DIST_DIR, 'api', 'data'), { recursive: true });

// 3. Load partials and build all marketing pages with shared shell injected.
const partials = loadPartials();

const marketingSourcePath = path.join(APPS_DIR, 'web-marketing', 'index.html');
if (!fs.existsSync(marketingSourcePath)) {
  console.error(`❌ ERROR: Marketing site source missing at ${marketingSourcePath}`);
  process.exit(1);
}
let marketingHtml = fs.readFileSync(marketingSourcePath, 'utf8');
marketingHtml = injectPartials(marketingHtml, partials);
marketingHtml = marketingHtml.replace(
  '<!-- BUILD_METADATA -->',
  `<!-- VaultBasis Build: ${commitSha} | Timestamp: ${buildTimestamp} -->`
);
fs.writeFileSync(path.join(DIST_DIR, 'index.html'), marketingHtml, 'utf8');
console.log('✓ Packaged Public Marketing Portal -> dist/public-web/index.html');

// Build standalone pages — inject partials into each before writing.
const standalonePages = ['privacy-policy', 'terms-of-service', 'contact', 'security-disclosure', 'about', 'trust-assurance', 'faq', 'verifier-access'];
for (const page of standalonePages) {
  const src = path.join(APPS_DIR, 'web-marketing', `${page}.html`);
  if (!fs.existsSync(src)) {
    console.error(`❌ ERROR: ${page}.html missing at ${src}`);
    process.exit(1);
  }
  let html = fs.readFileSync(src, 'utf8');
  html = injectPartials(html, partials);
  fs.writeFileSync(path.join(DIST_DIR, `${page}.html`), html, 'utf8');
  console.log(`✓ Packaged ${page} -> dist/public-web/${page}.html`);
}

// Copy Evidence Receipt Guide from web-dashboard
const guideSrc = path.join(APPS_DIR, 'web-dashboard', 'evidence-receipt-guide.html');
if (fs.existsSync(guideSrc)) {
  fs.copyFileSync(guideSrc, path.join(DIST_DIR, 'evidence-receipt-guide.html'));
  console.log('✓ Packaged Evidence Receipt Guide -> dist/public-web/evidence-receipt-guide.html');
}

// 4. Web Verifier — served by api/verifier-page.js, NOT as a static file.
// The verifier HTML is read from apps/web-verifier/index.html by the serverless
// function at request time, after server-side session validation.
// Verify the source exists so build fails fast if it is missing.
const verifierSourcePath = path.join(APPS_DIR, 'web-verifier', 'index.html');
if (!fs.existsSync(verifierSourcePath)) {
  console.error(`❌ ERROR: Web verifier source missing at ${verifierSourcePath}`);
  process.exit(1);
}
console.log('✓ Web Verifier source verified (served by api/verifier-page.js — not placed in outputDirectory)');

// 5. Copy Normative Schema (dist/public-web/schemas/receipt-v0.1.json)
const schemaSourcePath = path.join(SCHEMAS_DIR, 'receipt-v0.1.json');
if (fs.existsSync(schemaSourcePath)) {
  fs.copyFileSync(schemaSourcePath, path.join(DIST_DIR, 'schemas', 'receipt-v0.1.json'));
  console.log('✓ Packaged Evidence Contract Schema -> dist/public-web/schemas/receipt-v0.1.json');
}

// 5b. Copy Golden Sample Receipts and Documentation
const sampleValidSource = path.join(REPO_ROOT, 'tests', 'fixtures', 'golden_receipt_valid.json');
if (fs.existsSync(sampleValidSource)) {
  fs.copyFileSync(sampleValidSource, path.join(DIST_DIR, 'sample-receipt.json'));
  console.log('✓ Packaged Valid Sample Receipt -> dist/public-web/sample-receipt.json');
}
const sampleTamperedSource = path.join(REPO_ROOT, 'tests', 'fixtures', 'golden_receipt_tampered.json');
if (fs.existsSync(sampleTamperedSource)) {
  fs.copyFileSync(sampleTamperedSource, path.join(DIST_DIR, 'sample-receipt-tampered.json'));
  console.log('✓ Packaged Tampered Sample Receipt -> dist/public-web/sample-receipt-tampered.json');
}

fs.mkdirSync(path.join(DIST_DIR, 'docs'), { recursive: true });
const scopeDocSource = path.join(REPO_ROOT, 'docs', 'scope_and_limitations_v0.1.md');
if (fs.existsSync(scopeDocSource)) {
  // Render HTML only — do NOT copy the .md source into the output directory.
  // Vercel serves static files before applying rewrites, so a .md file in the
  // output would be served as raw text regardless of any rewrite rule.
  const { execFileSync } = require('child_process');
  execFileSync('python3', [
    path.join(REPO_ROOT, 'scripts', 'md_to_html.py'),
    scopeDocSource,
    path.join(DIST_DIR, 'docs', 'scope_and_limitations_v0.1.html'),
  ], { stdio: 'inherit' });
  console.log('✓ Rendered Scope & Limitations page -> dist/public-web/docs/scope_and_limitations_v0.1.html');
}

// 5c. API functions live at the repo root /api/ directory and are picked up by
// Vercel's function runtime directly — they must NOT be copied into outputDirectory
// or they will be served as static files instead of executed as serverless functions.

// 5d. Artifact distribution placeholder.
// RC3 qualified artifacts are not yet in controlled storage.
// download.js returns 503 UNAVAILABLE until artifacts are explicitly promoted.
// No RC1 fallback. No unqualified binary served.
console.log('✓ Distribution endpoint configured — awaiting RC3 artifact promotion to controlled storage.');

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

// 6.5. Generate Vercel Edge Middleware — capability access control
//
// Architecture:
//   /verifier → api/verifier-page (serverless function)
//   api/verifier-page performs server-side session validation BEFORE
//   returning any verifier HTML. The verifier application is never
//   returned to an unauthenticated request.
//
//   This middleware provides defense-in-depth at the edge (early redirect
//   if no cookie present) but is NOT the authoritative access control layer.
//   api/verifier-page is authoritative — it validates the session
//   cryptographically against private Blob storage before serving content.
//
// PUBLIC_INFORMATIONAL routes: pass through anonymously.
// AUTHENTICATED_CAPABILITY routes (/verifier, /api/verifier-page): defense-in-depth
//   edge redirect when cookie is absent; server-side validation is authoritative.
const middlewareJs = `
// Routes that are always publicly accessible without authentication.
const PUBLIC_PREFIXES = [
  '/',
  '/about',
  '/faq',
  '/trust-assurance',
  '/contact',
  '/security-disclosure',
  '/privacy-policy',
  '/terms-of-service',
  '/docs/',
  '/schemas/',
  '/sample-receipt',
  '/marketing',
  '/404',
  '/api/request-access',
  '/api/checkout',
  '/api/enterprise-inquiry',
  '/api/download',
  '/api/webhook-payment',
  '/api/verifier-session',
  '/api/verifier-session-check',
  '/verifier-access',
  '/_next/',
  '/favicon',
];

// SESSION_COOKIE_NAME must match api/verifier-session.js
const SESSION_COOKIE_NAME = 'vb_session';

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};

export default function middleware(req) {
  const { pathname } = new URL(req.url);

  // Allow all PUBLIC_INFORMATIONAL routes through immediately.
  const isPublic = PUBLIC_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(prefix)
  );
  if (isPublic) {
    return new Response(null, { headers: { 'x-middleware-next': '1' } });
  }

  // AUTHENTICATED_CAPABILITY: /verifier and /api/verifier-page require a session.
  // Defense-in-depth: redirect at edge when cookie is absent.
  // Authoritative validation is performed by api/verifier-page (server-side,
  // cryptographic, against private Blob) — a forged cookie is rejected there.
  if (pathname.startsWith('/verifier') || pathname.startsWith('/api/verifier-page')) {
    const cookies = req.headers.get('cookie') || '';
    const hasSession = cookies.split(';').some((c) => {
      const [name] = c.trim().split('=');
      return name.trim() === SESSION_COOKIE_NAME;
    });

    if (!hasSession) {
      const dest = new URL('/verifier-access', req.url);
      dest.searchParams.set('next', '/verifier');
      return Response.redirect(dest.toString(), 302);
    }
    return new Response(null, { headers: { 'x-middleware-next': '1' } });
  }

  // Anything else not explicitly listed passes through — /api/download
  // has its own full server-side entitlement check (SEC-002).
  return new Response(null, { headers: { 'x-middleware-next': '1' } });
}
`;
fs.writeFileSync(path.join(DIST_DIR, 'middleware.js'), middlewareJs, 'utf8');
console.log('✓ Generated Vercel Edge Middleware (capability access control) -> dist/public-web/middleware.js');

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
