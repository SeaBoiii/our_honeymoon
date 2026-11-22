const assert = require('node:assert/strict');
const { chromium } = require('playwright-core');
const base =
  (process.env.ATLAS_URL || 'http://127.0.0.1:8796').replace(/\/$/, '') + '/';

async function run() {
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH,
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });
  try {
    const page = await browser.newPage({
      viewport: { width: 390, height: 844 },
      reducedMotion: 'reduce',
    });
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    page.on('console', (m) => {
      if (m.type() === 'error') errors.push(m.text());
    });
    await page.goto(base);
    const activities = await page
      .locator('.activity-link')
      .evaluateAll((links) =>
        links.map((a) => ({
          hash: a.hash,
          day: Number(a.closest('article').id.slice(9)),
        })),
      );
    const stops = await page
      .locator('.map-stop')
      .evaluateAll((links) => links.map((a) => a.getAttribute('href')));
    assert.equal(stops.length, 9);
    for (const hash of stops) {
      await page.locator('.map-stop[href="' + hash + '"]').click();
      assert.equal(new URL(page.url()).hash, hash);
      assert.ok(await page.locator(hash).isVisible());
    }
    await page.locator('.map-stop[href="#base-queenstown"]').focus();
    await page.keyboard.press('Enter');
    const choices = page.locator('#base-queenstown li a');
    assert.deepEqual(
      await choices.evaluateAll((nodes) => nodes.map((a) => a.hash)),
      ['#trip-day-7', '#trip-day-8', '#trip-day-9'],
    );
    await choices.nth(1).click();
    assert.equal(new URL(page.url()).hash, '#trip-day-8');
    for (const edition of ['3d', 'claude-cut']) {
      await page.route(
        (url) => url.pathname.endsWith('/' + edition + '/'),
        async (route) => {
          const response = await route.fetch();
          const source = (await response.text()).replace(
            '  buildTimeline();',
            `  buildTimeline();
          window.sceneAudit=()=>({id:legs[curLeg]?.id,days:legs.length,day:curDay,night,follow,playing});`,
          );
          await route.fulfill({
            contentType: 'text/html; charset=utf-8',
            body: source,
          });
        },
      );
      await page.goto(base + edition + '/#scene-tekapo-chapel');
      await page.waitForFunction(
        () => window.sceneAudit?.().id === 'tekapo-chapel',
        null,
        { timeout: 90000 },
      );
      assert.equal(await page.locator('#journal-back').isVisible(), false);
      const pickerIds = await page.locator('#activity-picker option').evaluateAll(
        (options) => options.map((option) => option.value),
      );
      for (const { hash, day } of activities) {
        assert.ok(pickerIds.includes(hash.slice(7)), hash + ' missing from More');
        await page.evaluate((h) => {
          location.hash = h;
        }, hash);
        await page.waitForFunction(
          ({ hash, day }) =>
            window.sceneAudit().id === hash.slice(7) &&
            window.sceneAudit().day === day,
          { hash, day },
          { timeout: 12000 },
        );
        assert.equal(
          new URL(
            await page.locator('#journal-back').getAttribute('href'),
            page.url(),
          ).hash,
          '#trip-day-' + day,
        );
        assert.equal(await page.evaluate(() => sceneAudit().playing), false);
        if (hash === '#scene-mount-john')
          assert.ok(await page.evaluate(() => sceneAudit().night > 0.8));
        if (hash === '#scene-wanaka-tree' || hash === '#scene-onsen-sunset') {
          await page.waitForFunction(
            (h) => document.querySelector('#c').dataset.evening === h.slice(7),
            hash,
          );
        }
      }
      await page.locator('#toggle').click();
      await page.locator('#days button[data-day="8"]').click();
      assert.equal(
        await page.locator('#toggle').getAttribute('aria-expanded'),
        'false',
      );
      await page.locator('#options-toggle').click();
      await page.locator('#activity-picker').selectOption('mount-john');
      await page.waitForFunction(() => window.sceneAudit().id === 'mount-john');
      await page.locator('#options-toggle').click();
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#map-options').isVisible(), false);
      assert.ok(
        await page
          .locator('#options-toggle')
          .evaluate((b) => document.activeElement === b),
      );
      await page.setViewportSize({ width: 1280, height: 820 });
      await page.locator('#side #journal-back').waitFor({ state: 'visible' });
      assert.ok(await page.locator('#bar #speed').isVisible());
      await page.setViewportSize({ width: 390, height: 844 });
      await page.locator('#options-toggle').click();
      await page.locator('#tour-switch').click();
      await page.waitForFunction(
        () => window.sceneAudit?.().days === 39,
        null,
        { timeout: 90000 },
      );
      await page.evaluate(() => (location.hash = 'scene-onsen-sunset'));
      await page.waitForFunction(
        () => window.sceneAudit?.().id === 'onsen-sunset',
        null,
        { timeout: 90000 },
      );
      await page.locator('#options-toggle').click();
      await page.locator('#journal-back').click();
      assert.equal(new URL(page.url()).hash, '#trip-day-8');
      console.log(
        edition +
          ': ' +
          activities.length +
          ' journal activity links, evening models, mobile/desktop controls and full-tour handoff passed.',
      );
    }
    assert.deepEqual(errors, []);
    console.log('Nine map pins and all three Queenstown day choices passed.');
  } finally {
    await browser.close();
  }
}
run().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
