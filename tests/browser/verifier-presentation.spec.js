const { test, expect } = require('@playwright/test');
const fs = require('fs');
const { renderVerifier } = require('../../api/web-presentation');
const axe = fs.readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
const source = fs.readFileSync('apps/web-verifier/index.html', 'utf8');
test('shared verifier presentation preserves original scripts exactly', async () => {
 const scripts = [...source.matchAll(/<script\b[^>]*>[\s\S]*?<\/script>/g)].map(m => m[0]);
 for (const script of scripts) expect(renderVerifier()).toContain(script);
});
test('verifier keyboard samples, file input, results and mobile reflow', async ({ page }) => {
 // Local presentation qualification only. Live session qualification is separate.
 if (process.env.VB_PREVIEW_URL) test.skip(true, 'Live protected session covered by dedicated runtime qualification');
 await page.route('**/verifier', route => route.fulfill({contentType:'text/html',body:renderVerifier()}));
 await page.route('**/api/verifier-session-check', route => route.fulfill({status:200,body:'{}'}));
 await page.goto('/verifier');
 await expect(page.locator('header')).toHaveCount(1);
 await expect(page.locator('footer')).toHaveCount(1);
 await page.getByRole('button',{name:'Try valid test receipt',exact:true}).click();
 await expect(page.locator('#overall-badge')).toHaveText('PASS (VERIFIED)');
 await expect(page.locator('#results-card')).toContainText('NOT DETERMINED');
 await page.getByRole('button',{name:'Try intentionally tampered receipt',exact:true}).click();
 await expect(page.locator('#overall-badge')).toHaveText('FAIL (TAMPERED / INVALID)');
 await page.locator('#receipt-upload').setInputFiles('tests/fixtures/golden_receipt_valid.json');
 await expect(page.locator('#overall-badge')).toHaveText('PASS (VERIFIED)');
 for(const width of [1440,1280,768,390,320]) {
  await page.setViewportSize({width,height:900});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.addScriptTag({content:axe});
  const failures=await page.evaluate(async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})).violations.filter(v=>['serious','critical'].includes(v.impact)).map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)})));
  expect(failures).toEqual([]);
 }
});
