from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .config import AppSettings
from .lang import decide_direction
from .prompts import literal_prompt, neutral_prompt
from .providers import ModelConfig, translate_any
from .text_utils import join_parts


def _runtime_badge(cfg: ModelConfig) -> str:
    return f"{cfg.provider} | {cfg.model}"


def _translate_for_model(
    cfg: ModelConfig,
    chunks: List[str],
    progress,
    source_lang: str,
    target_lang: str,
    progress_prefix: str = "",
) -> Tuple[str, str]:
    lit_parts: List[str] = []
    neu_parts: List[str] = []

    n = max(len(chunks), 1)
    badge = _runtime_badge(cfg)

    lit_inst = literal_prompt(source_lang, target_lang)
    neu_inst = neutral_prompt(source_lang, target_lang)

    for i, c in enumerate(chunks, start=1):
        progress.progress(
            int((i - 1) / n * 100),
            text=f"{progress_prefix} {cfg.label} — {badge} — chunk {i}/{n} (literal)…",
        )
        lit_parts.append(translate_any(cfg, lit_inst, c))

        progress.progress(
            int((i - 1) / n * 100),
            text=f"{progress_prefix} {cfg.label} — {badge} — chunk {i}/{n} (neutral)…",
        )
        neu_parts.append(translate_any(cfg, neu_inst, c))

    progress.progress(100, text=f"{progress_prefix} {cfg.label} — done.")

    return join_parts(lit_parts), join_parts(neu_parts)


def run_translation(
    settings: AppSettings,
    chunks: List[str],
    progress,
) -> Dict[str, Dict[str, str]]:
    """Run translation according to settings.

    Returns:
      {
        "_meta": {"detected_language": "it", "direction": "Italian → English", ...},
        "Gemini 2.5 Flash": {"literal": "...", "neutral": "..."},
        "GPT-5.2": {"literal": "...", "neutral": "..."},
      }
    """

    settings.validate()

    # Language decision based on full input (re-join chunks for detection)
    joined = "\n\n".join(chunks)
    lang_decision = decide_direction(joined)
    direction_str = f"{lang_decision.source} → {lang_decision.target}"

    work_chunks = chunks
    if settings.compare_first_n_chunks and settings.compare_first_n_chunks > 0:
        work_chunks = chunks[: settings.compare_first_n_chunks]

    results: Dict[str, Dict[str, str]] = {
        "_meta": {
            "detected_language": lang_decision.detected,
            "direction": direction_str,
            "chunk_count_total": len(chunks),
            "chunk_count_used": len(work_chunks),
            "run_mode": settings.run_mode,
        }
    }

    want_gemini = settings.run_mode in ("Compare (Gemini vs OpenAI)", "Gemini only")
    want_openai = settings.run_mode in ("Compare (Gemini vs OpenAI)", "OpenAI only")

    tasks: List[ModelConfig] = []

    if want_gemini:
        tasks.append(
            ModelConfig(
                provider="gemini",
                model=settings.gemini_model,
                api_key=settings.gemini_api_key,
                label="Gemini 2.5 Flash",
            )
        )

    if want_openai:
        tasks.append(
            ModelConfig(
                provider="openai",
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                label="GPT-5.2",
            )
        )

    if not tasks:
        raise ValueError("Nothing to run — check Run mode and API keys.")

    # Run sequentially (clear progress in Streamlit)
    for idx, cfg in enumerate(tasks, start=1):
        prefix = f"{idx}/{len(tasks)}"
        lit, neu = _translate_for_model(
            cfg,
            work_chunks,
            progress,
            source_lang=lang_decision.source,
            target_lang=lang_decision.target,
            progress_prefix=prefix,
        )
        results[cfg.label] = {
            "literal": lit,
            "neutral": neu,
        }

    return results
