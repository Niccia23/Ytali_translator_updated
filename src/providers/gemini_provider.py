from __future__ import annotations

import json
import requests


def translate_gemini(
    api_key: str,
    model: str,
    instructions: str,
    text: str,
) -> str:
    """Gemini REST call.

    Endpoint:
      POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=...

    Notes:
      - model example: "gemini-2.5-flash"
      - uses systemInstruction + user content
    """

    if not api_key or not api_key.strip():
        raise ValueError("Missing GEMINI_API_KEY for Gemini provider.")
    if not model or not model.strip():
        raise ValueError("Missing Gemini model name.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    params = {"key": api_key.strip()}

    payload = {
        "systemInstruction": {"parts": [{"text": instructions}]},
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {"temperature": 0.2},
    }

    r = requests.post(url, params=params, json=payload, timeout=120)

    if r.status_code != 200:
        raise RuntimeError(f"Gemini API error {r.status_code}:\n{r.text}")

    data = r.json()

    try:
        return (data["candidates"][0]["content"]["parts"][0]["text"] or "").strip()
    except Exception:
        raise RuntimeError(
            "Unexpected Gemini response shape:\n"
            + json.dumps(data, ensure_ascii=False, indent=2)[:4000]
        )
