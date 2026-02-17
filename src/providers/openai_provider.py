from __future__ import annotations

from openai import OpenAI


def translate_openai(
    api_key: str,
    model: str,
    instructions: str,
    text: str,
) -> str:
    """Translate using OpenAI Responses API."""

    client = OpenAI(api_key=api_key)

    resp = client.responses.create(
        model=model,
        instructions=instructions,
        input=text,
    )

    out = getattr(resp, "output_text", "")
    return (out or "").strip()
