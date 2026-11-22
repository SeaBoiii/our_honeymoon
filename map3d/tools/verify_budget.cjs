/* Run against built docs using the same Playwright setup as verify_journal.cjs. */
const assert = require('node:assert/strict');
const { chromium } = require('playwright-core');
const base = (process.env.ATLAS_URL || 'http://127.0.0.1:8796').replace(/\/$/, '') + '/';

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({width, height: 850});
      await page.goto(base);
      const entry = page.getByRole('navigation', {name:'Trip navigation'}).getByRole('link', {name:'Budget'});
      assert.ok(await entry.isVisible());
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await entry.click();
      assert.ok(await page.getByRole('heading', {name:'Honeymoon budget'}).isVisible());
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    }
    assert.equal(await page.locator('#cash-left').innerText(), 'S$16,012.20');
    const plan = page.locator('[data-case="plan"]'), high = page.locator('[data-case="high"]');
    assert.equal(await plan.locator('[data-ground]').innerText(), 'S$12,448.16');
    assert.equal(await high.locator('[data-ground]').innerText(), 'S$17,482.48');
    assert.equal(await plan.locator('[data-verdict]').innerText(), 'S$3,564.04 left over');
    assert.equal(await high.locator('[data-verdict]').innerText(), 'S$1,470.28 over budget');
    await page.locator('#settings summary').click();
    await page.locator('#paid').fill('12500.50');
    await page.getByRole('button', {name:'Update budget'}).click();
    assert.equal(await page.locator('#cash-left').innerText(), 'S$17,499.50');
    assert.equal(await plan.locator('[data-total]').innerText(), 'S$24,948.66');
    await page.reload();
    assert.equal(await page.locator('#flight-total').innerText(), 'S$12,500.50');
    await page.locator('#settings summary').click();
    await page.locator('#lodging').fill('6000');
    await page.locator('#cap').fill('26000');
    await page.getByRole('button', {name:'Update budget'}).click();
    assert.equal(await plan.locator('[data-ground]').innerText(), 'S$12,083.16');
    assert.equal(await high.locator('[data-verdict]').innerText(), 'S$2,344.98 over budget');
    assert.ok(await page.locator('#lodging-target').isVisible());
    await page.locator('#settings summary').click();
    await page.getByRole('button', {name:'Restore trip figures'}).click();
    assert.equal(await plan.locator('[data-total]').innerText(), 'S$26,435.96');
    assert.equal(await high.locator('[data-ground]').innerText(), 'S$17,482.48');
    await page.reload();
    assert.equal(await page.locator('#cash-left').innerText(), 'S$16,012.20');
    const staticPage = await browser.newPage({javaScriptEnabled:false, viewport:{width:320,height:800}});
    await staticPage.goto(base + 'budget/');
    assert.ok(await staticPage.locator('noscript p').isVisible());
    assert.equal(await staticPage.locator('[data-case="high"] [data-total]').innerText(), 'S$31,470.28');
    assert.equal(await staticPage.locator('.price-list li').count(), 8);
    assert.deepEqual(errors, []);
    console.log('Budget navigation, four screen sizes, airfare, currency math, saved edits, shortfall and static estimates passed.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
