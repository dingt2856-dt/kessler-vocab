const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

(async () => {
  const baseUrl = process.env.KESSLER_APP_URL || "http://127.0.0.1:8765";
  const output = path.join(__dirname, "screenshots");
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, locale: "zh-CN" });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });

  await page.goto(`${baseUrl}/self-introduction/`, { waitUntil: "networkidle" });
  if ((await page.locator(".word-unit").count()) !== 332) throw new Error("word count mismatch");
  if ((await page.locator(".word-ipa:empty").count()) !== 0) throw new Error("missing IPA");
  if ((await page.locator(".paragraph-card").count()) !== 10) throw new Error("paragraph count mismatch");
  if (!(await page.locator(".badge").first().textContent()).includes("Ryan")) throw new Error("male voice label missing");
  if (await page.evaluate(() => document.getElementById("audio").playbackRate) !== 0.75) throw new Error("default rate mismatch");

  await page.screenshot({ path: path.join(output, "10-self-introduction-top.png"), fullPage: false });
  await page.click('[data-rate="0.5"]');
  if (await page.evaluate(() => document.getElementById("audio").playbackRate) !== 0.5) throw new Error("rate control failed");
  const response = await page.request.get(`${baseUrl}/self-introduction/self-introduction.mp3`);
  if (!response.ok() || (await response.body()).length < 700_000) throw new Error("audio missing or incomplete");
  const data = await (await page.request.get(`${baseUrl}/self-introduction/self-introduction.json`)).json();
  if (data.voice !== "en-GB-RyanNeural" || data.wordCount !== 332) throw new Error("metadata mismatch");

  await page.locator('.paragraph-card[data-paragraph="3"]').scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(output, "11-self-introduction-words.png"), fullPage: false });
  await browser.close();
  if (errors.length) throw new Error(errors.join("\n"));
  console.log(JSON.stringify({ ok: true, words: 332, voice: data.voice, screenshots: 2 }, null, 2));
})().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
