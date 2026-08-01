const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

(async () => {
  const baseUrl = process.env.KESSLER_APP_URL || "http://127.0.0.1:8765";
  const out = path.join(__dirname, "screenshots");
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  });
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 1,
    locale: "zh-CN",
    permissions: [],
  });
  const page = await context.newPage();
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  page.on("pageerror", (error) => errors.push(`pageerror: ${error.message}`));

  await page.goto(`${baseUrl}/`, { waitUntil: "networkidle" });
  await page.evaluate(() => localStorage.clear());
  await page.reload({ waitUntil: "networkidle" });

  if ((await page.locator("#paperCount").textContent()) !== "373") throw new Error("paper count mismatch");
  if (!(await page.locator("#newItemsHint").textContent()).includes("15")) throw new Error("daily plan missing");
  await page.waitForTimeout(350);
  await page.screenshot({ path: path.join(out, "01-home-mobile.png") });

  await page.click("#startTodayButton");
  await page.locator("#cardTerm").waitFor({ state: "visible" });
  if ((await page.locator("#sessionCounter").textContent()).trim() !== "1 / 15") throw new Error("session queue mismatch");
  await page.waitForTimeout(350);
  await page.screenshot({ path: path.join(out, "02-learning-card.png") });

  await page.click("#revealButton");
  if (!(await page.locator("#cardAnswer").isVisible())) throw new Error("answer did not reveal");
  await page.waitForTimeout(350);
  await page.screenshot({ path: path.join(out, "03-learning-answer.png"), fullPage: true });
  await page.click('[data-rating="good"]');
  if ((await page.locator("#sessionCounter").textContent()).trim() !== "2 / 15") throw new Error("rating did not advance");

  await page.click('.bottom-nav [data-go="library"]');
  await page.locator(".library-item").first().waitFor({ state: "visible" });
  if ((await page.locator(".library-item").count()) !== 50) throw new Error("library pagination mismatch");
  await page.waitForTimeout(350);
  await page.screenshot({ path: path.join(out, "04-library.png") });

  await page.fill("#librarySearch", "ubiquitin");
  if ((await page.locator(".library-item").count()) < 1) throw new Error("library search failed");
  await page.fill("#librarySearch", "");

  await page.click('.bottom-nav [data-go="stats"]');
  if ((await page.locator("#seenCount").textContent()).trim() !== "1") throw new Error("stats did not update");
  await page.waitForTimeout(350);
  await page.screenshot({ path: path.join(out, "05-stats.png") });

  await page.click('.bottom-nav [data-go="settings"]');
  await page.waitForTimeout(350);
  await page.screenshot({ path: path.join(out, "06-settings.png") });
  const manifest = await page.request.get(`${baseUrl}/manifest.webmanifest`);
  if (!manifest.ok()) throw new Error("manifest missing");
  const data = await page.request.get(`${baseUrl}/data/learning_items.json`);
  const payload = await data.json();
  if (payload.items.length !== 300) throw new Error("learning item count mismatch");

  const serviceWorkerControlled = await page.evaluate(async () => {
    if (!("serviceWorker" in navigator)) return false;
    await navigator.serviceWorker.ready;
    return Boolean(navigator.serviceWorker.controller || (await navigator.serviceWorker.getRegistration()));
  });
  if (!serviceWorkerControlled) errors.push("service worker not controlling page during test");

  await page.click('.bottom-nav [data-go="home"]');
  await context.setOffline(true);
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.locator("#paperCount").waitFor({ state: "visible" });
  if ((await page.locator("#paperCount").textContent()) !== "373") errors.push("offline reload lost learning data");
  await context.setOffline(false);

  await browser.close();
  if (errors.length) {
    console.error(JSON.stringify({ ok: false, errors }, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify({ ok: true, screenshots: 6, items: payload.items.length }, null, 2));
})().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
