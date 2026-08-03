"use strict";

const INTERVIEW_PREFS_KEY = "kessler-interview-preferences-v1";
const INTERVIEW_RATES = [1, 0.75, 0.5];
const MALE_VOICE_PATTERN = /\b(male|george|ryan|guy|david|mark|james|daniel|thomas|arthur|oliver|roger|aaron|fred|alex|rishi|lee|reed|ralph|andrew|brian|christopher|eric|stef+an|aiden|jacob|jason|brandon|justin|kevin|matthew|william|davis|tony|jackson|robert|ethan|henry|liam|mason|noah|gordon|malcolm)\b/i;
const FEMALE_VOICE_PATTERN = /\b(female|aria|ava|emma|jenny|michelle|monica|nancy|sara|sonia|libby|abbi|maisie|olivia|amy|joanna|samantha|susan|victoria|karen|moira|fiona|serena|tessa|veena|kate|hazel|zira)\b/i;

const INTERVIEW_QUESTIONS = [
  {
    id: "introduction",
    topic: "Introduction",
    question: "Good morning, Tao. Thank you for meeting with me. Could you briefly introduce yourself and describe your current research?",
    keywords: ["research", "proteomics", "mass spectrometry", "lactylation", "phosphoproteomics", "multi-omics"],
  },
  {
    id: "lactylome-objective",
    topic: "C. elegans lactylome",
    question: "Could you give me a short overview of your C. elegans lactylome study, and explain its main objective?",
    keywords: ["c. elegans", "lactyl", "objective", "aim", "protein", "study"],
  },
  {
    id: "lactylome-methods",
    topic: "Study design",
    question: "How did you prepare the samples and identify the lactylated peptides by mass spectrometry?",
    keywords: ["sample", "peptide", "enrichment", "antibody", "mass spectrometry", "lc-ms", "analysis"],
  },
  {
    id: "lactylome-findings",
    topic: "Findings and reliability",
    question: "What was the most important finding, and how did you assess the reliability of the lactylation sites?",
    keywords: ["finding", "site", "reliability", "validation", "fdr", "replicate", "result"],
  },
  {
    id: "mass-spec-experience",
    topic: "Mass spectrometry",
    question: "Which mass spectrometers and acquisition strategies have you used most independently?",
    keywords: ["orbitrap", "exploris", "fusion", "lumos", "qe", "tims", "tof", "dda", "dia", "prm", "tmt", "independently"],
  },
  {
    id: "technical-problem",
    topic: "Technical problem-solving",
    question: "Please describe one technical problem you encountered in a proteomics experiment, and explain how you solved it.",
    keywords: ["problem", "challenge", "signal", "sample", "contamination", "reproducibility", "solved", "optimised", "optimized"],
  },
  {
    id: "motivation",
    topic: "Motivation",
    question: "Why are you interested in visiting my group at Oxford?",
    keywords: ["ubiquitin", "protease", "proteomics", "kessler", "oxford", "learn", "collaboration", "interested"],
  },
  {
    id: "visit-project",
    topic: "Proposed visit",
    question: "What research question would you like to address during a three-to-six-month visit?",
    keywords: ["project", "question", "aim", "ubiquitin", "protease", "mass spectrometry", "during", "visit"],
  },
  {
    id: "contribution",
    topic: "Contribution to the group",
    question: "How would your experience in lactylation, phosphoproteomics, or single-cell multi-omics contribute to our work?",
    keywords: ["experience", "lactylation", "phosphoproteomics", "single-cell", "multi-omics", "contribute", "combine", "skills"],
  },
  {
    id: "funding",
    topic: "Funding",
    question: "How would your visit be funded, and are there any conditions attached to that funding?",
    keywords: ["fund", "funding", "scholarship", "csc", "china scholarship council", "institution", "support"],
  },
  {
    id: "availability",
    topic: "Availability",
    question: "When would you be available to start, and how long could you stay in Oxford?",
    keywords: ["available", "start", "month", "three", "four", "five", "six", "stay", "date"],
  },
  {
    id: "questions",
    topic: "Your questions",
    question: "Finally, what questions would you like to ask me about the project or the group?",
    keywords: ["project", "group", "question", "priority", "training", "method", "expect", "collaboration"],
  },
];

const INTERVIEW_FOLLOW_UPS = {
  introduction: {
    id: "introduction-follow-up",
    topic: "Introduction · follow-up",
    question: "Could you tell me more specifically how your current work relates to mass spectrometry-based proteomics?",
    keywords: ["mass spectrometry", "proteomics", "sample", "analysis", "protein"],
  },
  "lactylome-objective": {
    id: "lactylome-objective-follow-up",
    topic: "C. elegans lactylome · follow-up",
    question: "What biological question were you trying to answer with the lactylome study?",
    keywords: ["question", "lactyl", "biological", "process", "mechanism", "aim"],
  },
  "lactylome-methods": {
    id: "lactylome-methods-follow-up",
    topic: "Study design · follow-up",
    question: "Which step in the experimental workflow was the most technically demanding for you?",
    keywords: ["enrichment", "sample", "peptide", "instrument", "analysis", "challenging", "difficult"],
  },
  "lactylome-findings": {
    id: "lactylome-findings-follow-up",
    topic: "Findings · follow-up",
    question: "How did you distinguish a reliable lactylation site from a possible false positive?",
    keywords: ["fdr", "localisation", "localization", "score", "replicate", "validation", "false positive"],
  },
  "mass-spec-experience": {
    id: "mass-spec-experience-follow-up",
    topic: "Mass spectrometry · follow-up",
    question: "Could you name the instrument and software that you can operate most confidently?",
    keywords: ["orbitrap", "exploris", "lumos", "fusion", "maxquant", "proteome discoverer", "spectronaut", "software"],
  },
  motivation: {
    id: "motivation-follow-up",
    topic: "Motivation · follow-up",
    question: "Which aspect of our work on ubiquitin or protease biology is most relevant to your research goals?",
    keywords: ["ubiquitin", "protease", "deubiquitin", "mass spectrometry", "profiling", "goal"],
  },
  "visit-project": {
    id: "visit-project-follow-up",
    topic: "Proposed visit · follow-up",
    question: "What specific result would you hope to achieve by the end of a short visit?",
    keywords: ["result", "dataset", "method", "workflow", "manuscript", "pilot", "achieve"],
  },
  funding: {
    id: "funding-follow-up",
    topic: "Funding · follow-up",
    question: "Would the funding cover your travel, accommodation, and living costs in Oxford?",
    keywords: ["cover", "travel", "accommodation", "living", "cost", "funding", "support"],
  },
  availability: {
    id: "availability-follow-up",
    topic: "Availability · follow-up",
    question: "How flexible would you be if the laboratory needed to adjust the starting date?",
    keywords: ["flexible", "adjust", "date", "available", "month", "schedule"],
  },
};

const IMPROVEMENT_SENTENCES = [
  {
    id: "practice-introduction",
    topics: ["introduction"],
    text: "My research focuses on mass spectrometry-based proteomics, particularly protein lactylation and phosphoproteomics.",
  },
  {
    id: "practice-lactylome-objective",
    topics: ["lactylome-objective"],
    text: "The main objective of our study was to characterise the lactylome of C. elegans and explore its potential biological significance.",
  },
  {
    id: "practice-lactylome-methods",
    topics: ["lactylome-methods"],
    text: "We prepared the samples carefully and used mass spectrometry-based analysis to identify lactylated peptides and modification sites.",
  },
  {
    id: "practice-lactylome-findings",
    topics: ["lactylome-findings"],
    text: "Our most important finding was that lactylation may be associated with specific biological processes in C. elegans.",
  },
  {
    id: "practice-mass-spec",
    topics: ["mass-spec-experience", "technical-problem"],
    text: "I have hands-on experience in proteomic sample preparation, mass spectrometry data acquisition, and downstream data analysis.",
  },
  {
    id: "practice-motivation",
    topics: ["motivation"],
    text: "I am particularly interested in your group's expertise in ubiquitin biology, proteases, and mass spectrometry-based proteomics.",
  },
  {
    id: "practice-visit-project",
    topics: ["visit-project", "contribution"],
    text: "During the visit, I hope to develop a focused and feasible project that complements the group's current priorities.",
  },
  {
    id: "practice-funding",
    topics: ["funding"],
    text: "I plan to apply for funding from the China Scholarship Council, subject to the relevant approval requirements.",
  },
  {
    id: "practice-availability",
    topics: ["availability"],
    text: "I am flexible about the starting date and would be available for a research visit of three to six months.",
  },
  {
    id: "practice-questions",
    topics: ["questions"],
    text: "Could you please advise me which research direction would be most useful for your group at present?",
  },
];

let interviewIndex = 0;
let interviewQueue = [];
let interviewAnswers = [];
let interviewSupport = {};
let interviewStartedAt = 0;
let interviewRate = 0.75;
let interviewVoiceURI = "";
let recognition = null;
let recognitionActive = false;
let recognitionBase = "";
let answerTimer = null;
let answerStartedAt = 0;
let interviewAudio = null;

const INTERVIEW_AUDIO_VERSION = "2026-08-04-6";

const interviewElement = (id) => document.getElementById(id);

function loadInterviewPreferences() {
  try {
    const saved = JSON.parse(localStorage.getItem(INTERVIEW_PREFS_KEY) || "null");
    const savedRate = Number(saved?.rate);
    if (INTERVIEW_RATES.includes(savedRate)) interviewRate = savedRate;
    interviewVoiceURI = String(saved?.voiceURI || "");
  } catch {
    interviewRate = 0.75;
    interviewVoiceURI = "";
  }
}

function saveInterviewPreferences() {
  localStorage.setItem(INTERVIEW_PREFS_KEY, JSON.stringify({
    rate: interviewRate,
    voiceURI: interviewVoiceURI,
  }));
}

function isLikelyMaleVoice(voice) {
  return MALE_VOICE_PATTERN.test(voice?.name || "");
}

function isLikelyFemaleVoice(voice) {
  return FEMALE_VOICE_PATTERN.test(voice?.name || "");
}

function voicePriority(voice) {
  const british = /^en-GB$/i.test(voice.lang);
  const likelyMale = isLikelyMaleVoice(voice);
  if (british && likelyMale) return 0;
  if (likelyMale) return 1;
  if (british) return 2;
  return 3;
}

function updateRateControls() {
  document.querySelectorAll("[data-interview-rate]").forEach((button) => {
    button.classList.toggle("is-active", Number(button.dataset.interviewRate) === interviewRate);
  });
  interviewElement("interviewSessionRateSelect").value = String(interviewRate);
}

function setInterviewRate(value) {
  const rate = Number(value);
  if (!INTERVIEW_RATES.includes(rate)) return;
  interviewRate = rate;
  updateRateControls();
  saveInterviewPreferences();
}

function populateInterviewVoices() {
  const select = interviewElement("interviewVoiceSelect");
  select.innerHTML = "";
  const option = document.createElement("option");
  option.value = "bundled-ryan";
  option.textContent = "Ryan · British English · Male";
  select.append(option);
  select.value = option.value;
  select.disabled = true;
  interviewVoiceURI = option.value;
  interviewElement("interviewVoiceStatus").textContent = "固定英国男声 · 不调用设备女声";
  saveInterviewPreferences();
}

function currentInterviewQuestion() {
  return interviewQueue[interviewIndex];
}

function getEnglishVoice() {
  if (!("speechSynthesis" in window)) return null;
  const voices = window.speechSynthesis.getVoices();
  let appVoiceUri = "";
  try {
    const saved = JSON.parse(localStorage.getItem("kessler-vocab-progress-v1") || "null");
    appVoiceUri = saved?.settings?.voiceURI || "";
  } catch {
    appVoiceUri = "";
  }
  const maleEnglish = voices.filter((voice) => /^en/i.test(voice.lang) && isLikelyMaleVoice(voice));
  const selected = voices.find((voice) => voice.voiceURI === interviewVoiceURI);
  return (selected && (!maleEnglish.length || isLikelyMaleVoice(selected)) ? selected : null)
    || voices.find((voice) => /^en-GB$/i.test(voice.lang) && isLikelyMaleVoice(voice))
    || voices.find((voice) => /^en/i.test(voice.lang) && isLikelyMaleVoice(voice))
    || voices.find((voice) => voice.voiceURI === appVoiceUri)
    || voices.find((voice) => /^en-GB$/i.test(voice.lang))
    || voices.find((voice) => /^en/i.test(voice.lang))
    || null;
}

function setInterviewSpeaking(speaking) {
  interviewElement("interviewWave").classList.toggle("is-speaking", speaking);
  interviewElement("interviewStatus").textContent = speaking
    ? "Speaking… please listen"
    : "Your turn · Please answer in English";
}

function stopInterviewPlayback() {
  if (interviewAudio) {
    interviewAudio.pause();
    interviewAudio.removeAttribute("src");
    interviewAudio.load();
    interviewAudio = null;
  }
  window.speechSynthesis?.cancel();
}

function playBundledMaleAudio(identifier, rate, onStart, onEnd, onFailure) {
  stopInterviewPlayback();
  const audio = new Audio(`./audio/interview/${identifier}.mp3?v=${INTERVIEW_AUDIO_VERSION}`);
  interviewAudio = audio;
  audio.preload = "auto";
  audio.playbackRate = rate;
  audio.defaultPlaybackRate = rate;
  audio.preservesPitch = true;
  audio.onplay = () => onStart?.();
  audio.onended = () => {
    if (interviewAudio === audio) interviewAudio = null;
    onEnd?.();
  };
  let failed = false;
  const fail = () => {
    if (failed) return;
    failed = true;
    if (interviewAudio === audio) interviewAudio = null;
    onFailure?.();
  };
  audio.onerror = fail;
  audio.play().catch(fail);
}

function fallbackToDeviceSpeech(text, rate, onStart, onEnd) {
  if (!("speechSynthesis" in window) || !("SpeechSynthesisUtterance" in window)) {
    onEnd?.();
    return;
  }
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-GB";
  utterance.rate = rate;
  const voice = getEnglishVoice();
  if (voice) utterance.voice = voice;
  utterance.pitch = voice && isLikelyMaleVoice(voice) ? 0.9 : 0.72;
  utterance.onstart = onStart;
  utterance.onend = onEnd;
  utterance.onerror = onEnd;
  window.speechSynthesis.speak(utterance);
}

function speakInterviewQuestion(rate = interviewRate) {
  const item = currentInterviewQuestion();
  if (!item) return;
  playBundledMaleAudio(
    item.id,
    rate,
    () => setInterviewSpeaking(true),
    () => setInterviewSpeaking(false),
    () => fallbackToDeviceSpeech(item.question, rate, () => setInterviewSpeaking(true), () => setInterviewSpeaking(false)),
  );
}

function supportForCurrentQuestion() {
  const id = currentInterviewQuestion().id;
  if (!interviewSupport[id]) {
    interviewSupport[id] = { repeats: 0, slowRepeats: 0, didNotUnderstand: 0, showedText: false };
  }
  return interviewSupport[id];
}

function resetAnswerTimer() {
  window.clearInterval(answerTimer);
  answerTimer = null;
  answerStartedAt = 0;
  interviewElement("interviewTimer").textContent = "00:00";
}

function startAnswerTimer() {
  if (answerTimer) return;
  answerStartedAt = Date.now();
  answerTimer = window.setInterval(() => {
    const seconds = Math.floor((Date.now() - answerStartedAt) / 1000);
    const minutes = String(Math.floor(seconds / 60)).padStart(2, "0");
    const remainder = String(seconds % 60).padStart(2, "0");
    interviewElement("interviewTimer").textContent = `${minutes}:${remainder}`;
  }, 250);
}

function updateSubmitAvailability() {
  interviewElement("interviewSubmitButton").disabled = !interviewElement("interviewAnswerInput").value.trim();
}

function stopRecognition() {
  if (recognition && recognitionActive) {
    recognitionActive = false;
    try {
      recognition.stop();
    } catch {
      // Recognition may already have stopped after a pause.
    }
  }
  window.clearInterval(answerTimer);
  answerTimer = null;
  interviewElement("interviewMicButton").classList.remove("is-recording");
  interviewElement("interviewMicLabel").textContent = interviewElement("interviewAnswerInput").value.trim()
    ? "继续补充回答"
    : "点击开始回答";
}

function createRecognition() {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) return null;
  const instance = new Recognition();
  instance.lang = "en-GB";
  instance.continuous = true;
  instance.interimResults = true;
  instance.maxAlternatives = 1;

  instance.onstart = () => {
    recognitionActive = true;
    interviewElement("interviewMicButton").classList.add("is-recording");
    interviewElement("interviewMicLabel").textContent = "正在听你的回答…";
    interviewElement("interviewRecognitionNote").textContent = "请自然说英语；说完后再次点击红色按钮。";
    startAnswerTimer();
  };

  instance.onresult = (event) => {
    let finalText = "";
    let interimText = "";
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const text = event.results[i][0].transcript;
      if (event.results[i].isFinal) finalText += `${text} `;
      else interimText += text;
    }
    if (finalText) recognitionBase = `${recognitionBase} ${finalText}`.trim();
    interviewElement("interviewAnswerInput").value = `${recognitionBase} ${interimText}`.trim();
    updateSubmitAvailability();
  };

  instance.onerror = (event) => {
    if (event.error === "not-allowed" || event.error === "service-not-allowed") {
      interviewElement("interviewRecognitionNote").textContent = "未取得麦克风权限。请允许权限，或使用手机键盘的语音输入。";
    } else if (event.error !== "no-speech" && event.error !== "aborted") {
      interviewElement("interviewRecognitionNote").textContent = `语音转写暂时不可用（${event.error}），可手动输入后继续。`;
    }
    recognitionActive = false;
    stopRecognition();
  };

  instance.onend = () => {
    recognitionActive = false;
    stopRecognition();
    updateSubmitAvailability();
  };
  return instance;
}

function toggleInterviewMicrophone() {
  if (recognitionActive) {
    stopRecognition();
    return;
  }
  if (!recognition) recognition = createRecognition();
  if (!recognition) {
    interviewElement("interviewRecognitionNote").textContent = "此浏览器没有自动转写功能。可点击输入框，并使用手机键盘上的麦克风进行英语语音输入。";
    interviewElement("interviewAnswerInput").focus();
    return;
  }
  stopInterviewPlayback();
  recognitionBase = interviewElement("interviewAnswerInput").value.trim();
  try {
    recognition.start();
  } catch {
    interviewElement("interviewRecognitionNote").textContent = "麦克风正在启动，请稍后再试。";
  }
}

function renderInterviewQuestion() {
  const item = currentInterviewQuestion();
  interviewElement("interviewQuestionNumber").textContent = `Question ${interviewIndex + 1} / ${interviewQueue.length}`;
  interviewElement("interviewTopic").textContent = item.topic;
  interviewElement("interviewProgressBar").style.width = `${(interviewIndex / interviewQueue.length) * 100}%`;
  interviewElement("interviewQuestionText").textContent = item.question;
  interviewElement("interviewQuestionText").hidden = true;
  interviewElement("interviewShowTextButton").innerHTML = '<span aria-hidden="true">Aa</span> 显示原文';
  interviewElement("interviewAnswerInput").value = "";
  interviewElement("interviewRecognitionNote").textContent = recognition || window.SpeechRecognition || window.webkitSpeechRecognition
    ? "系统不会在面试过程中纠正你；所有反馈将在结束后显示。"
    : "需要语音转写时，可使用手机键盘自带的英语语音输入。";
  recognitionBase = "";
  resetAnswerTimer();
  stopRecognition();
  updateSubmitAvailability();
  interviewElement("interviewMicLabel").textContent = "点击开始回答";
  window.scrollTo({ top: 0, behavior: "smooth" });
  speakInterviewQuestion(interviewRate);
}

function startInterview() {
  stopInterviewPlayback();
  interviewIndex = 0;
  interviewQueue = INTERVIEW_QUESTIONS.map((question) => ({ ...question }));
  interviewAnswers = [];
  interviewSupport = {};
  interviewStartedAt = Date.now();
  recognition = createRecognition();
  interviewElement("interviewIntro").hidden = true;
  interviewElement("interviewResult").hidden = true;
  interviewElement("interviewSession").hidden = false;
  renderInterviewQuestion();
}

function wordCount(value) {
  return String(value).trim().split(/\s+/).filter(Boolean).length;
}

function keywordMatches(answer, keywords) {
  const normalised = answer.toLowerCase();
  return keywords.filter((keyword) => normalised.includes(keyword)).length;
}

function answerAssessment(record) {
  const words = wordCount(record.answer);
  const matches = keywordMatches(record.answer, record.question.keywords);
  if (!record.answer.trim()) return "没有记录到回答";
  if (words < 7) return "回答较短，核心信息可能没有展开";
  if (words < 14 && matches === 0) return "回答较短，且没有清楚回应问题重点";
  return "";
}

function submitInterviewAnswer() {
  const answer = interviewElement("interviewAnswerInput").value.trim();
  if (!answer) return;
  stopRecognition();
  const question = currentInterviewQuestion();
  interviewAnswers.push({
    question,
    answer,
    support: { ...supportForCurrentQuestion() },
    elapsedSeconds: answerStartedAt ? Math.round((Date.now() - answerStartedAt) / 1000) : 0,
  });
  const followUp = INTERVIEW_FOLLOW_UPS[question.id];
  const needsFollowUp = followUp && (wordCount(answer) < 12 || keywordMatches(answer, question.keywords) === 0);
  if (needsFollowUp) interviewQueue.splice(interviewIndex + 1, 0, { ...followUp, adaptive: true });
  interviewIndex += 1;
  if (interviewIndex >= interviewQueue.length) {
    finishInterview();
    return;
  }
  renderInterviewQuestion();
}

function markNotUnderstood() {
  const support = supportForCurrentQuestion();
  support.didNotUnderstand += 1;
  support.slowRepeats += 1;
  speakInterviewQuestion(0.5);
}

function toggleQuestionText() {
  const panel = interviewElement("interviewQuestionText");
  panel.hidden = !panel.hidden;
  supportForCurrentQuestion().showedText = !panel.hidden || supportForCurrentQuestion().showedText;
  interviewElement("interviewShowTextButton").innerHTML = panel.hidden
    ? '<span aria-hidden="true">Aa</span> 显示原文'
    : '<span aria-hidden="true">Aa</span> 隐藏原文';
}

function fiveImprovementSentences(unclearRecords) {
  const weakIds = unclearRecords.map((record) => record.question.id);
  const priority = [
    ...IMPROVEMENT_SENTENCES.filter((item) => item.topics.some((topic) => weakIds.includes(topic))),
    ...IMPROVEMENT_SENTENCES.filter((item) => !item.topics.some((topic) => weakIds.includes(topic))),
  ];
  return [...new Map(priority.map((item) => [item.text, item])).values()].slice(0, 5);
}

function buildInterviewReport() {
  const misunderstood = interviewAnswers.filter((record) => record.support.didNotUnderstand > 0 || record.support.showedText);
  const unclear = interviewAnswers
    .map((record) => ({ ...record, issue: answerAssessment(record) }))
    .filter((record) => record.issue);
  const sentences = fiveImprovementSentences(unclear);
  const durationMinutes = Math.max(1, Math.round((Date.now() - interviewStartedAt) / 60_000));
  return { misunderstood, unclear, sentences, durationMinutes };
}

function listItem(text, detail = "") {
  const item = document.createElement("li");
  const strong = document.createElement("strong");
  strong.textContent = text;
  item.append(strong);
  if (detail) {
    const paragraph = document.createElement("p");
    paragraph.textContent = detail;
    item.append(paragraph);
  }
  return item;
}

function renderEmptyList(list, text) {
  const item = document.createElement("li");
  item.className = "result-empty";
  item.textContent = text;
  list.append(item);
}

function finishInterview() {
  stopRecognition();
  stopInterviewPlayback();
  const report = buildInterviewReport();
  interviewElement("interviewSession").hidden = true;
  interviewElement("interviewIntro").hidden = true;
  interviewElement("interviewResult").hidden = false;
  interviewElement("interviewResultSummary").textContent = `完成 ${interviewAnswers.length} 个问题 · 约 ${report.durationMinutes} 分钟`;

  const misunderstoodList = interviewElement("interviewMisunderstoodList");
  misunderstoodList.innerHTML = "";
  for (const record of report.misunderstood) {
    const reason = record.support.didNotUnderstand
      ? `使用了 ${record.support.didNotUnderstand} 次“没听懂”慢速重播。`
      : "查看了英文原文。";
    misunderstoodList.append(listItem(record.question.question, reason));
  }
  if (!report.misunderstood.length) renderEmptyList(misunderstoodList, "本轮没有记录到未听懂的问题。");

  const unclearList = interviewElement("interviewUnclearList");
  unclearList.innerHTML = "";
  for (const record of report.unclear) {
    unclearList.append(listItem(record.question.topic, `${record.issue}｜你的回答：${record.answer}`));
  }
  if (!report.unclear.length) renderEmptyList(unclearList, "本轮所有回答都达到了基本清晰度。");

  const sentenceList = interviewElement("interviewSentenceList");
  sentenceList.innerHTML = "";
  for (const sentence of report.sentences) {
    const item = document.createElement("li");
    const text = document.createElement("span");
    text.textContent = sentence.text;
    const play = document.createElement("button");
    play.type = "button";
    play.textContent = "▶ 慢速听";
    play.addEventListener("click", () => speakPracticeSentence(sentence.text, sentence.id));
    item.append(text, play);
    sentenceList.append(item);
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function speakPracticeSentence(text, identifier) {
  playBundledMaleAudio(
    identifier,
    0.68,
    null,
    null,
    () => fallbackToDeviceSpeech(text, 0.68),
  );
}

function previewInterviewVoice() {
  const status = interviewElement("interviewVoiceStatus");
  playBundledMaleAudio(
    "preview",
    interviewRate,
    () => (status.textContent = "正在试听固定英国男声 Ryan…"),
    () => (status.textContent = "固定英国男声 Ryan · 不调用设备女声"),
    () => (status.textContent = "男声音频加载失败，请检查网络后重试"),
  );
}

function interviewReportText() {
  const report = buildInterviewReport();
  const misunderstood = report.misunderstood.length
    ? report.misunderstood.map((record, index) => `${index + 1}. ${record.question.question}`).join("\n")
    : "None recorded.";
  const unclear = report.unclear.length
    ? report.unclear.map((record, index) => `${index + 1}. ${record.question.topic}: ${record.issue}\n   ${record.answer}`).join("\n")
    : "None recorded.";
  const sentences = report.sentences.map((sentence, index) => `${index + 1}. ${sentence.text}`).join("\n");
  return `Kessler Research English — Mock Interview Review\n\nQuestions not understood\n${misunderstood}\n\nAnswers that were unclear\n${unclear}\n\nFive sentences to improve\n${sentences}`;
}

async function copyInterviewReport() {
  const button = interviewElement("interviewCopyButton");
  try {
    await navigator.clipboard.writeText(interviewReportText());
    button.textContent = "已复制复盘";
  } catch {
    const textarea = document.createElement("textarea");
    textarea.value = interviewReportText();
    document.body.append(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
    button.textContent = "已复制复盘";
  }
  window.setTimeout(() => (button.textContent = "复制本轮复盘"), 1800);
}

function exitInterview() {
  const hasProgress = interviewAnswers.length || interviewElement("interviewAnswerInput").value.trim();
  if (hasProgress && !window.confirm("退出后，本轮尚未完成的模拟面试不会保存。确定退出吗？")) return;
  stopRecognition();
  stopInterviewPlayback();
  interviewElement("interviewSession").hidden = true;
  interviewElement("interviewResult").hidden = true;
  interviewElement("interviewIntro").hidden = false;
  document.querySelector('.bottom-nav [data-go="home"]')?.click();
}

function initInterview() {
  loadInterviewPreferences();
  updateRateControls();
  populateInterviewVoices();
  document.querySelectorAll("[data-interview-rate]").forEach((button) => {
    button.addEventListener("click", () => setInterviewRate(button.dataset.interviewRate));
  });
  interviewElement("interviewSessionRateSelect").addEventListener("change", (event) => setInterviewRate(event.target.value));
  interviewElement("interviewVoicePreviewButton").addEventListener("click", previewInterviewVoice);
  interviewElement("interviewStartButton").addEventListener("click", startInterview);
  interviewElement("interviewRestartButton").addEventListener("click", startInterview);
  interviewElement("interviewRepeatButton").addEventListener("click", () => {
    supportForCurrentQuestion().repeats += 1;
    speakInterviewQuestion(interviewRate);
  });
  interviewElement("interviewShowTextButton").addEventListener("click", toggleQuestionText);
  interviewElement("interviewDidNotUnderstandButton").addEventListener("click", markNotUnderstood);
  interviewElement("interviewMicButton").addEventListener("click", toggleInterviewMicrophone);
  interviewElement("interviewAnswerInput").addEventListener("input", updateSubmitAvailability);
  interviewElement("interviewSubmitButton").addEventListener("click", submitInterviewAnswer);
  interviewElement("interviewEndButton").addEventListener("click", finishInterview);
  interviewElement("interviewExitButton").addEventListener("click", exitInterview);
  interviewElement("interviewCopyButton").addEventListener("click", copyInterviewReport);

  document.querySelectorAll("[data-go]").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.go !== "interview" && !interviewElement("interviewSession").hidden) {
        stopRecognition();
        stopInterviewPlayback();
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", initInterview);
