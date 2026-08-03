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
  await page.addInitScript(() => {
    window.__spokenInterviewQuestions = [];
    window.__playedInterviewAudio = [];
    const nativeSpeak = window.speechSynthesis.speak.bind(window.speechSynthesis);
    window.speechSynthesis.speak = (utterance) => {
      window.__spokenInterviewQuestions.push({ text: utterance.text, rate: utterance.rate });
      return nativeSpeak(utterance);
    };
    const nativeMediaPlay = window.HTMLMediaElement.prototype.play;
    window.HTMLMediaElement.prototype.play = function play() {
      window.__playedInterviewAudio.push({ src: this.src, rate: this.playbackRate });
      return nativeMediaPlay.call(this);
    };
    window.SpeechRecognition = class MockSpeechRecognition {
      start() {
        this.onstart?.();
        const result = [{ transcript: "My research focuses on mass spectrometry based proteomics and protein lactylation." }];
        result.isFinal = true;
        window.setTimeout(() => this.onresult?.({ resultIndex: 0, results: [result] }), 20);
      }
      stop() {
        this.onend?.();
      }
    };
  });
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  page.on("pageerror", (error) => errors.push(`pageerror: ${error.message}`));

  await page.goto(`${baseUrl}/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1_200);
  await page.waitForLoadState("networkidle");

  if ((await page.locator("#paperCount").textContent()) !== "373") throw new Error("paper count mismatch");
  if (!(await page.locator("#newItemsHint").textContent()).includes("15")) throw new Error("daily plan missing");
  await page.waitForTimeout(350);
  await page.screenshot({ path: path.join(out, "01-home-mobile.png") });

  await page.click('.bottom-nav [data-go="interview"]');
  if ((await page.locator("[data-interview-rate]").count()) !== 3) throw new Error("interview speed choices missing");
  if ((await page.locator("#interviewVoiceSelect option").count()) < 1) throw new Error("interview voice selector missing");
  await page.click('[data-interview-rate="0.5"]');
  await page.screenshot({ path: path.join(out, "07-interview-setup.png"), fullPage: true });
  await page.click("#interviewStartButton");
  await page.locator("#interviewSession").waitFor({ state: "visible" });
  await page.waitForTimeout(500);
  if (!(await page.locator("#interviewQuestionText").isHidden())) throw new Error("interview question should start hidden");
  const playedAudio = await page.evaluate(() => window.__playedInterviewAudio);
  if (!playedAudio.length || !playedAudio[0].src.includes("introduction.mp3")) throw new Error("bundled male interview audio did not play");
  if (Math.abs(playedAudio[0].rate - 0.5) > 0.01) throw new Error("interview did not use the selected 0.5 speed");
  if ((await page.locator("#interviewSessionRateSelect").inputValue()) !== "0.5") throw new Error("session speed did not stay in sync");
  await page.selectOption("#interviewSessionRateSelect", "1");
  await page.click("#interviewRepeatButton");
  await page.waitForTimeout(100);
  const replayRate = await page.evaluate(() => window.__playedInterviewAudio.at(-1).rate);
  if (Math.abs(replayRate - 1) > 0.01) throw new Error("interview did not switch to 1.0 speed");
  await page.click("#interviewShowTextButton");
  if (!(await page.locator("#interviewQuestionText").isVisible())) throw new Error("interview transcript did not reveal");
  await page.click("#interviewMicButton");
  await page.waitForFunction(() => document.getElementById("interviewAnswerInput").value.includes("mass spectrometry"));
  await page.click("#interviewMicButton");
  await page.click("#interviewSubmitButton");
  if (!(await page.locator("#interviewQuestionNumber").textContent()).includes("Question 2")) throw new Error("interview did not advance");
  await page.waitForTimeout(350);
  await page.screenshot({ path: path.join(out, "08-interview-mobile.png"), fullPage: true });
  for (let index = 1; index < 24 && await page.locator("#interviewResult").isHidden(); index += 1) {
    await page.fill("#interviewAnswerInput", "I would like to explain my experience and discuss a focused research project with your group.");
    await page.click("#interviewSubmitButton");
  }
  await page.locator("#interviewResult").waitFor({ state: "visible" });
  if ((await page.locator("#interviewSentenceList li").count()) !== 5) throw new Error("interview review did not provide five sentences");
  if ((await page.locator("#interviewMisunderstoodList li").count()) < 1) throw new Error("interview listening support was not recorded");
  await page.screenshot({ path: path.join(out, "09-interview-result.png"), fullPage: true });
  await page.click('.bottom-nav [data-go="home"]');

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
  const interviewAudio = await page.request.get(`${baseUrl}/audio/interview/introduction.mp3`);
  if (!interviewAudio.ok() || (await interviewAudio.body()).length < 1_000) throw new Error("bundled male interview audio missing");

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
  console.log(JSON.stringify({ ok: true, screenshots: 9, items: payload.items.length }, null, 2));
})().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
