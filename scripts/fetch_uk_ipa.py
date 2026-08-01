#!/usr/bin/env python3
"""Fetch English RP/UK IPA from Wiktionary for meeting-tier terms.

The output is a small derived pronunciation dataset. Wiktionary content is
available under CC BY-SA; attribution is displayed in the app.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from build_learning_content import CUSTOM_IPA, PHRASE_DATA, WORD_DATA, parse_rows


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
USER_AGENT = "KesslerResearchEnglish/1.0 (personal educational project)"


def fetch_pages(titles: list[str]) -> dict[str, str]:
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "titles": "|".join(titles),
            "format": "json",
            "formatversion": "2",
        }
    )
    request = urllib.request.Request(
        f"https://en.wiktionary.org/w/api.php?{params}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = {}
    for page in (payload.get("query") or {}).get("pages", []):
        revisions = page.get("revisions") or []
        if not revisions:
            continue
        text = ((revisions[0].get("slots") or {}).get("main") or {}).get("content") or ""
        result[str(page.get("title") or "").lower()] = text
    return result


def english_section(wikitext: str) -> str:
    match = re.search(r"^==English==\s*$", wikitext, flags=re.M)
    if not match:
        return ""
    rest = wikitext[match.end() :]
    next_language = re.search(r"^==[^=].*?==\s*$", rest, flags=re.M)
    return rest[: next_language.start()] if next_language else rest


def extract_ipa(wikitext: str) -> str:
    section = english_section(wikitext)
    lines = [line for line in section.splitlines() if "{{IPA|en|" in line]
    if not lines:
        return ""
    preferred = []
    generic = []
    for line in lines:
        lower = line.lower()
        if any(tag in lower for tag in ("a=ga", "a=us", "a=canada", "a=ca")) and not any(
            tag in lower for tag in ("a=rp", "a=uk", "a=britain", "a=england")
        ):
            continue
        values = re.findall(r"/[^/{|}]+/", line)
        if not values:
            continue
        if any(tag in lower for tag in ("a=rp", "a=uk", "a=britain", "a=england")):
            preferred.extend(values)
        elif "a=" not in lower:
            generic.extend(values)
    return (preferred or generic or [""])[0]


def clean_token(value: str) -> str:
    return re.sub(r"[^A-Za-z]", "", value).lower()


def main() -> None:
    words = [row[0] for row in parse_rows(WORD_DATA, 4)]
    phrases = [row[0] for row in parse_rows(PHRASE_DATA, 3)]
    phrase_tokens = []
    for phrase in phrases:
        phrase_tokens.extend(clean_token(token) for token in re.split(r"[\s/-]+", phrase))
    titles = sorted({word.lower() for word in words if word.isalpha()} | {token for token in phrase_tokens if token})

    pages: dict[str, str] = {}
    for index in range(0, len(titles), 40):
        batch = titles[index : index + 40]
        pages.update(fetch_pages(batch))
        time.sleep(0.35)

    token_ipa = {title: extract_ipa(text) for title, text in pages.items()}
    token_ipa = {title: value for title, value in token_ipa.items() if value}
    for term, value in CUSTOM_IPA.items():
        if term.isalpha():
            token_ipa[term.lower()] = value
    result: dict[str, str] = {}

    for term in words:
        if term in CUSTOM_IPA:
            result[term] = CUSTOM_IPA[term]
            continue
        value = token_ipa.get(term.lower(), "")
        if value:
            result[term] = value

    for phrase in phrases:
        if phrase in CUSTOM_IPA:
            result[phrase] = CUSTOM_IPA[phrase]
            continue
        if phrase == "LC-MS/MS":
            result[phrase] = CUSTOM_IPA[phrase]
            continue
        parts = []
        complete = True
        for token in re.split(r"[\s/-]+", phrase):
            clean = clean_token(token)
            value = token_ipa.get(clean, "")
            if not value:
                complete = False
                break
            parts.append(value.strip("/"))
        if complete and parts:
            result[phrase] = f"/{' '.join(parts)}/"

    payload = {
        "_meta": {
            "source": "English Wiktionary plus curated technical overrides",
            "license": "Wiktionary CC BY-SA 4.0",
            "retrieved": "2026-07-31",
            "termsRequested": len(words) + len(phrases),
            "termsResolved": len(result),
        },
        **result,
    }
    (DATA / "uk_ipa.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload["_meta"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
