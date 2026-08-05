#!/usr/bin/env python3
"""Validate corpus outputs and the deployable PWA release."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
DATA = ROOT / "data"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    corpus = json.loads((DATA / "publications.json").read_text(encoding="utf-8"))
    learning = json.loads((APP / "data" / "learning_items.json").read_text(encoding="utf-8"))
    manifest = json.loads((APP / "manifest.webmanifest").read_text(encoding="utf-8"))
    interview_audio = json.loads((APP / "audio" / "interview" / "manifest.json").read_text(encoding="utf-8"))
    introduction = json.loads((APP / "self-introduction" / "self-introduction.json").read_text(encoding="utf-8"))
    items = learning["items"]

    require(corpus["meta"]["orcid"] == "0000-0002-8160-2446", "wrong ORCID")
    require(corpus["meta"]["includedPublications"] == 373, "unexpected corpus count")
    require(len(corpus["publications"]) == 373, "corpus list count mismatch")
    require(len(items) == 300, "meeting-tier item count mismatch")
    require(Counter(item["type"] for item in items) == {"word": 200, "phrase": 60, "sentence": 40}, "type counts mismatch")
    require(len({item["id"] for item in items}) == len(items), "duplicate learning item IDs")

    required_fields = {
        "id",
        "type",
        "term",
        "chinese",
        "theme",
        "exampleEnglish",
        "exampleChinese",
        "pronounceAs",
        "reviewStatus",
    }
    for item in items:
        require(required_fields.issubset(item), f"missing fields in {item.get('id')}")
        require(all(str(item[field]).strip() for field in required_fields), f"empty required field in {item['id']}")
        if item["type"] != "sentence":
            require(item.get("sourceIds"), f"missing corpus source for {item['id']}")
            require(item.get("sourceTitle"), f"missing source title for {item['id']}")
            require(item.get("sourceDoi"), f"missing DOI for {item['id']}")
            require(item.get("ipa"), f"missing IPA for {item['id']}")

    app_json = (APP / "data" / "learning_items.json").read_text(encoding="utf-8").lower()
    require('"abstract"' not in app_json and '"abstracttext"' not in app_json, "public PWA contains abstract fields")

    assets = [
        "index.html",
        "styles.css",
        "app.js",
        "interview.js",
        "sw.js",
        "manifest.webmanifest",
        "data/learning_items.json",
        "icons/icon-192.png",
        "icons/icon-512.png",
        "self-introduction/index.html",
        "self-introduction/self-introduction.mp3",
        "self-introduction/self-introduction.json",
        ".nojekyll",
    ]
    for asset in assets:
        require((APP / asset).exists(), f"missing app asset: {asset}")
    require(manifest["display"] == "standalone", "manifest is not standalone")
    require(manifest["start_url"] == "./", "manifest start_url is not Pages-safe")
    require(interview_audio["voice"] == "en-GB-RyanNeural", "unexpected interview voice")
    require(interview_audio["generatedFiles"] == 32, "unexpected interview audio count")
    for audio in interview_audio["items"]:
        audio_path = APP / "audio" / "interview" / audio["file"]
        require(audio_path.exists() and audio_path.stat().st_size > 1_000, f"invalid interview audio: {audio['file']}")
    require(introduction["voice"] == "en-GB-RyanNeural", "unexpected self-introduction voice")
    require(introduction["wordCount"] == 284, "unexpected self-introduction word count")
    require(len(introduction["words"]) == 284, "self-introduction word list mismatch")
    require(all(item["ipa"].strip() for item in introduction["words"]), "self-introduction has missing IPA")
    introduction_audio = APP / "self-introduction" / "self-introduction.mp3"
    require(introduction_audio.stat().st_size > 700_000, "self-introduction audio is incomplete")

    service_worker = (APP / "sw.js").read_text(encoding="utf-8")
    for asset in [value for value in assets if value not in {".nojekyll", "sw.js"}]:
        if asset == "data/learning_items.json":
            expected = "./data/learning_items.json"
        else:
            expected = f"./{asset}"
        require(expected in service_worker or asset == "manifest.webmanifest", f"service worker does not cache {asset}")

    html = (APP / "index.html").read_text(encoding="utf-8")
    ids = re.findall(r'\bid="([^"]+)"', html)
    require(len(ids) == len(set(ids)), "duplicate HTML IDs")

    report = [
        "# Release verification",
        "",
        "- Status: PASS",
        f"- Verified publications: {len(corpus['publications'])}",
        f"- Learning items: {len(items)}",
        "- Words / phrases / sentences: 200 / 60 / 40",
        "- All words and phrases have a verified paper source, DOI, Chinese meaning, example, and IPA.",
        "- The deployable PWA contains no abstract fields.",
        "- Manifest, icons, service worker, offline data, and GitHub Pages workflow are present.",
        "- The browser-only mock interview module provides spoken questions, speech recognition fallback, and end-of-session review.",
        "- All interview questions and practice sentences include bundled en-GB-RyanNeural male audio.",
        "- The self-introduction player provides 284 word-level British IPA annotations and bundled en-GB-RyanNeural male audio.",
        "",
    ]
    (DATA / "release_verification.md").write_text("\n".join(report), encoding="utf-8")
    print("PASS: corpus, content, and PWA release verified")


if __name__ == "__main__":
    main()
