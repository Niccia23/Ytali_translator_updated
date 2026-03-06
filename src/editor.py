import os
import json
from typing import Any, Dict, List
from openai import OpenAI


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=api_key)


def _strip_json_fence(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("```"):
        lines = s.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        s = "\n".join(lines).strip()
    return s


def _extract_json_object(text: str) -> str:
    """
    Best-effort: remove fences, then if extra prose exists, take substring from first { to last }.
    """
    t = _strip_json_fence(text).strip()
    if t.startswith("{") and t.endswith("}"):
        return t
    l = t.find("{")
    r = t.rfind("}")
    if l != -1 and r != -1 and r > l:
        return t[l : r + 1]
    raise ValueError("Could not locate JSON object in model output")


def _parse_payload(raw_text: str) -> Dict[str, Any]:
    obj = _extract_json_object(raw_text)
    data = json.loads(obj)

    edited_text = data.get("edited_text", "")
    titles = data.get("title_suggestions", [])

    if not isinstance(edited_text, str):
        edited_text = str(edited_text)

    if not isinstance(titles, list):
        titles = []
    titles = [t.strip() for t in titles if isinstance(t, str) and t.strip()]

    return {"edited_text": edited_text, "title_suggestions": titles}


def _call_editor(client: OpenAI, text: str, target_language: str) -> Dict[str, Any]:
    """
    Single call that *attempts* to enforce JSON schema, but still works if schema isn't applied.
    """
    schema = {
        "name": "ytali_copyedit_titles",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "edited_text": {"type": "string"},
                "title_suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 1,
                },
            },
            "required": ["edited_text", "title_suggestions"],
        },
    }

    system = f"""
You are a meticulous editor.

Task:
1) Copyedit the text (fix grammar, punctuation, clarity; preserve meaning).
2) Suggest EXACTLY ONE strong title in the target language.

Target language: {target_language}

Return ONLY valid JSON with keys:
- edited_text (string)
- title_suggestions (array with exactly 1 string)

No markdown fences. No extra text.
""".strip()

    # Try schema mode first; if the installed SDK/server rejects it, fallback to plain prompt.
    try:
        resp = client.responses.create(
            model="gpt-5.2",
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            response_format={"type": "json_schema", "json_schema": schema},
        )
    except Exception:
        # Fallback: still ask for JSON, just without schema enforcement
        resp = client.responses.create(
            model="gpt-5.2",
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
        )

    raw = resp.output_text
    return _parse_payload(raw)


def _call_titles_only(client: OpenAI, edited_text: str, target_language: str) -> List[str]:
    """
    Backup call if titles are missing.
    """
    system = f"""
Generate EXACTLY ONE strong title in the target language.

Target language: {target_language}

Return ONLY valid JSON:
{{"title_suggestions": ["..."]}}

No markdown fences. No extra text.
""".strip()

    resp = client.responses.create(
        model="gpt-5.2",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": edited_text},
        ],
    )

    data = _parse_payload(resp.output_text)
    titles = data.get("title_suggestions", [])
    return titles if isinstance(titles, list) else []


def copyedit_and_generate_titles(text: str, target_language: str) -> Dict[str, Any]:
    """
    Guaranteed output:
      - edited_text: string
      - title_suggestions: list with 1 element
    """
    client = get_openai_client()

    data = _call_editor(client, text=text, target_language=target_language)

    # Hard guarantee: if missing titles, try a second call
    if not data.get("title_suggestions"):
        titles = _call_titles_only(client, edited_text=data["edited_text"], target_language=target_language)
        data["title_suggestions"] = titles

    # Absolute last resort fallback
    if not data.get("title_suggestions"):
        data["title_suggestions"] = ["(Title unavailable)"]

    # Enforce exactly one
    data["title_suggestions"] = data["title_suggestions"][:1]

    return data