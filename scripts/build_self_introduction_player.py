#!/usr/bin/env python3
"""Build Tao Ding's mobile self-introduction player with British IPA."""

from __future__ import annotations

import asyncio
import html
import json
import os
import re
from pathlib import Path

import edge_tts
import espeakng_loader


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "app" / "self-introduction"
VOICE = "en-GB-RyanNeural"
TOKEN_RE = re.compile(
    r"[A-Za-z]+(?:['’][A-Za-z]+)*(?:-[A-Za-z]+(?:['’][A-Za-z]+)*)*|\d+(?:\.\d+)?"
)

PARAGRAPHS = [
    {
        "title": "Opening",
        "title_zh": "开场",
        "text": "Good morning, Professor Kessler.",
    },
    {
        "title": "Education and background",
        "title_zh": "教育背景",
        "text": (
            "My name is Ding Tao, and I was born in April 1998 in Guiyang, Guizhou Province. "
            "I am currently a PhD student at the Institute of Basic Medical Sciences, Chinese Academy "
            "of Medical Sciences and Peking Union Medical College. Throughout my academic journey, I have maintained "
            "a passion and dedication to my major courses, which has led to outstanding "
            "achievements across various disciplines."
        ),
    },
    {
        "title": "Research focus",
        "title_zh": "研究方向",
        "text": (
            "Under the meticulous guidance of Professor Yang Juntao, I have been engaged in the "
            "application of liquid chromatography-mass spectrometry (LC-MS) technology in "
            "proteomics. My focus has been on experimental design, detection analysis, and "
            "translational research, with a commitment to exploring disease mechanisms and biomarkers."
        ),
    },
    {
        "title": "Research achievements",
        "title_zh": "研究成果",
        "text": (
            "To date, my research achievements include being the co-first author of a paper titled "
            '"Global profiling of protein lactylation in Caenorhabditis elegans," published in the '
            "journal Proteomics (Impact Factor: 3.4). Additionally, I was honoured with the first-class "
            "scholarship at Peking Union Medical College for the academic year 2022-2023."
        ),
    },
    {
        "title": "Core competencies",
        "title_zh": "核心能力",
        "text": "Through my scientific training, I have accumulated some key competencies.",
    },
    {
        "title": "Project design",
        "title_zh": "课题设计",
        "text": (
            "I am well-versed in the design and conceptualization of proteomics projects and actively "
            "participate in the design and discussion of new research topics."
        ),
    },
    {
        "title": "Instrument experience",
        "title_zh": "仪器经验",
        "text": (
            "I am capable of operating various liquid chromatography-mass spectrometers, such as "
            "the timsTOF Pro 2, independently, and I am able to perform maintenance and optimize mass "
            "spectrometry methods for different samples."
        ),
    },
    {
        "title": "Data analysis and writing",
        "title_zh": "数据分析与写作",
        "text": (
            "I possess the ability to independently process proteomics and related multi-omics data "
            "and can write SCI papers independently."
        ),
    },
    {
        "title": "Personal qualities",
        "title_zh": "个人特点",
        "text": (
            "I have a cheerful personality and enjoy communication. I maintain a positive attitude "
            "in both academia and daily life. With a good mindset, solid professional skills, and "
            "relentless enthusiasm, I am confident that I can become an outstanding researcher."
        ),
    },
    {
        "title": "Closing",
        "title_zh": "结尾",
        "text": "Thank you all for your time and consideration.",
    },
]

IPA_OVERRIDES = {
    "ding": "dɪŋ",
    "tao": "taʊ",
    "guiyang": "ɡweɪˈjɑːŋ",
    "guizhou": "ɡweɪˈdʒəʊ",
    "yang": "jɑːŋ",
    "juntao": "dʒuːnˈtaʊ",
    "kessler": "ˈkeslə",
    "peking": "ˌpiːˈkɪŋ",
    "lc-ms": "ˌel siː ˌem ˈes",
    "timstof": "ˌtɪmz tiː əʊ ˈef",
    "sci": "ˌes siː ˈaɪ",
    "phd": "ˌpiː eɪtʃ ˈdiː",
    "proteomics": "ˌprəʊtiˈɒmɪks",
    "lactylation": "ˌlæktɪlˈeɪʃən",
    "multi-omics": "ˌmʌltiˈəʊmɪks",
    "caenorhabditis": "ˌsiːnəʊræbˈdaɪtɪs",
    "elegans": "ˈelɪɡænz",
    "1998": "ˌnaɪntiːn naɪntiˈeɪt",
    "2022": "ˌtwenti twentiˈtuː",
    "2023": "ˌtwenti twentiˈθriː",
    "3.4": "ˌθriː pɔɪnt ˈfɔː",
    "2": "tuː",
}


def normalise_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def configure_phonemizer() -> None:
    os.environ["ESPEAK_DATA_PATH"] = str(espeakng_loader.get_data_path())
    from phonemizer.backend.espeak.wrapper import EspeakWrapper

    EspeakWrapper.set_library(str(espeakng_loader.get_library_path()))


def make_ipa(tokens: list[str]) -> list[str]:
    configure_phonemizer()
    from phonemizer import phonemize

    generated = phonemize(
        tokens,
        language="en-gb",
        backend="espeak",
        strip=True,
        preserve_punctuation=False,
        with_stress=True,
        njobs=1,
    )
    return [IPA_OVERRIDES.get(token.lower(), value.strip()) for token, value in zip(tokens, generated)]


async def generate_audio(text: str, destination: Path) -> list[dict]:
    last_error: Exception | None = None
    for attempt in range(1, 5):
        try:
            destination.unlink(missing_ok=True)
            boundaries: list[dict] = []
            communicate = edge_tts.Communicate(
                text,
                VOICE,
                rate="+0%",
                volume="+0%",
                pitch="+0Hz",
                boundary="WordBoundary",
            )
            with destination.open("wb") as audio:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        boundaries.append(chunk)
            if destination.stat().st_size < 10_000 or not boundaries:
                raise RuntimeError("audio generation returned incomplete output")
            return boundaries
        except Exception as error:
            last_error = error
            await asyncio.sleep(attempt * 1.5)
    raise RuntimeError("unable to generate self-introduction audio") from last_error


def expand_boundaries(boundaries: list[dict]) -> list[dict]:
    expanded: list[dict] = []
    for boundary in boundaries:
        parts = TOKEN_RE.findall(boundary["text"])
        if not parts:
            continue
        start = boundary["offset"] / 10_000_000
        duration = boundary["duration"] / 10_000_000
        weights = [max(1, len(re.sub(r"[^A-Za-z0-9]", "", part))) for part in parts]
        total_weight = sum(weights)
        cursor = start
        for part, weight in zip(parts, weights):
            part_duration = duration * weight / total_weight
            expanded.append({"text": part, "start": cursor, "end": cursor + part_duration})
            cursor += part_duration
    for index in range(len(expanded) - 1):
        expanded[index]["end"] = max(expanded[index]["end"], expanded[index + 1]["start"])
    return expanded


def paragraph_token_matches() -> list[tuple[int, re.Match[str]]]:
    return [
        (paragraph_index, match)
        for paragraph_index, paragraph in enumerate(PARAGRAPHS)
        for match in TOKEN_RE.finditer(paragraph["text"])
    ]


def align_words(boundaries: list[dict]) -> list[dict]:
    matches = paragraph_token_matches()
    expanded = expand_boundaries(boundaries)
    display_tokens = [match.group(0) for _, match in matches]
    audio_tokens = [item["text"] for item in expanded]
    if len(display_tokens) != len(audio_tokens):
        raise RuntimeError(
            f"word boundary count mismatch: display={len(display_tokens)} audio={len(audio_tokens)}\n"
            f"display={display_tokens}\naudio={audio_tokens}"
        )
    for index, (display, audio) in enumerate(zip(display_tokens, audio_tokens)):
        if normalise_token(display) != normalise_token(audio):
            raise RuntimeError(f"word boundary mismatch at {index}: display={display!r} audio={audio!r}")

    ipa = make_ipa(display_tokens)
    aligned = []
    for index, ((paragraph_index, match), timing, phonetic) in enumerate(zip(matches, expanded, ipa)):
        aligned.append(
            {
                "index": index,
                "paragraph": paragraph_index,
                "word": match.group(0),
                "start_char": match.start(),
                "end_char": match.end(),
                "start": round(timing["start"], 3),
                "end": round(timing["end"], 3),
                "ipa": phonetic,
            }
        )
    return aligned


def build_cards(words: list[dict]) -> str:
    cards = []
    for paragraph_index, paragraph in enumerate(PARAGRAPHS):
        paragraph_words = [item for item in words if item["paragraph"] == paragraph_index]
        cursor = 0
        text_fragments = []
        for item in paragraph_words:
            text_fragments.append(html.escape(paragraph["text"][cursor : item["start_char"]]))
            label = f"{item['word']}, {item['ipa']}"
            text_fragments.append(
                f'<button class="word-unit" type="button" data-word-index="{item["index"]}" '
                f'data-start="{item["start"]}" data-end="{item["end"]}" '
                f'aria-label="{html.escape(label, quote=True)}">'
                f'<span class="word-text">{html.escape(item["word"])}</span>'
                f'<span class="word-ipa">/{html.escape(item["ipa"])}/</span></button>'
            )
            cursor = item["end_char"]
        text_fragments.append(html.escape(paragraph["text"][cursor:]))
        start = paragraph_words[0]["start"]
        end = paragraph_words[-1]["end"]
        cards.append(
            f'''<article class="paragraph-card" data-paragraph="{paragraph_index}">
  <header class="paragraph-header">
    <div><span class="paragraph-number">{paragraph_index + 1:02d}</span>
      <h2>{html.escape(paragraph["title"])}</h2><p>{html.escape(paragraph["title_zh"])}</p></div>
    <button class="play-paragraph" type="button" data-start="{start}" data-end="{end}" aria-label="播放本段">▶ 本段</button>
  </header>
  <p class="annotated-text">{''.join(text_fragments)}</p>
</article>'''
        )
    return "\n".join(cards)


HTML_TEMPLATE = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#082f49">
  <meta name="description" content="Tao Ding English self-introduction with British male audio and word-by-word IPA">
  <link rel="icon" href="../icons/icon-192.png">
  <link rel="apple-touch-icon" href="../icons/icon-192.png">
  <title>Tao Ding · Self-introduction pronunciation player</title>
  <style>
    :root { --navy:#082f49; --blue:#075985; --teal:#0f766e; --mint:#ccfbf1; --ink:#0f172a; --muted:#64748b; --line:#dbe7ef; --paper:#f8fafc; --active:#fef3c7; }
    * { box-sizing:border-box; }
    html { scroll-behavior:smooth; }
    body { margin:0; color:var(--ink); background:linear-gradient(180deg,#e8f4f8 0,#f8fafc 360px); font-family:Inter,"Segoe UI",Arial,sans-serif; }
    button, audio, input { font:inherit; }
    .shell { width:min(920px,100%); margin:0 auto; padding:18px 16px 72px; }
    .hero { position:relative; overflow:hidden; padding:28px 24px; border-radius:28px; color:white; background:linear-gradient(135deg,#082f49,#075985 62%,#0f766e); box-shadow:0 20px 52px rgba(8,47,73,.22); }
    .hero::after { content:""; position:absolute; width:220px; height:220px; right:-95px; top:-105px; border:38px solid rgba(255,255,255,.09); border-radius:50%; }
    .eyebrow { margin:0 0 10px; color:#99f6e4; font-size:12px; font-weight:800; letter-spacing:.18em; text-transform:uppercase; }
    h1 { margin:0; max-width:680px; font-size:clamp(28px,7vw,46px); line-height:1.05; letter-spacing:-.035em; }
    .hero-copy { margin:14px 0 0; max-width:650px; color:#dbeafe; font-size:15px; line-height:1.7; }
    .badges { display:flex; flex-wrap:wrap; gap:8px; margin-top:18px; }
    .badge { padding:7px 11px; border:1px solid rgba(255,255,255,.24); border-radius:999px; background:rgba(255,255,255,.1); font-size:12px; font-weight:700; }
    .player { position:sticky; z-index:20; top:8px; margin:18px 0; padding:16px; border:1px solid rgba(148,163,184,.3); border-radius:22px; background:rgba(255,255,255,.94); box-shadow:0 14px 36px rgba(15,23,42,.14); backdrop-filter:blur(14px); }
    .player-top { display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:12px; }
    .player-title strong { display:block; font-size:15px; }
    .player-title span { color:var(--muted); font-size:12px; }
    .download { color:var(--teal); font-size:13px; font-weight:800; text-decoration:none; }
    audio { display:block; width:100%; height:42px; }
    .controls { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:10px; margin-top:12px; }
    .action-row, .rate-row { display:flex; align-items:center; gap:7px; }
    .action, .rate, .play-paragraph { border:0; border-radius:12px; cursor:pointer; font-weight:800; }
    .action { padding:10px 13px; color:white; background:var(--blue); }
    .action.secondary { color:var(--blue); background:#e0f2fe; }
    .rate { min-width:52px; padding:9px 10px; color:#475569; background:#eef2f7; }
    .rate.is-active { color:white; background:var(--teal); }
    .instructions { display:flex; gap:10px; align-items:flex-start; margin:18px 2px; padding:14px 16px; color:#334155; border-radius:16px; background:#ecfeff; font-size:13px; line-height:1.65; }
    .instructions strong { color:var(--teal); }
    .paragraph-list { display:grid; gap:14px; }
    .paragraph-card { padding:20px; border:1px solid var(--line); border-radius:22px; background:white; box-shadow:0 8px 24px rgba(15,23,42,.05); transition:.2s ease; }
    .paragraph-card.is-active { border-color:#14b8a6; box-shadow:0 0 0 3px rgba(20,184,166,.12),0 12px 28px rgba(15,23,42,.08); }
    .paragraph-header { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; padding-bottom:14px; border-bottom:1px solid #edf2f7; }
    .paragraph-header > div { display:grid; grid-template-columns:auto 1fr; column-gap:10px; align-items:center; }
    .paragraph-number { grid-row:1/3; display:grid; place-items:center; width:38px; height:38px; border-radius:12px; color:var(--teal); background:var(--mint); font-size:12px; font-weight:900; }
    .paragraph-header h2 { margin:0; font-size:17px; line-height:1.2; }
    .paragraph-header p { margin:3px 0 0; color:var(--muted); font-size:12px; }
    .play-paragraph { flex:0 0 auto; padding:9px 11px; color:var(--teal); background:#ecfdf5; }
    .annotated-text { margin:18px 0 2px; font-family:"Segoe UI",Arial,sans-serif; font-size:0; line-height:1.2; }
    .annotated-text > .word-unit { margin-right:5px; margin-bottom:10px; }
    .word-unit { display:inline-flex; flex-direction:column; align-items:center; vertical-align:top; min-height:48px; padding:5px 5px 4px; color:inherit; border:1px solid transparent; border-radius:9px; background:transparent; cursor:pointer; transition:.12s ease; }
    .word-unit:hover, .word-unit:focus-visible { border-color:#99f6e4; background:#f0fdfa; outline:none; }
    .word-unit.is-active { color:#713f12; border-color:#f59e0b; background:var(--active); transform:translateY(-1px); }
    .word-text { font-size:17px; font-weight:650; line-height:1.25; letter-spacing:-.01em; }
    .word-ipa { margin-top:3px; color:#0f766e; font-family:"Segoe UI",Arial,sans-serif; font-size:12px; font-weight:500; line-height:1.15; white-space:nowrap; }
    .word-unit.is-active .word-ipa { color:#92400e; }
    .footer { margin:24px 0 0; color:var(--muted); text-align:center; font-size:12px; line-height:1.6; }
    .footer a { color:var(--teal); font-weight:700; }
    @media (max-width:560px) {
      .shell { padding:10px 10px 56px; }
      .hero { padding:24px 20px; border-radius:22px; }
      .player { position:static; top:auto; margin:12px 0; padding:13px; border-radius:18px; }
      .player-top { align-items:flex-start; }
      .controls { align-items:flex-start; }
      .paragraph-card { padding:16px 13px; border-radius:18px; }
      .paragraph-header { gap:8px; }
      .play-paragraph { padding:8px 9px; font-size:12px; }
      .annotated-text > .word-unit { margin-right:3px; margin-bottom:8px; }
      .word-unit { padding:4px 3px; }
      .word-text { font-size:16px; }
      .word-ipa { font-size:12px; }
    }
    @media (prefers-reduced-motion:reduce) { * { scroll-behavior:auto!important; transition:none!important; } }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <p class="eyebrow">Listening + Pronunciation</p>
      <h1>Tao Ding’s English self-introduction</h1>
      <p class="hero-copy">固定英国男声朗读，全文逐词显示英式 IPA。播放时当前单词会自动高亮，也可以点击任意单词从该位置开始听。</p>
      <div class="badges"><span class="badge">Ryan · British English · Male</span><span class="badge">__WORD_COUNT__ words</span><span class="badge">逐词音标</span></div>
    </section>

    <section class="player" aria-label="音频播放器">
      <div class="player-top"><div class="player-title"><strong>英语自我介绍 · 完整音频</strong><span id="statusText">默认 0.75×，适合听力训练</span></div><a class="download" href="./self-introduction.mp3" download>下载 MP3</a></div>
      <audio id="audio" controls preload="metadata" src="./self-introduction.mp3"></audio>
      <div class="controls">
        <div class="action-row"><button class="action" id="playAll" type="button">▶ 从头播放</button><button class="action secondary" id="restart" type="button">↺ 重播</button></div>
        <div class="rate-row" aria-label="语速"><button class="rate" type="button" data-rate="0.5">0.5×</button><button class="rate is-active" type="button" data-rate="0.75">0.75×</button><button class="rate" type="button" data-rate="1">1.0×</button></div>
      </div>
    </section>

    <aside class="instructions"><span aria-hidden="true">💡</span><div><strong>使用方法：</strong>先用 0.75× 跟读；听不清时切到 0.5×。点击“本段”只练一个段落，点击任意单词可从该词开始播放。</div></aside>
    <section class="paragraph-list" aria-label="逐词音标文本">__CARDS__</section>
    <p class="footer">英式 IPA 由 eSpeak NG 生成，姓名、地名、缩写及专业词汇已人工校正。<br><a href="../">返回 Kessler Research English</a></p>
  </main>
  <script>
    const audio = document.getElementById("audio");
    const words = [...document.querySelectorAll(".word-unit")];
    const paragraphs = [...document.querySelectorAll(".paragraph-card")];
    const statusText = document.getElementById("statusText");
    let activeWord = null;
    let activeParagraph = null;
    let clipEnd = null;

    function setRate(rate) {
      audio.playbackRate = rate;
      audio.preservesPitch = true;
      document.querySelectorAll(".rate").forEach((button) => button.classList.toggle("is-active", Number(button.dataset.rate) === rate));
      statusText.textContent = `当前语速 ${rate.toFixed(rate === 1 ? 1 : 2).replace(/0$/, "")}× · Ryan 英国男声`;
    }

    function updateHighlight() {
      const time = audio.currentTime;
      const next = words.find((word) => time >= Number(word.dataset.start) && time < Number(word.dataset.end));
      if (next !== activeWord) {
        activeWord?.classList.remove("is-active");
        activeWord = next || null;
        activeWord?.classList.add("is-active");
        const paragraph = activeWord?.closest(".paragraph-card") || null;
        if (paragraph !== activeParagraph) {
          activeParagraph?.classList.remove("is-active");
          activeParagraph = paragraph;
          activeParagraph?.classList.add("is-active");
        }
      }
      if (clipEnd !== null && time >= clipEnd) {
        audio.pause();
        clipEnd = null;
      }
    }

    setRate(0.75);
    audio.addEventListener("timeupdate", updateHighlight);
    audio.addEventListener("seeked", updateHighlight);
    audio.addEventListener("ended", () => { clipEnd = null; });

    document.querySelectorAll(".rate").forEach((button) => button.addEventListener("click", () => setRate(Number(button.dataset.rate))));
    document.getElementById("playAll").addEventListener("click", () => { clipEnd = null; audio.currentTime = 0; audio.play(); });
    document.getElementById("restart").addEventListener("click", () => { audio.currentTime = clipEnd === null ? 0 : Math.max(0, audio.currentTime - 4); audio.play(); });
    document.querySelectorAll(".play-paragraph").forEach((button) => button.addEventListener("click", () => {
      audio.currentTime = Number(button.dataset.start);
      clipEnd = Number(button.dataset.end);
      audio.play();
    }));
    words.forEach((word) => word.addEventListener("click", () => {
      clipEnd = null;
      audio.currentTime = Number(word.dataset.start);
      audio.play();
    }));
  </script>
</body>
</html>
'''


async def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    full_text = "\n\n".join(item["text"] for item in PARAGRAPHS)
    audio_path = OUTPUT / "self-introduction.mp3"
    boundaries = await generate_audio(full_text, audio_path)
    words = align_words(boundaries)

    payload = {
        "voice": VOICE,
        "language": "en-GB",
        "source": "英语自我介绍.docx",
        "wordCount": len(words),
        "audioBytes": audio_path.stat().st_size,
        "paragraphs": PARAGRAPHS,
        "words": words,
    }
    (OUTPUT / "self-introduction.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    page = HTML_TEMPLATE.replace("__WORD_COUNT__", str(len(words))).replace("__CARDS__", build_cards(words))
    (OUTPUT / "index.html").write_text(page, encoding="utf-8")
    print(
        json.dumps(
            {
                "voice": VOICE,
                "words": len(words),
                "audioBytes": audio_path.stat().st_size,
                "boundaries": len(boundaries),
                "output": str(OUTPUT),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
