const { test, expect } = require('@playwright/test');
const fs = require('fs');
const axe = fs.readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
const pages = ['/', '/trust-assurance', '/about', '/contact', '/verifier-access', '/privacy-policy', '/terms-of-service', '/security-disclosure', '/faq', '/docs/scope_and_limitations_v0.1.html'];
async function checkA11y(page) {
  await page.addScriptTag({ content: axe });
  const results = await page.evaluate(async () => (await axe.run(document, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'] },
  })).violations.filter(v => ['serious', 'critical'].includes(v.impact)));
  expect(results.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) }))).toEqual([]);
}
async function assertFocusContained(page) {
  // Check the starting state too: the next Tab can re-enter an already
  // escaped dialog and otherwise conceal the broken containment.
  expect(await page.evaluate(() => !!document.activeElement.closest('#access-modal'))).toBe(true);
  for (let i = 0; i < 12; i++) {
    await page.keyboard.press('Tab');
    expect(await page.evaluate(() => !!document.activeElement.closest('#access-modal'))).toBe(true);
  }
  for (let i = 0; i < 12; i++) {
    await page.keyboard.press('Shift+Tab');
    expect(await page.evaluate(() => !!document.activeElement.closest('#access-modal'))).toBe(true);
  }
}
async function assertNotFound(response) {
  expect(response.status()).toBe(404);
  expect(await response.text()).toContain('We couldn’t find that page.');
}

for (const width of [1440, 1280, 768, 390, 320]) {
  test(`public pages: navigation shell, reflow, a11y at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    for (const route of pages) {
      const response = await page.goto(route);
      expect(response.status()).toBe(200);
      await expect(page.locator('header')).toHaveCount(1);
      await expect(page.locator('footer')).toHaveCount(1);
      expect(await page.locator('#main-nav a').allTextContents()).toEqual(['How It Works', 'Trust Center', 'About']);
      await expect(page.locator('.page-nav-strip')).toHaveCount(0);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      await checkA11y(page);
    }
    expect(errors).toEqual([]);
  });
}

test('dialog contains focus, validates, preserves input, and restores exact invoker', async ({ page }) => {
  await page.goto('/');
  const invoke = page.locator('header').getByRole('button', { name: 'Request Access', exact: true });
  await invoke.click();
  await expect(page.locator('#req-name')).toBeFocused();
  await assertFocusContained(page);
  await page.getByRole('button', { name: 'Submit Request', exact: true }).click();
  await expect(page.locator('#req-name')).toBeFocused();
  await expect(page.locator('#req-name')).toHaveAttribute('aria-invalid', 'true');
  await checkA11y(page);
  await page.locator('#req-name').fill('Synthetic Reviewer');
  await page.keyboard.press('Escape');
  await expect(invoke).toBeFocused();
  await invoke.click();
  await expect(page.locator('#req-name')).toHaveValue('Synthetic Reviewer');
  await page.getByRole('button', { name: 'Close Request Access', exact: true }).click();
  await expect(invoke).toBeFocused();
});

test('request working, failure, retry and response states never imply delivery', async ({ page }) => {
  let requests = 0;
  await page.route('**/api/request-access', async route => {
    requests++;
    await new Promise(resolve => setTimeout(resolve, 150));
    await route.fulfill({ status: requests === 1 ? 503 : 202, contentType: 'application/json', body: JSON.stringify({ status: 'pending_review' }) });
  });
  await page.goto('/');
  await page.locator('header').getByRole('button', { name: 'Request Access', exact: true }).click();
  await page.locator('#req-name').fill('Synthetic Reviewer');
  await page.locator('#req-email').fill('reviewer@example.invalid');
  const button = page.locator('#btn-submit-req');
  await button.click();
  await expect(button).toBeDisabled();
  await expect(page.locator('#request-status')).toContainText('temporarily unavailable');
  await expect(button).toBeEnabled();
  await button.click();
  await expect(page.locator('#request-success')).toBeVisible();
  await expect(page.locator('#request-status')).toContainText('Pending review and manual provisioning');
  await expect(page.locator('#request-success-title')).toBeFocused();
  await assertFocusContained(page);
  expect(requests).toBe(2);
  await checkA11y(page);
});

test('mobile navigation, fragment history and reduced-motion top control', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  await page.getByRole('button', { name: 'Open navigation', exact: true }).click();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('button', { name: 'Open navigation', exact: true })).toBeFocused();
  await page.getByRole('button', { name: 'Open navigation', exact: true }).click();
  const invoke = page.locator('header').getByRole('button', { name: 'Request Access', exact: true });
  await invoke.click();
  await page.getByRole('button', { name: 'Close Request Access', exact: true }).click();
  await expect(invoke).toBeFocused();
  await page.locator('#main-nav').getByRole('link', { name: 'How It Works', exact: true }).click();
  await expect(page).toHaveURL(/#how-it-works$/);
  await page.reload();
  await expect(page.locator('#how-it-works')).toBeInViewport();
  await page.evaluate(() => scrollTo(0, document.body.scrollHeight));
  await page.getByRole('button', { name: 'Back to top', exact: true }).click();
  await expect(page.locator('main')).toBeFocused();
  expect(await page.evaluate(() => scrollY)).toBe(0);
});

test('unknown paths return real 404; recovery works; gate stays server-side', async ({ page, request }) => {
  for (const route of ['/definitely-not-a-vaultbasis-route', '/unknown/nested/path', '/about-does-not-exist']) await assertNotFound(await request.get(route));
  const response = await page.goto('/definitely-not-a-vaultbasis-route');
  expect(response.status()).toBe(404);
  await checkA11y(page);
  await page.getByRole('link', { name: 'Return to Home', exact: true }).click();
  await expect(page).toHaveURL(/\/$/);
  await page.goto('/verifier');
  await expect(page).toHaveURL(/\/verifier-access\?next=/);
});

test('negative control: soft-404 assertion rejects Home/200', async ({ request }) => {
  await expect(assertNotFound(await request.get('/'))).rejects.toThrow();
});
test('generated public destinations and fragments resolve; missing-link control fails', async ({ page, request, baseURL }) => {
  const destinations = new Set();
  for (const route of pages) {
    await page.goto(route);
    for (const href of await page.locator('a[href]').evaluateAll(nodes => nodes.map(n => n.href))) {
      if (href.startsWith(baseURL)) destinations.add(href);
    }
  }
  async function checkDestination(href) {
    const url = new URL(href);
    const response = await request.get(url.pathname + url.search);
    expect(response.status(), href).toBeLessThan(400);
    if (url.hash) expect(await response.text(), href).toContain(`id="${decodeURIComponent(url.hash.slice(1))}"`);
  }
  for (const href of destinations) await checkDestination(href);
  await expect(checkDestination(baseURL + '/deliberately-dead-link')).rejects.toThrow();
});
test('negative control: keyboard contract rejects a non-modal dialog', async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => { const d = document.getElementById('access-modal'); d.show(); document.querySelector('header a').focus(); });
  await expect(assertFocusContained(page)).rejects.toThrow();
});
test('negative control: axe detects a missing dialog name', async ({ page }) => {
  await page.goto('/');
  await page.locator('header').getByRole('button', { name: 'Request Access', exact: true }).click();
  await page.locator('#access-modal').evaluate(d => d.removeAttribute('aria-labelledby'));
  await page.addScriptTag({ content: axe });
  const result = await page.evaluate(async () => (await axe.run(document, { runOnly: ['aria-dialog-name'] })).violations.map(v => v.id));
  expect(result).toContain('aria-dialog-name');
});
