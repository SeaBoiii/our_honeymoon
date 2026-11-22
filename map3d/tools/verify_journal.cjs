/* Serve docs, then run with playwright-core on NODE_PATH. Accepts the same browser
   and site environment variables as verify_playback.cjs. */
const assert = require("node:assert/strict");
const { chromium } = require("playwright-core");
const base =
  (process.env.ATLAS_URL || "http://127.0.0.1:8796").replace(/\/$/, "") + "/";

async function checkLayout(page, width) {
  await page.setViewportSize({ width, height: 844 });
  await page.goto(base);
  await page.evaluate(() => document.fonts.ready);
  const layout = await page.evaluate(() => ({
    days: document.querySelectorAll(".chapter").length,
    choices: document.querySelector("#day-picker").length,
    first: document.querySelector("main > section").id,
    dayTop: Math.round(
      document.querySelector("#days").getBoundingClientRect().top,
    ),
    overflow: document.documentElement.scrollWidth - innerWidth,
    tablesFit: [...document.querySelectorAll(".tablewrap")].every(
      (t) => t.scrollWidth <= t.clientWidth + 1,
    ),
    brokenAnchors: [...document.querySelectorAll('a[href^="#"]')]
      .map((a) => a.getAttribute("href"))
      .filter((hash) => !document.getElementById(hash.slice(1))),
  }));
  assert.equal(layout.days, 15);
  assert.equal(layout.choices, layout.days);
  const scenes = page.locator(".chapter-head img");
  assert.equal(await scenes.count(), 5);
  for (const image of await scenes.all()) {
    await image.scrollIntoViewIfNeeded();
    await page.waitForFunction(
      (src) =>
        Array.from(document.images).some(
          (img) => img.getAttribute("src") === src && img.naturalWidth === 900,
        ),
      await image.getAttribute("src"),
    );
  }
  assert.equal(layout.first, "days");
  assert.equal(layout.overflow, 0);
  assert.equal(layout.tablesFit, true);
  assert.deepEqual(layout.brokenAnchors, []);
  await page.locator(".atlas-btn").click();
  const picker = page.locator("#day-picker");
  if (width <= 760) {
    await picker.selectOption("#trip-day-11");
    assert.ok(
      await page
        .locator("#trip-day-11")
        .evaluate((el) => el === document.activeElement),
    );
  } else {
    await page.locator('.day-index a[href="#trip-day-11"]').focus();
    await page.keyboard.press("Enter");
  }
  await page.waitForFunction(
    () =>
      document.querySelector(".day-index a[aria-current]")?.hash ===
      "#trip-day-11",
  );
  await page.locator("#trip-day-2 summary").click();
  assert.ok(
    await page.locator("#trip-day-2 details").evaluate((el) => el.open),
  );
  const check = page.locator("#c4");
  await check.check();
  await page.reload();
  assert.ok(await check.isChecked());
  console.log(
    width +
      "px: " +
      layout.days +
      " chapters, day index begins at " +
      layout.dayTop +
      "px",
  );
}

async function checkReturn(page, edition, day, query = "") {
  if (edition === "3d" && !query) {
    await page.goto(base + "#trip-day-" + day);
    await page.locator("#trip-day-" + day + " a[href$='#day-" + day + "']").click();
  } else {
    await page.goto(base + edition + "/" + query + "#day-" + day);
  }
  const back = page.locator("#journal-back");
  await page.waitForFunction(
    (d) => document.getElementById("journal-back")?.hash === "#trip-day-" + d,
    day,
    { timeout: 90000 },
  );
  const otherMode = await page.locator("#tour-switch").getAttribute("href");
  assert.equal(new URL(otherMode).hash, "#day-" + day);
  const more=page.locator('#options-toggle');
  if(await more.isVisible()) await more.click();
  await back.click();
  await page.waitForFunction(
    (d) =>
      location.hash === "#trip-day-" + d &&
      document.getElementById("day-picker")?.value === location.hash,
    day,
  );
  assert.equal(new URL(page.url()).pathname, new URL(base).pathname);
}

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH,
    args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
  });
  try {
    const page = await browser.newPage({ reducedMotion: "reduce" });
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    for (const width of [320, 390, 768, 1440]) await checkLayout(page, width);
    await page.setViewportSize({ width: 390, height: 844 });
    for (const edition of ["3d", "claude-cut"]) {
      await checkReturn(page, edition, 6);
      await checkReturn(page, edition, 0, "?tour=drive");
    }
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto(base + "#guide");
    assert.equal(await page.locator("#guide h2").innerText(), "Trip guide");
    const plain = await browser.newPage({
      javaScriptEnabled: false,
      viewport: { width: 390, height: 844 },
    });
    await plain.goto(base);
    await plain.locator('.day-index a[href="#trip-day-2"]').click();
    assert.equal(new URL(plain.url()).hash, "#trip-day-2");
    assert.deepEqual(errors, []);
    console.log(
      "Both map editions return to the written day in each tour. The day index also works without JavaScript.",
    );
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
