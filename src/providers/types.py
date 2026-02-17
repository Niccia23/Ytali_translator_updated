from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ProviderName = Literal["openai", "gemini"]


@dataclass(frozen=True)
class ModelConfig:
    provider: ProviderName
    model: str
    api_key: str
    label: str

    def validate(self) -> None:
        if self.provider not in ("openai", "gemini"):
            raise ValueError(f"Unsupported provider: {self.provider}")
        if not self.model or not self.model.strip():
            raise ValueError("Missing model id.")
        if not self.api_key or not self.api_key.strip():
            raise ValueError("Missing API key.")
