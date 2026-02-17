from openai import OpenAI
import os


def get_openai_client() -> OpenAI:
    """
    Lazily create the OpenAI client.
    This is Streamlit-safe and cloud-safe.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    return OpenAI(api_key=api_key)


def copyedit_and_generate_titles(text: str, target_language: str):
    client = get_openai_client()

    response = client.responses.create(
        model="gpt-5.2",
        input=f"""
Copyedit the following text and suggest ONE strong title.

Return JSON with keys:
- edited_text
- title_suggestions (list with 1 element)

Target language: {target_language}

TEXT:
{text}
""",
    )

    # 👇 adapt this to your existing parsing logic
    output_text = response.output_text

    return {
        "edited_text": output_text,
        "title_suggestions": [],
    }
