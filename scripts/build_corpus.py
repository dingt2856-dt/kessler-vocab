#!/usr/bin/env python3
"""Build a verified Benedikt Kessler title-and-abstract corpus.

Primary discovery source: Europe PMC AUTHORID query for ORCID
0000-0002-8160-2446. ORCID's public API is used for corpus inventory.
No full text is downloaded.
"""

from __future__ import annotations

import csv
import html
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ORCID = "0000-0002-8160-2446"
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data"
USER_AGENT = "KesslerResearchEnglish/1.0 (personal research vocabulary project)"

BAD_TYPES = {
    "preprint",
    "published erratum",
    "erratum",
    "correction",
    "retraction of publication",
    "retracted publication",
    "editorial",
    "letter",
    "comment",
    "news",
    "abstract",
    "conference abstract",
    "article-commentary",
    "introductory journal article",
}

ALLOWED_TYPES = {
    "journal article",
    "research-article",
    "review",
    "review-article",
    "brief-report",
    "report",
    "comparative study",
    "evaluation study",
    "validation study",
    "observational study",
    "randomized controlled trial",
    "clinical trial",
    "multicenter study",
    "case reports",
    "case-report",
}


def fetch_json(url: str, attempts: int = 4) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - network dependent
            last_error = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"Unable to fetch {url}: {last_error}")


def clean_html_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"</?(?:title|h[1-6]|p|sec|bold|italic)[^>]*>", " ", value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = value.replace("\u00ad", "").replace("\xa0", " ")
    return re.sub(r"\s+", " ", value).strip()


def normalized_doi(value: str | None) -> str:
    if not value:
        return ""
    value = value.strip().lower()
    value = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value)
    return value.rstrip(". ")


def normalized_title(value: str | None) -> str:
    text = clean_html_text(value).lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def pub_types(record: dict[str, Any]) -> list[str]:
    container = record.get("pubTypeList") or {}
    return [str(x).strip() for x in as_list(container.get("pubType")) if str(x).strip()]


def has_target_orcid(record: dict[str, Any]) -> bool:
    ids = as_list((record.get("authorIdList") or {}).get("authorId"))
    for author_id in ids:
        if isinstance(author_id, dict) and str(author_id.get("value", "")).strip() == ORCID:
            return True
    authors = as_list((record.get("authorList") or {}).get("author"))
    for author in authors:
        if not isinstance(author, dict):
            continue
        author_id = author.get("authorId") or {}
        if str(author_id.get("value", "")).strip() == ORCID:
            return True
    return False


def crossref_abstract(doi: str) -> str:
    if not doi:
        return ""
    encoded = urllib.parse.quote(doi, safe="")
    try:
        payload = fetch_json(f"https://api.crossref.org/works/{encoded}", attempts=2)
        return clean_html_text((payload.get("message") or {}).get("abstract"))
    except Exception:
        return ""


def record_score(record: dict[str, Any]) -> tuple[int, int, int]:
    abstract = clean_html_text(record.get("abstractText"))
    return (
        1 if record.get("pmid") else 0,
        1 if normalized_doi(record.get("doi")) else 0,
        len(abstract),
    )


def corpus_key(record: dict[str, Any]) -> str:
    doi = normalized_doi(record.get("doi"))
    if doi:
        return f"doi:{doi}"
    pmid = str(record.get("pmid") or "").strip()
    if pmid:
        return f"pmid:{pmid}"
    year = str(record.get("pubYear") or "").strip()
    return f"title:{normalized_title(record.get('title'))}:{year}"


def journal_name(record: dict[str, Any]) -> str:
    info = record.get("journalInfo") or {}
    journal = info.get("journal") or {}
    return str(journal.get("title") or journal.get("medlineAbbreviation") or "").strip()


def keywords(record: dict[str, Any]) -> list[str]:
    values = as_list((record.get("keywordList") or {}).get("keyword"))
    return sorted({clean_html_text(str(value)) for value in values if clean_html_text(str(value))})


def mesh_terms(record: dict[str, Any]) -> list[str]:
    result: list[str] = []
    headings = as_list((record.get("meshHeadingList") or {}).get("meshHeading"))
    for heading in headings:
        if isinstance(heading, dict):
            name = clean_html_text(str(heading.get("descriptorName") or ""))
            if name:
                result.append(name)
    return sorted(set(result))


def exclusion_reason(record: dict[str, Any]) -> str:
    types = {item.lower() for item in pub_types(record)}
    if not has_target_orcid(record):
        return "target ORCID not present in returned author identifiers"
    if record.get("source") == "PPR" or "preprint" in types:
        return "preprint"
    bad = sorted(types.intersection(BAD_TYPES))
    if bad:
        return f"excluded publication type: {', '.join(bad)}"
    if not types.intersection(ALLOWED_TYPES):
        return f"unsupported publication type: {', '.join(sorted(types)) or 'missing'}"
    if len(clean_html_text(record.get("title"))) < 8:
        return "missing or invalid title"
    return ""


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    orcid_payload = fetch_json(f"https://pub.orcid.org/v3.0/{ORCID}/works")
    query = urllib.parse.quote(f"AUTHORID:{ORCID}")
    epmc_url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        f"?query={query}&format=json&pageSize=1000&resultType=core"
    )
    epmc_payload = fetch_json(epmc_url)

    (RAW_DIR / "orcid_works.json").write_text(
        json.dumps(orcid_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (RAW_DIR / "europe_pmc_core.json").write_text(
        json.dumps(epmc_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    raw_records = as_list((epmc_payload.get("resultList") or {}).get("result"))
    excluded: list[dict[str, str]] = []
    candidates: list[dict[str, Any]] = []

    for record in raw_records:
        reason = exclusion_reason(record)
        if reason:
            excluded.append(
                {
                    "id": str(record.get("id") or ""),
                    "doi": normalized_doi(record.get("doi")),
                    "title": clean_html_text(record.get("title")),
                    "year": str(record.get("pubYear") or ""),
                    "reason": reason,
                }
            )
            continue

        abstract = clean_html_text(record.get("abstractText"))
        if len(abstract) < 80:
            abstract = crossref_abstract(normalized_doi(record.get("doi")))
        if len(abstract) < 80:
            excluded.append(
                {
                    "id": str(record.get("id") or ""),
                    "doi": normalized_doi(record.get("doi")),
                    "title": clean_html_text(record.get("title")),
                    "year": str(record.get("pubYear") or ""),
                    "reason": "no usable English abstract",
                }
            )
            continue

        item = dict(record)
        item["cleanAbstract"] = abstract
        candidates.append(item)

    # Prefer the richest record when multiple sources describe the same paper.
    deduped: dict[str, dict[str, Any]] = {}
    duplicate_count = 0
    for record in sorted(candidates, key=record_score, reverse=True):
        key = corpus_key(record)
        if key in deduped:
            duplicate_count += 1
            excluded.append(
                {
                    "id": str(record.get("id") or ""),
                    "doi": normalized_doi(record.get("doi")),
                    "title": clean_html_text(record.get("title")),
                    "year": str(record.get("pubYear") or ""),
                    "reason": f"duplicate of {key}",
                }
            )
        else:
            deduped[key] = record

    publications: list[dict[str, Any]] = []
    for index, (key, record) in enumerate(
        sorted(
            deduped.items(),
            key=lambda pair: (
                -int(str(pair[1].get("pubYear") or "0")[:4] or 0),
                clean_html_text(pair[1].get("title")).lower(),
            ),
        ),
        start=1,
    ):
        publications.append(
            {
                "corpusId": f"BK{index:04d}",
                "dedupeKey": key,
                "title": clean_html_text(record.get("title")),
                "abstract": record["cleanAbstract"],
                "year": str(record.get("pubYear") or ""),
                "journal": journal_name(record),
                "doi": normalized_doi(record.get("doi")),
                "pmid": str(record.get("pmid") or ""),
                "europePmcId": str(record.get("id") or ""),
                "source": str(record.get("source") or ""),
                "authors": clean_html_text(record.get("authorString")),
                "publicationTypes": pub_types(record),
                "keywords": keywords(record),
                "meshTerms": mesh_terms(record),
                "isOpenAccess": str(record.get("isOpenAccess") or "N") == "Y",
            }
        )

    orcid_groups = as_list(orcid_payload.get("group"))
    orcid_type_counts: Counter[str] = Counter()
    for group in orcid_groups:
        summaries = as_list(group.get("work-summary") if isinstance(group, dict) else None)
        if summaries:
            orcid_type_counts[str(summaries[0].get("type") or "unknown")] += 1

    meta = {
        "generatedAt": timestamp,
        "targetAuthor": "Benedikt M. Kessler",
        "orcid": ORCID,
        "sourceQuery": f"Europe PMC AUTHORID:{ORCID}",
        "orcidWorkGroups": len(orcid_groups),
        "orcidWorkTypes": dict(sorted(orcid_type_counts.items())),
        "europePmcHitCount": int(epmc_payload.get("hitCount") or len(raw_records)),
        "europePmcReturned": len(raw_records),
        "includedPublications": len(publications),
        "excludedRecords": len(excluded),
        "duplicatesRemoved": duplicate_count,
        "textScope": "titles and abstracts only",
        "abstractPolicy": "used for term extraction; not redistributed as full text in the PWA",
    }
    bundle = {"meta": meta, "publications": publications}
    (OUT_DIR / "publications.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    with (OUT_DIR / "publications.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["corpusId", "year", "title", "journal", "doi", "pmid", "source"],
        )
        writer.writeheader()
        for item in publications:
            writer.writerow({field: item[field] for field in writer.fieldnames})

    with (OUT_DIR / "excluded_records.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "year", "title", "doi", "reason"])
        writer.writeheader()
        writer.writerows(excluded)

    reason_counts = Counter(item["reason"] for item in excluded)
    report_lines = [
        "# Benedikt Kessler Corpus Report",
        "",
        f"Generated: {timestamp}",
        "",
        "## Identity and sources",
        "",
        f"- Target author: Benedikt M. Kessler",
        f"- ORCID: `{ORCID}`",
        f"- ORCID work groups: {len(orcid_groups)}",
        f"- Europe PMC exact-ORCID hits: {len(raw_records)}",
        "- Text scope: titles and abstracts only",
        "",
        "## Outcome",
        "",
        f"- Included unique publications with usable abstracts: **{len(publications)}**",
        f"- Excluded or duplicate records: **{len(excluded)}**",
        f"- Duplicate records removed: **{duplicate_count}**",
        "",
        "## Exclusion reasons",
        "",
        "| Reason | Count |",
        "|---|---:|",
    ]
    report_lines.extend(
        f"| {reason.replace('|', '/')} | {count} |"
        for reason, count in reason_counts.most_common()
    )
    report_lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Inclusion is based on exact ORCID attribution in Europe PMC, not name-only matching.",
            "- Preprints, corrections, errata, editorials, letters, comments, and unsupported types are excluded.",
            "- Abstracts are analyzed for vocabulary but are not republished in the learning application.",
            "- The corpus is a dated public-metadata snapshot and can be rebuilt later.",
            "",
        ]
    )
    (OUT_DIR / "corpus_report.md").write_text("\n".join(report_lines), encoding="utf-8")

    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
