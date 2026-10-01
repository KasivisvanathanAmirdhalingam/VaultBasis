'use strict';
const fs = require('fs');
const path = require('path');
function renderVerifier() {
  const source = fs.readFileSync(path.join(__dirname, '../apps/web-verifier/index.html'), 'utf8');
  const partial = name => fs.readFileSync(path.join(__dirname, '../apps/web-marketing/partials', name), 'utf8');
  // Only presentation markup is replaced. The original verifier script stays
  // byte-identical and remains the authority for every verification result.
  return source.replace(/<header\b[\s\S]*?<\/header>/, partial('header.html'))
    .replace(/<footer\b[\s\S]*?<\/footer>/, partial('footer.html'))
    .replace('</head>', `<style>${partial('shell.css')} main.container{width:100%;max-width:1000px;min-width:0} .dropzone{overflow-wrap:anywhere} .check-row{gap:1rem;flex-wrap:wrap} #rep-receipt-id{overflow-wrap:anywhere;max-width:100%} #errors-box{color:#991b1b!important}</style></head>`)
    .replace('<main class="container"', '<main id="main-content" tabindex="-1" class="container"')
    .replace(/<h2([^>]*)>Independent Outcome Verification<\/h2>/, '<h1$1>Independent Outcome Verification</h1>')
    .replace('onclick="loadSampleGoldenValid()"', 'onclick="loadPublishedSample(false)"')
    .replace('onclick="loadSampleGoldenTampered()"', 'onclick="loadPublishedSample(true)"')
    .replace('<!-- Results Card -->', '<p id="sample-status" role="status" aria-live="polite"></p><!-- Results Card -->')
    .replace('</body>', `${partial('modal.html')}${partial('shell.js')}
      <script>
      async function loadPublishedSample(tampered) {
        const status = document.getElementById('sample-status');
        status.textContent = 'Loading published test receipt…';
        try {
          const response = await fetch(tampered ? '/sample-receipt-tampered.json' : '/sample-receipt.json');
          if (!response.ok) throw new Error('Sample unavailable');
          const report = await verifyReceiptClientSide(await response.json());
          renderReport(report);
          status.textContent = 'Published test receipt checked. See the verification report.';
        } catch (_) { status.textContent = 'The test receipt could not be loaded. Try again or select a receipt file.'; }
      }
      </script></body>`);
}
module.exports = { renderVerifier };
