from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AppSettings:
    header_logo_path: Optional[str]
    watermark_logo_path: Optional[str]
    watermark_size_px: int
    watermark_opacity: float

    openai_api_key: str
    gemini_api_key: str

    # "Compare (Gemini vs OpenAI)" | "Gemini only" | "OpenAI only"
    run_mode: str

    chunk_chars: int = 9000
    compare_first_n_chunks: Optional[int] = None
    save_local: bool = True
    debug: bool = False

    # Fixed models per user request
    openai_model: str = "gpt-5.2"
    gemini_model: str = "gemini-2.5-flash"

    def validate(self) -> None:
        if self.run_mode not in (
            "Compare (Gemini vs OpenAI)",
            "Gemini only",
            "OpenAI only",
        ):
            raise ValueError(f"Invalid run mode: {self.run_mode}")

        # 🔐 Streamlit-safe: accept keys from config OR environment
        openai_key = self.openai_api_key or os.getenv("OPENAI_API_KEY", "")
        gemini_key = self.gemini_api_key or os.getenv("GEMINI_API_KEY", "")

        if self.run_mode in ("Compare (Gemini vs OpenAI)", "OpenAI only"):
            if not openai_key:
                raise ValueError("Missing OpenAI API key.")

        if self.run_mode in ("Compare (Gemini vs OpenAI)", "Gemini only"):
            if not gemini_key:
                raise ValueError("Missing Gemini API key.")
