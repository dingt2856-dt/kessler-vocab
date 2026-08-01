#!/usr/bin/env python3
"""Generate auditable word and n-gram candidates from the verified corpus."""

from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

STOPWORDS = set(
    """
    a about above after again against all am an and any are aren't as at be because been
    before being below between both but by can cannot could couldn't did didn't do does
    doesn't doing don't down during each few for from further had hadn't has hasn't have
    haven't having he her here hers herself him himself his how i if in into is isn't it
    its itself just me more most mustn't my myself no nor not of off on once only or other
    ought our ours ourselves out over own same she should shouldn't so some such than that
    the their theirs them themselves then there these they this those through to too under
    until up very was wasn't we were weren't what when where which while who whom why will
    with won't would wouldn't you your yours yourself yourselves
    study studies result results method methods data analysis analyses approach approaches
    identify identifies identified identifying show shows showed shown showing demonstrate
    demonstrates demonstrated demonstrating suggest suggests suggested suggesting investigate
    investigates investigated investigating determine determines determined determining
    assess assesses assessed assessing evaluate evaluates evaluated evaluating examine
    examines examined examining include includes included including compare compares compared
    comparing associate associates associated associating relate relates related relating
    use uses used using via based level levels group groups role roles effect effects
    significant significantly respectively however therefore furthermore together overall
    here herein aim aims aimed investigate novel new first previous previously present
    current currently recent recently provide provides provided providing reveal reveals
    revealed revealing find finds found finding observed observations whether whereas
    well also either both may might can could would should among across within without
    following followed likely important major several different various high low higher lower
    one two three four five six seven eight nine ten
    """.split()
)

TOKEN_RE = re.compile(r"[a-z][a-z0-9]*(?:[-'][a-z0-9]+)*", re.I)


def normalized_text(value: str) -> str:
    return (
        value.lower()
        .replace("β", " beta ")
        .replace("α", " alpha ")
        .replace("γ", " gamma ")
        .replace("κ", " kappa ")
        .replace("–", "-")
        .replace("—", "-")
    )


def tokens(value: str) -> list[str]:
    result = []
    for raw in TOKEN_RE.findall(normalized_text(value)):
        word = raw.strip("-'")
        if len(word) < 3 or word in STOPWORDS or word.isdigit():
            continue
        if re.fullmatch(r"[a-z]+\d*", word) is None:
            continue
        result.append(word)
    return result


def main() -> None:
    bundle = json.loads((DATA / "publications.json").read_text(encoding="utf-8"))
    publications = bundle["publications"]
    term_frequency: Counter[str] = Counter()
    doc_frequency: Counter[str] = Counter()
    sources: dict[str, list[str]] = defaultdict(list)
    ngram_tf: Counter[str] = Counter()
    ngram_df: Counter[str] = Counter()
    ngram_sources: dict[str, list[str]] = defaultdict(list)

    for pub in publications:
        doc_tokens = tokens(pub["title"] + " " + pub["abstract"])
        term_frequency.update(doc_tokens)
        for word in set(doc_tokens):
            doc_frequency[word] += 1
            if len(sources[word]) < 8:
                sources[word].append(pub["corpusId"])

        title_and_abstract = normalized_text(pub["title"] + ". " + pub["abstract"])
        sentence_tokens: list[list[str]] = []
        for sentence in re.split(r"[.!?;:]", title_and_abstract):
            sentence_tokens.append(tokens(sentence))
        document_ngrams: set[str] = set()
        for sequence in sentence_tokens:
            for size in (2, 3):
                for index in range(len(sequence) - size + 1):
                    gram_tokens = sequence[index : index + size]
                    if any(token in STOPWORDS for token in gram_tokens):
                        continue
                    gram = " ".join(gram_tokens)
                    ngram_tf[gram] += 1
                    document_ngrams.add(gram)
        for gram in document_ngrams:
            ngram_df[gram] += 1
            if len(ngram_sources[gram]) < 8:
                ngram_sources[gram].append(pub["corpusId"])

    total_docs = len(publications)
    word_rows = []
    for term, df in doc_frequency.items():
        tf = term_frequency[term]
        # Reward cross-document recurrence but keep specialist low-frequency terms visible.
        score = df * math.log2(tf + 2)
        word_rows.append(
            {
                "term": term,
                "documentFrequency": df,
                "termFrequency": tf,
                "documentShare": round(df / total_docs, 6),
                "score": round(score, 6),
                "sourceIds": ";".join(sources[term]),
            }
        )
    word_rows.sort(key=lambda row: (-row["score"], row["term"]))

    phrase_rows = []
    for term, df in ngram_df.items():
        tf = ngram_tf[term]
        if df < 2 or tf < 2:
            continue
        score = df * math.log2(tf + 2) * (1.15 if len(term.split()) == 3 else 1.0)
        phrase_rows.append(
            {
                "term": term,
                "documentFrequency": df,
                "termFrequency": tf,
                "score": round(score, 6),
                "sourceIds": ";".join(ngram_sources[term]),
            }
        )
    phrase_rows.sort(key=lambda row: (-row["score"], row["term"]))

    with (DATA / "word_candidates.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(word_rows[0]))
        writer.writeheader()
        writer.writerows(word_rows)
    with (DATA / "phrase_candidates.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(phrase_rows[0]))
        writer.writeheader()
        writer.writerows(phrase_rows)

    print(
        json.dumps(
            {
                "documents": total_docs,
                "wordCandidates": len(word_rows),
                "phraseCandidates": len(phrase_rows),
                "topWords": [row["term"] for row in word_rows[:30]],
                "topPhrases": [row["term"] for row in phrase_rows[:30]],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
