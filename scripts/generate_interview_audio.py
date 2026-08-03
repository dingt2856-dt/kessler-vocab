#!/usr/bin/env python3
"""Generate the fixed British male audio used by the mock interview."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import edge_tts


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "app" / "audio" / "interview"
VOICE = "en-GB-RyanNeural"

QUESTIONS = {
    "introduction": "Good morning, Tao. Thank you for meeting with me. Could you briefly introduce yourself and describe your current research?",
    "lactylome-objective": "Could you give me a short overview of your C. elegans lactylome study, and explain its main objective?",
    "lactylome-methods": "How did you prepare the samples and identify the lactylated peptides by mass spectrometry?",
    "lactylome-findings": "What was the most important finding, and how did you assess the reliability of the lactylation sites?",
    "mass-spec-experience": "Which mass spectrometers and acquisition strategies have you used most independently?",
    "technical-problem": "Please describe one technical problem you encountered in a proteomics experiment, and explain how you solved it.",
    "motivation": "Why are you interested in visiting my group at Oxford?",
    "visit-project": "What research question would you like to address during a three-to-six-month visit?",
    "contribution": "How would your experience in lactylation, phosphoproteomics, or single-cell multi-omics contribute to our work?",
    "funding": "How would your visit be funded, and are there any conditions attached to that funding?",
    "availability": "When would you be available to start, and how long could you stay in Oxford?",
    "questions": "Finally, what questions would you like to ask me about the project or the group?",
    "introduction-follow-up": "Could you tell me more specifically how your current work relates to mass spectrometry-based proteomics?",
    "lactylome-objective-follow-up": "What biological question were you trying to answer with the lactylome study?",
    "lactylome-methods-follow-up": "Which step in the experimental workflow was the most technically demanding for you?",
    "lactylome-findings-follow-up": "How did you distinguish a reliable lactylation site from a possible false positive?",
    "mass-spec-experience-follow-up": "Could you name the instrument and software that you can operate most confidently?",
    "motivation-follow-up": "Which aspect of our work on ubiquitin or protease biology is most relevant to your research goals?",
    "visit-project-follow-up": "What specific result would you hope to achieve by the end of a short visit?",
    "funding-follow-up": "Would the funding cover your travel, accommodation, and living costs in Oxford?",
    "availability-follow-up": "How flexible would you be if the laboratory needed to adjust the starting date?",
}

PRACTICE = {
    "practice-introduction": "My research focuses on mass spectrometry-based proteomics, particularly protein lactylation and phosphoproteomics.",
    "practice-lactylome-objective": "The main objective of our study was to characterise the lactylome of C. elegans and explore its potential biological significance.",
    "practice-lactylome-methods": "We prepared the samples carefully and used mass spectrometry-based analysis to identify lactylated peptides and modification sites.",
    "practice-lactylome-findings": "Our most important finding was that lactylation may be associated with specific biological processes in C. elegans.",
    "practice-mass-spec": "I have hands-on experience in proteomic sample preparation, mass spectrometry data acquisition, and downstream data analysis.",
    "practice-motivation": "I am particularly interested in your group's expertise in ubiquitin biology, proteases, and mass spectrometry-based proteomics.",
    "practice-visit-project": "During the visit, I hope to develop a focused and feasible project that complements the group's current priorities.",
    "practice-funding": "I plan to apply for funding from the China Scholarship Council, subject to the relevant approval requirements.",
    "practice-availability": "I am flexible about the starting date and would be available for a research visit of three to six months.",
    "practice-questions": "Could you please advise me which research direction would be most useful for your group at present?",
}

ALL_AUDIO = {
    "preview": "Good morning, Tao. Thank you for meeting with me today.",
    **QUESTIONS,
    **PRACTICE,
}


async def generate_one(identifier: str, text: str) -> dict[str, str | int]:
    destination = OUTPUT / f"{identifier}.mp3"
    if not destination.exists() or destination.stat().st_size < 1_000:
        last_error: Exception | None = None
        for attempt in range(1, 5):
            try:
                destination.unlink(missing_ok=True)
                communicate = edge_tts.Communicate(text, VOICE, rate="+0%", volume="+0%", pitch="+0Hz")
                await communicate.save(str(destination))
                if destination.stat().st_size < 1_000:
                    raise RuntimeError("generated audio is unexpectedly small")
                last_error = None
                break
            except Exception as error:  # network synthesis occasionally closes early
                last_error = error
                await asyncio.sleep(attempt * 1.5)
        if last_error is not None:
            raise last_error
    return {
        "id": identifier,
        "file": destination.name,
        "text": text,
        "bytes": destination.stat().st_size,
    }


async def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    records = []
    for identifier, text in ALL_AUDIO.items():
        records.append(await generate_one(identifier, text))
        print(f"generated {identifier}.mp3")
    manifest = {
        "voice": VOICE,
        "format": "audio/mpeg",
        "generatedFiles": len(records),
        "items": records,
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"generated {len(records)} files with {VOICE}")


if __name__ == "__main__":
    asyncio.run(main())
