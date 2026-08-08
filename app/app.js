"use strict";

const STORAGE_KEY = "kessler-vocab-progress-v1";
const DAY_MS = 86_400_000;
const DAILY_PLAN_VERSION = 2;
const TYPE_TARGETS = { word: 50, phrase: 3, sentence: 2 };
const TYPE_LABELS = { word: "单词", phrase: "专业短语", sentence: "会议句型" };
const TYPE_LETTERS = { word: "W", phrase: "P", sentence: "S" };
const THEME_LABELS = {
  ubiquitin: "泛素系统",
  protease: "蛋白酶",
  "mass-spec": "质谱",
  proteomics: "蛋白质组",
  "molecular-biology": "分子生物学",
  "cell-biology": "细胞生物学",
  immunology: "免疫学",
  clinical: "疾病与临床",
  "drug-discovery": "靶点发现",
  metabolism: "代谢",
  methods: "实验方法",
  communication: "科研交流",
};

let content = { meta: {}, items: [] };
let itemMap = new Map();
let state = loadState();
let currentView = "home";
let sessionQueue = [];
let sessionIndex = 0;
let sessionKind = "new";
let activeItem = null;
let voices = [];
let deferredInstallPrompt = null;
let mediaRecorder = null;
let recordingChunks = [];
let recordingUrl = "";
let libraryFilter = "all";
let libraryLimit = 50;
let toastTimer = null;

const $ = (id) => document.getElementById(id);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function defaultState() {
  return {
    schemaVersion: 1,
    createdAt: new Date().toISOString(),
    items: {},
    history: [],
    daily: { date: "", newIds: [], completedNewIds: [], planVersion: 0 },
    flags: [],
    settings: { voiceURI: "", slowRate: 0.72 },
    dismissedBackup: false,
  };
}

function loadState() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    if (!parsed || parsed.schemaVersion !== 1 || typeof parsed.items !== "object") return defaultState();
    return { ...defaultState(), ...parsed, settings: { ...defaultState().settings, ...(parsed.settings || {}) } };
  } catch {
    return defaultState();
  }
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function localDateKey(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatToday() {
  return new Intl.DateTimeFormat("zh-CN", { month: "long", day: "numeric", weekday: "short" }).format(new Date());
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function shuffle(values) {
  const result = [...values];
  for (let i = result.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

function showToast(message) {
  const toast = $("toast");
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove("is-visible"), 2300);
}

async function loadContent() {
  const response = await fetch("./data/learning_items.json?v=2026-08-08-1", { cache: "no-cache" });
  if (!response.ok) throw new Error(`学习数据加载失败：${response.status}`);
  content = await response.json();
  itemMap = new Map(content.items.map((item) => [item.id, item]));
  $("paperCount").textContent = content.meta.publicationCount || 373;
  $("appVersion").textContent = content.meta.version || "2026.08.08";
}

function ensureDailyPlan() {
  const today = localDateKey();
  const sameDay = state.daily.date === today && Array.isArray(state.daily.newIds);
  const originalIds = sameDay
    ? state.daily.newIds.filter((id) => itemMap.has(id))
    : [];
  const newIds = [...new Set(originalIds)];
  const selected = new Set(newIds);

  for (const [type, target] of Object.entries(TYPE_TARGETS)) {
    const selectedCount = newIds.filter((id) => itemMap.get(id)?.type === type).length;
    const needed = Math.max(0, target - selectedCount);
    const available = content.items
      .filter((item) => item.type === type && !selected.has(item.id) && !state.items[item.id])
      .sort((a, b) => {
        const priority = Number(a.dailyPriority ?? 1) - Number(b.dailyPriority ?? 1);
        return priority || Number(a.rank ?? 0) - Number(b.rank ?? 0);
      })
      .slice(0, needed)
      .map((item) => item.id);
    newIds.push(...available);
    available.forEach((id) => selected.add(id));
  }

  const completedNewIds = sameDay && Array.isArray(state.daily.completedNewIds)
    ? [...new Set(state.daily.completedNewIds.filter((id) => selected.has(id)))]
    : [];
  const planIsCurrent = sameDay
    && state.daily.planVersion === DAILY_PLAN_VERSION
    && newIds.length === originalIds.length
    && newIds.every((id, index) => id === originalIds[index]);
  if (planIsCurrent) return;

  state.daily = { date: today, newIds, completedNewIds, planVersion: DAILY_PLAN_VERSION };
  saveState();
}

function dueReviewItems(limit = 30) {
  const now = Date.now();
  return Object.entries(state.items)
    .filter(([id, progress]) => itemMap.has(id) && progress.reps > 0 && Number(progress.nextReview || 0) <= now)
    .sort((a, b) => Number(a[1].nextReview || 0) - Number(b[1].nextReview || 0))
    .slice(0, limit)
    .map(([id]) => id);
}

function dailyCounts() {
  const completed = new Set(state.daily.completedNewIds || []);
  const counts = { word: 0, phrase: 0, sentence: 0 };
  for (const id of completed) {
    const item = itemMap.get(id);
    if (item) counts[item.type] += 1;
  }
  return counts;
}

function updateHome() {
  ensureDailyPlan();
  $("todayDate").textContent = formatToday();
  const counts = dailyCounts();
  const totalDone = Object.values(counts).reduce((sum, value) => sum + value, 0);
  const totalTarget = Object.values(TYPE_TARGETS).reduce((sum, value) => sum + value, 0);
  const percent = Math.round((totalDone / totalTarget) * 100);
  $("todayPercent").textContent = `${percent}%`;
  $("progressOrbit").style.strokeDashoffset = String(314.16 * (1 - percent / 100));

  for (const type of Object.keys(TYPE_TARGETS)) {
    $(`${type}Progress`).textContent = counts[type];
    $(`${type}Bar`).style.width = `${Math.min(100, (counts[type] / TYPE_TARGETS[type]) * 100)}%`;
  }

  const pendingNew = state.daily.newIds.filter((id) => !(state.daily.completedNewIds || []).includes(id));
  $("newItemsHint").textContent = pendingNew.length ? `${pendingNew.length}个新内容` : "今日新内容已完成";
  $("dueReviewCount").textContent = dueReviewItems().length;
  $("planStatus").textContent = percent === 100 ? "今日完成" : totalDone ? "进行中" : "尚未开始";
  $("planStatus").style.background = percent === 100 ? "var(--teal-soft)" : "#e9eef3";
  $("planStatus").style.color = percent === 100 ? "#087d78" : "var(--muted)";
  $("backupNotice").hidden = Boolean(state.dismissedBackup);
}

function goView(name) {
  if (name === "learn" && !activeItem) {
    startSession("new");
    return;
  }
  currentView = name;
  $$(".view").forEach((view) => view.classList.toggle("is-active", view.dataset.view === name));
  $$(".bottom-nav button").forEach((button) => button.classList.toggle("is-active", button.dataset.go === name));
  if (name === "home") updateHome();
  if (name === "library") renderLibrary();
  if (name === "stats") renderStats();
  if (name === "settings") renderSettings();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function startSession(kind, ids = null) {
  ensureDailyPlan();
  if (kind === "new") {
    sessionQueue = state.daily.newIds.filter((id) => !(state.daily.completedNewIds || []).includes(id));
    sessionKind = "new";
    $("sessionTitle").textContent = "今日新内容";
  } else if (kind === "review") {
    sessionQueue = dueReviewItems(30);
    sessionKind = "review";
    $("sessionTitle").textContent = "间隔复习";
  } else {
    sessionQueue = ids || [];
    sessionKind = "library";
    $("sessionTitle").textContent = "词库预览";
  }

  if (!sessionQueue.length) {
    showToast(kind === "review" ? "当前没有到期复习项" : "今日新内容已经完成");
    goView("home");
    return;
  }
  sessionIndex = 0;
  activeItem = itemMap.get(sessionQueue[sessionIndex]);
  renderLearningCard();
  currentView = "learn";
  $$(".view").forEach((view) => view.classList.toggle("is-active", view.dataset.view === "learn"));
  $$(".bottom-nav button").forEach((button) => button.classList.toggle("is-active", button.dataset.go === "learn"));
  window.scrollTo({ top: 0 });
}

function renderLearningCard() {
  if (!activeItem) return;
  speechSynthesis.cancel();
  $("sessionCounter").textContent = `${sessionIndex + 1} / ${sessionQueue.length}`;
  $("sessionProgressBar").style.width = `${(sessionIndex / sessionQueue.length) * 100}%`;
  const badge = $("cardTypeBadge");
  badge.textContent = TYPE_LABELS[activeItem.type];
  badge.className = `type-badge ${activeItem.type}-color`;
  $("cardTheme").textContent = THEME_LABELS[activeItem.theme] || activeItem.theme;
  $("cardFrequency").textContent = activeItem.documentFrequency ? `见于${activeItem.documentFrequency}篇` : "会议练习";
  $("cardTerm").textContent = activeItem.displayTerm;
  $("cardTerm").classList.toggle("is-sentence", activeItem.type === "sentence");
  $("cardIpa").textContent = activeItem.ipa || "";
  $("cardIpa").hidden = !activeItem.ipa;
  $("cardSyllables").textContent = activeItem.syllables || "";
  $("cardSyllables").hidden = !activeItem.syllables;
  $("cardChinese").textContent = activeItem.chinese;
  $("cardWordFamily").textContent = (activeItem.wordFamily || []).join(" · ");
  $("wordFamilyBlock").hidden = !(activeItem.wordFamily || []).length;
  $("cardExampleEnglish").textContent = activeItem.exampleEnglish;
  $("cardExampleChinese").textContent = activeItem.exampleChinese;

  const hasPaperSource = activeItem.sourceDoi && activeItem.sourceTitle;
  $("sourceBlock").hidden = !hasPaperSource;
  if (hasPaperSource) {
    $("cardSourceTitle").textContent = activeItem.sourceTitle;
    $("cardSourceDoi").textContent = activeItem.sourceDoi;
    $("cardSourceLink").href = `https://doi.org/${activeItem.sourceDoi}`;
  }

  $("cardAnswer").hidden = true;
  $("revealButton").hidden = false;
  $("revealButton").textContent = "点击显示中文与例句";
  $("ratingPanel").hidden = true;
  $("flagButton").classList.toggle("is-flagged", state.flags.includes(activeItem.id));
  $("flagButton").style.color = state.flags.includes(activeItem.id) ? "var(--coral)" : "";
  resetRecording();
}

function revealAnswer() {
  $("cardAnswer").hidden = false;
  $("revealButton").hidden = true;
  $("ratingPanel").hidden = false;
}

function rateActiveItem(rating) {
  if (!activeItem) return;
  const now = Date.now();
  const previous = state.items[activeItem.id] || {
    reps: 0,
    lapses: 0,
    intervalDays: 0,
    ease: 2.5,
    nextReview: now,
    firstSeen: new Date().toISOString(),
  };
  let intervalDays = Number(previous.intervalDays || 0);
  let ease = Number(previous.ease || 2.5);
  let lapses = Number(previous.lapses || 0);

  if (rating === "again") {
    intervalDays = 10 / (24 * 60);
    ease = Math.max(1.3, ease - 0.2);
    lapses += 1;
  } else if (rating === "hard") {
    intervalDays = previous.reps ? Math.max(1, intervalDays * 1.2) : 1;
    ease = Math.max(1.3, ease - 0.08);
  } else if (rating === "good") {
    intervalDays = previous.reps ? Math.max(2, intervalDays * ease) : 2;
  } else {
    intervalDays = previous.reps ? Math.max(4, intervalDays * (ease + 0.9)) : 4;
    ease = Math.min(3.1, ease + 0.12);
  }

  state.items[activeItem.id] = {
    ...previous,
    reps: Number(previous.reps || 0) + 1,
    lapses,
    intervalDays: Number(intervalDays.toFixed(3)),
    ease: Number(ease.toFixed(2)),
    lastRating: rating,
    lastReviewed: new Date(now).toISOString(),
    nextReview: now + intervalDays * DAY_MS,
  };
  state.history.push({ id: activeItem.id, type: activeItem.type, rating, at: new Date(now).toISOString(), date: localDateKey() });
  if (state.history.length > 5000) state.history = state.history.slice(-5000);

  if (sessionKind === "new" && !state.daily.completedNewIds.includes(activeItem.id)) {
    state.daily.completedNewIds.push(activeItem.id);
  }
  saveState();
  sessionIndex += 1;
  if (sessionIndex >= sessionQueue.length) {
    activeItem = null;
    $("sessionProgressBar").style.width = "100%";
    showToast(sessionKind === "new" ? "今日新内容完成" : "本轮复习完成");
    window.setTimeout(() => goView("home"), 450);
    return;
  }
  activeItem = itemMap.get(sessionQueue[sessionIndex]);
  renderLearningCard();
}

function populateVoices() {
  voices = speechSynthesis.getVoices();
  const voiceSelect = $("voiceSelect");
  const british = voices.filter((voice) => /^en-GB$/i.test(voice.lang));
  const english = voices.filter((voice) => /^en/i.test(voice.lang));
  const choices = british.length ? british : english;
  voiceSelect.innerHTML = "";
  for (const voice of choices) {
    const option = document.createElement("option");
    option.value = voice.voiceURI;
    option.textContent = `${voice.name} (${voice.lang})`;
    voiceSelect.append(option);
  }
  if (!choices.length) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "未检测到英语系统语音";
    voiceSelect.append(option);
  }
  const preferred = choices.find((voice) => voice.voiceURI === state.settings.voiceURI) || british[0] || english[0];
  if (preferred) {
    voiceSelect.value = preferred.voiceURI;
    state.settings.voiceURI = preferred.voiceURI;
  }
  $("voiceStatus").textContent = british.length ? `检测到${british.length}个英式声音` : "未检测到en-GB，已显示其他英语声音";
  saveState();
}

function selectedVoice() {
  return voices.find((voice) => voice.voiceURI === state.settings.voiceURI) || voices.find((voice) => /^en-GB$/i.test(voice.lang)) || voices.find((voice) => /^en/i.test(voice.lang));
}

function speak(text, rate = 1, repeat = 1) {
  if (!("speechSynthesis" in window)) {
    showToast("当前浏览器不支持语音朗读");
    return;
  }
  speechSynthesis.cancel();
  let remaining = repeat;
  const run = () => {
    if (remaining <= 0) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-GB";
    utterance.rate = rate;
    utterance.pitch = 1;
    const voice = selectedVoice();
    if (voice) utterance.voice = voice;
    utterance.onend = () => {
      remaining -= 1;
      if (remaining > 0) window.setTimeout(run, 350);
    };
    utterance.onerror = () => showToast("语音播放失败，请在设置中更换声音");
    speechSynthesis.speak(utterance);
  };
  run();
}

function speakCurrent(rate, repeat = 1) {
  if (!activeItem) return;
  speak(activeItem.pronounceAs || activeItem.term, rate, repeat);
}

async function toggleRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    return;
  }
  if (!(navigator.mediaDevices && window.MediaRecorder)) {
    showToast("当前浏览器不支持录音");
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recordingChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size) recordingChunks.push(event.data);
    };
    mediaRecorder.onstop = () => {
      const blob = new Blob(recordingChunks, { type: mediaRecorder.mimeType || "audio/webm" });
      if (recordingUrl) URL.revokeObjectURL(recordingUrl);
      recordingUrl = URL.createObjectURL(blob);
      $("recordingPlayback").src = recordingUrl;
      $("playRecordingButton").disabled = false;
      $("recordButton").classList.remove("is-recording");
      $("recordLabel").textContent = "重新录音";
      stream.getTracks().forEach((track) => track.stop());
    };
    mediaRecorder.start();
    $("recordButton").classList.add("is-recording");
    $("recordLabel").textContent = "停止录音";
  } catch {
    showToast("没有取得麦克风权限；其他学习功能仍可使用");
  }
}

function resetRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") mediaRecorder.stop();
  if (recordingUrl) URL.revokeObjectURL(recordingUrl);
  recordingUrl = "";
  $("playRecordingButton").disabled = true;
  $("recordButton").classList.remove("is-recording");
  $("recordLabel").textContent = "录下我的发音";
}

function openQuiz() {
  if (!activeItem) return;
  const pool = content.items.filter((item) => item.type === activeItem.type && item.id !== activeItem.id);
  const distractors = shuffle(pool).slice(0, 3);
  const options = shuffle([activeItem, ...distractors]);
  const container = $("quizOptions");
  container.innerHTML = "";
  $("quizFeedback").textContent = "";
  for (const optionItem of options) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.id = optionItem.id;
    button.innerHTML = `<strong>${escapeHtml(optionItem.displayTerm)}</strong><br><small>${escapeHtml(optionItem.chinese)}</small>`;
    button.addEventListener("click", () => {
      container.querySelectorAll("button").forEach((item) => (item.disabled = true));
      if (optionItem.id === activeItem.id) {
        button.classList.add("correct");
        $("quizFeedback").textContent = "正确。再跟读一遍巩固发音。";
        speakCurrent(0.9);
      } else {
        button.classList.add("incorrect");
        const correct = container.querySelector(`[data-id="${activeItem.id}"]`);
        if (correct) correct.classList.add("correct");
        $("quizFeedback").textContent = `正确答案：${activeItem.displayTerm}`;
      }
    });
    container.append(button);
  }
  $("quizDialog").showModal();
  window.setTimeout(() => speakCurrent(0.9), 250);
}

function toggleFlag() {
  if (!activeItem) return;
  if (state.flags.includes(activeItem.id)) {
    state.flags = state.flags.filter((id) => id !== activeItem.id);
    showToast("已取消错误标记");
  } else {
    state.flags.push(activeItem.id);
    showToast("已标记；导出备份时会保留");
  }
  saveState();
  $("flagButton").classList.toggle("is-flagged", state.flags.includes(activeItem.id));
  $("flagButton").style.color = state.flags.includes(activeItem.id) ? "var(--coral)" : "";
}

function itemMastered(id) {
  const progress = state.items[id];
  return Boolean(progress && progress.reps >= 3 && progress.intervalDays >= 14 && progress.lastRating !== "again");
}

function renderLibrary() {
  const query = $("librarySearch").value.trim().toLowerCase();
  let matches = content.items;
  if (libraryFilter === "flagged") matches = matches.filter((item) => state.flags.includes(item.id));
  else if (libraryFilter !== "all") matches = matches.filter((item) => item.type === libraryFilter);
  if (query) {
    matches = matches.filter((item) => `${item.term} ${item.chinese} ${item.theme}`.toLowerCase().includes(query));
  }
  const visible = matches.slice(0, libraryLimit);
  $("libraryList").innerHTML = visible
    .map((item) => {
      const progress = state.items[item.id];
      const status = itemMastered(item.id) ? "已掌握" : progress ? "学习中" : "未学习";
      return `<button type="button" class="library-item" data-id="${item.id}">
        <span class="task-icon ${item.type}-color">${TYPE_LETTERS[item.type]}</span>
        <span class="library-term"><strong>${escapeHtml(item.displayTerm)}</strong><span>${escapeHtml(item.chinese)} · ${escapeHtml(THEME_LABELS[item.theme] || item.theme)}</span></span>
        <span class="library-state ${status === "已掌握" ? "mastered" : ""}">${status}</span>
      </button>`;
    })
    .join("");
  $$(".library-item").forEach((button) => button.addEventListener("click", () => startSession("library", [button.dataset.id])));
  $("loadMoreLibrary").hidden = visible.length >= matches.length;
  $("loadMoreLibrary").textContent = `显示更多（${visible.length}/${matches.length}）`;
}

function computeStreak() {
  const dates = new Set(state.history.map((entry) => entry.date));
  let streak = 0;
  const cursor = new Date();
  if (!dates.has(localDateKey(cursor))) cursor.setDate(cursor.getDate() - 1);
  while (dates.has(localDateKey(cursor))) {
    streak += 1;
    cursor.setDate(cursor.getDate() - 1);
  }
  return streak;
}

function renderStats() {
  const seenIds = Object.keys(state.items).filter((id) => itemMap.has(id));
  const masteredIds = seenIds.filter(itemMastered);
  $("streakCount").textContent = computeStreak();
  $("seenCount").textContent = seenIds.length;
  $("masteredCount").textContent = masteredIds.length;
  $("reviewCount").textContent = state.history.length;
  const percent = Math.round((masteredIds.length / content.items.length) * 100);
  $("masteryPercent").textContent = `${percent}%`;
  $("masteryBar").style.width = `${percent}%`;

  $("typeStats").innerHTML = Object.keys(TYPE_TARGETS)
    .map((type) => {
      const all = content.items.filter((item) => item.type === type).length;
      const mastered = content.items.filter((item) => item.type === type && itemMastered(item.id)).length;
      const typePercent = all ? Math.round((mastered / all) * 100) : 0;
      return `<div class="type-stat"><strong>${TYPE_LABELS[type]}</strong><span class="bar"><i style="width:${typePercent}%"></i></span><span>${typePercent}%</span></div>`;
    })
    .join("");

  const days = [];
  for (let offset = 6; offset >= 0; offset -= 1) {
    const date = new Date();
    date.setDate(date.getDate() - offset);
    const key = localDateKey(date);
    const count = state.history.filter((entry) => entry.date === key).length;
    days.push({ label: new Intl.DateTimeFormat("zh-CN", { weekday: "short" }).format(date), count });
  }
  const max = Math.max(1, ...days.map((day) => day.count));
  $("weeklyChart").innerHTML = days
    .map((day) => `<div class="day-column"><i title="${day.count}次" style="height:${Math.max(3, (day.count / max) * 108)}px"></i><span>${day.label}</span></div>`)
    .join("");
}

function renderSettings() {
  $("slowRate").value = state.settings.slowRate;
  $("slowRateValue").textContent = `${Number(state.settings.slowRate).toFixed(2)}×`;
  $("flaggedCount").textContent = state.flags.length;
  populateVoices();
}

function downloadJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function exportProgress() {
  downloadJson(`kessler-vocab-progress-${localDateKey()}.json`, {
    app: "Kessler Research English",
    exportedAt: new Date().toISOString(),
    contentVersion: content.meta.version,
    progress: state,
  });
  showToast("学习进度已导出");
}

async function importProgress(file) {
  try {
    const payload = JSON.parse(await file.text());
    const imported = payload.progress || payload;
    if (!imported || imported.schemaVersion !== 1 || typeof imported.items !== "object") throw new Error("invalid schema");
    state = { ...defaultState(), ...imported, settings: { ...defaultState().settings, ...(imported.settings || {}) } };
    saveState();
    ensureDailyPlan();
    updateHome();
    renderSettings();
    showToast("学习进度导入成功");
  } catch {
    showToast("无法导入：文件格式不正确");
  }
}

function bindEvents() {
  $$('[data-go]').forEach((button) => button.addEventListener("click", () => goView(button.dataset.go)));
  $("startTodayButton").addEventListener("click", () => startSession("new"));
  $("startReviewButton").addEventListener("click", () => startSession("review"));
  $("closeSessionButton").addEventListener("click", () => {
    activeItem = null;
    speechSynthesis.cancel();
    goView("home");
  });
  $("revealButton").addEventListener("click", revealAnswer);
  $$("[data-rating]").forEach((button) => button.addEventListener("click", () => rateActiveItem(button.dataset.rating)));
  $("speakSlowButton").addEventListener("click", () => speakCurrent(Number(state.settings.slowRate || 0.72)));
  $("speakNormalButton").addEventListener("click", () => speakCurrent(1));
  $("speakLoopButton").addEventListener("click", () => speakCurrent(Number(state.settings.slowRate || 0.72), 3));
  $("recordButton").addEventListener("click", toggleRecording);
  $("playRecordingButton").addEventListener("click", () => $("recordingPlayback").play());
  $("quizButton").addEventListener("click", openQuiz);
  $("quizReplayButton").addEventListener("click", () => speakCurrent(0.9));
  $("flagButton").addEventListener("click", toggleFlag);
  $("dismissBackup").addEventListener("click", () => {
    state.dismissedBackup = true;
    saveState();
    $("backupNotice").hidden = true;
  });

  $("librarySearch").addEventListener("input", () => {
    libraryLimit = 50;
    renderLibrary();
  });
  $$("#libraryFilters button").forEach((button) =>
    button.addEventListener("click", () => {
      libraryFilter = button.dataset.filter;
      libraryLimit = 50;
      $$("#libraryFilters button").forEach((item) => item.classList.toggle("is-active", item === button));
      renderLibrary();
    })
  );
  $("loadMoreLibrary").addEventListener("click", () => {
    libraryLimit += 50;
    renderLibrary();
  });

  $("voiceSelect").addEventListener("change", (event) => {
    state.settings.voiceURI = event.target.value;
    saveState();
  });
  $("slowRate").addEventListener("input", (event) => {
    state.settings.slowRate = Number(event.target.value);
    $("slowRateValue").textContent = `${state.settings.slowRate.toFixed(2)}×`;
    saveState();
  });
  $("testVoiceButton").addEventListener("click", () => speak("Ubiquitin and mass spectrometry", Number(state.settings.slowRate || 0.72)));
  $("exportButton").addEventListener("click", exportProgress);
  $("importInput").addEventListener("change", (event) => {
    if (event.target.files[0]) importProgress(event.target.files[0]);
    event.target.value = "";
  });
  $("exportFlagsButton").addEventListener("click", () => {
    const flaggedItems = state.flags.map((id) => itemMap.get(id)).filter(Boolean);
    downloadJson(`kessler-vocab-flags-${localDateKey()}.json`, { exportedAt: new Date().toISOString(), items: flaggedItems });
  });
  $("resetButton").addEventListener("click", () => {
    if (!window.confirm("确定清除本设备的全部学习进度吗？建议先导出备份。")) return;
    state = defaultState();
    saveState();
    ensureDailyPlan();
    updateHome();
    renderSettings();
    showToast("学习进度已清除");
  });

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredInstallPrompt = event;
    $("installButton").hidden = false;
  });
  $("installButton").addEventListener("click", async () => {
    if (!deferredInstallPrompt) return;
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
    $("installButton").hidden = true;
  });
  window.addEventListener("appinstalled", () => showToast("应用已安装到设备"));
}

async function init() {
  try {
    await loadContent();
    ensureDailyPlan();
    bindEvents();
    updateHome();
    populateVoices();
    if ("speechSynthesis" in window) speechSynthesis.addEventListener("voiceschanged", populateVoices);
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("./sw.js", { updateViaCache: "none" })
        .then((registration) => registration.update())
        .catch(() => showToast("离线缓存注册失败，联网功能仍可使用"));
    }
  } catch (error) {
    console.error(error);
    document.body.innerHTML = `<main style="padding:32px;font-family:system-ui"><h1>学习数据加载失败</h1><p>${escapeHtml(error.message)}</p><p>请通过本地服务器或GitHub Pages打开应用。</p></main>`;
  }
}

document.addEventListener("DOMContentLoaded", init);
