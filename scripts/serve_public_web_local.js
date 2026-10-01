'use strict';
const express = require('express');
const path = require('path');
const app = express();
const DIST_DIR = path.join(__dirname, '..', 'dist', 'public-web');
const notFound = require('../api/not-found');

// Local generated-output qualification, not a Vercel runtime substitute.
// Real provisioning is deliberately unavailable here; browser tests intercept
// the request boundary, never send practitioner email or mint entitlements.
app.use(express.json());
app.post('/api/request-access', (_req, res) => res.status(503).json({ error: 'Local provisioning unavailable.' }));
app.get('/verifier', require('../api/verifier-page'));
app.get('/api/verifier-page', require('../api/verifier-page'));
app.get('/marketing', (_req, res) => res.redirect(308, '/'));
app.use(express.static(DIST_DIR, { extensions: ['html'], redirect: true }));
app.use(notFound);

if (require.main === module) {
  const port = Number(process.env.PORT || 3000);
  app.listen(port, '127.0.0.1', () => console.log(`Generated public web: http://127.0.0.1:${port}`));
}
module.exports = app;
