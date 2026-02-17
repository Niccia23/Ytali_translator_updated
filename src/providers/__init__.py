from .types import ModelConfig, ProviderName
from .openai_provider import translate_openai
from .gemini_provider import translate_gemini


def translate_any(cfg: ModelConfig, instructions: str, text: str) -> str:
    cfg.validate()

    if cfg.provider == "openai":
        return translate_openai(cfg.api_key, cfg.model, instructions, text)

    if cfg.provider == "gemini":
        return translate_gemini(cfg.api_key, cfg.model, instructions, text)

    raise ValueError(f"Unknown provider: {cfg.provider}")
