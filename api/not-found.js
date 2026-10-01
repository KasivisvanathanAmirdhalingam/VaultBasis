'use strict';
const fs = require('fs');
const path = require('path');
// Unmatched routes must never become Home/200, even if the error artifact fails.
module.exports = (_req, res) => {
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  try {
    return res.status(404).send(fs.readFileSync(path.join(__dirname, '..', 'dist', 'public-web', '404.html'), 'utf8'));
  } catch (_) {
    return res.status(404).send('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Page not found — VaultBasis</title><main><h1>Page not found</h1><p>The requested page is unavailable.</p><a href="/">Return to Home</a></main></html>');
  }
};
