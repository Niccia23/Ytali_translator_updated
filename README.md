# YTALI Translator (IT ↔ EN)

Streamlit app that **auto-detects Italian vs English** and translates to the other language.

It runs two translation styles:
- **Literal + cultural notes**
- **Neutral reader-friendly**

And can run in 3 modes:
- **Compare (Gemini vs OpenAI)**
- **Gemini only**
- **OpenAI only**

## Models (fixed)
- **Gemini:** `gemini-2.5-flash`
- **OpenAI:** `gpt-5.2`

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt

streamlit run app.py
```

## Secrets (recommended)
Create `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "..."
GEMINI_API_KEY = "..."
```

## Notes
- **Compare mode** runs both models → more cost.
- Long texts are chunked by paragraphs (configurable in sidebar).
