const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: './tests/browser',
  timeout: 30000,
  workers: 1,
  reporter: [['list'], ['json', { outputFile: 'test-results/ux-results.json' }]],
  use: { baseURL: process.env.VB_PREVIEW_URL || 'http://127.0.0.1:3187', trace: 'retain-on-failure' },
  projects: ['chromium', 'firefox', 'webkit'].map(browserName => ({
    name: browserName, use: { browserName },
  })),
  webServer: process.env.VB_PREVIEW_URL ? undefined : {
    command: 'PORT=3187 node scripts/serve_public_web_local.js',
    url: 'http://127.0.0.1:3187', reuseExistingServer: false,
  },
});
