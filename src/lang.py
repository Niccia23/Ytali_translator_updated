from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Lang = Literal["it", "en", "unknown"]


@dataclass(frozen=True)
class LangDecision:
    detected: Lang
    source: Literal["Italian", "English"]
    target: Literal["Italian", "English"]


def _heuristic_it_score(text: str) -> int:
    t = text.lower()
    score = 0

    # Italian-specific characters/diacritics show up sometimes
    for ch in "àèéìòù":
        if ch in t:
            score += 2

    # Common Italian stop-words / function words
    it_words = [
        " il ",
        " lo ",
        " la ",
        " gli ",
        " le ",
        " un ",
        " una ",
        " che ",
        " non ",
        " per ",
        " con ",
        " come ",
        " anche ",
        " però ",
        " quindi ",
        " perché ",
        " del ",
        " della ",
        " dei ",
        " delle ",
        " nel ",
        " nella ",
        " nell'",
        " è ",
        " sono ",
    ]

    en_words = [
        " the ",
        " and ",
        " of ",
        " to ",
        " in ",
        " for ",
        " with ",
        " that ",
        " not ",
        " is ",
        " are ",
        " was ",
        " were ",
        " you ",
        " your ",
        " this ",
        " it ",
    ]

    padded = f" {t} "

    for w in it_words:
        if w in padded:
            score += 1

    for w in en_words:
        if w in padded:
            score -= 1

    return score


def detect_lang_it_en(text: str) -> Lang:
    """Detect Italian vs English. Uses langdetect if available, with heuristic fallback.

    Returns: "it" | "en" | "unknown"
    """
    sample = (text or "").strip()
    if not sample:
        return "unknown"

    # Keep the detector stable
    sample = sample[:5000]

    # 1) langdetect (if installed)
    try:
        from langdetect import detect  # type: ignore

        lang = detect(sample)
        if lang == "it":
            return "it"
        if lang == "en":
            return "en"
    except Exception:
        pass

    # 2) heuristic
    score = _heuristic_it_score(sample)
    if score >= 1:
        return "it"
    if score <= -1:
        return "en"
    return "unknown"


def decide_direction(text: str) -> LangDecision:
    detected = detect_lang_it_en(text)

    # Default to IT->EN when unsure (matches original app behavior)
    if detected == "en":
        return LangDecision(detected="en", source="English", target="Italian")

    if detected == "it":
        return LangDecision(detected="it", source="Italian", target="English")

    return LangDecision(detected="unknown", source="Italian", target="English")
