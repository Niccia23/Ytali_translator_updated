from openai import OpenAI
import json

client = OpenAI()

def copyedit_and_generate_titles(
    text: str,
    target_language: str,
    model: str = "gpt-5.2"
) -> dict:
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional editor and translator.\n\n"
                    "Tasks:\n"
                    "1. Copyedit the document:\n"
                    "- Fix spelling, punctuation, spacing, grammar\n"
                    "- Do NOT rewrite or change style\n"
                    "- Preserve paragraph structure\n\n"
                    "2. Suggest 2–3 article titles in the same language.\n\n"
                    "Output valid JSON with keys:\n"
                    "edited_text, title_suggestions"
                )
            },
            {
                "role": "user",
                "content": f"""
Language: {target_language}

Document:
\"\"\"
{text}
\"\"\"
"""
            }
        ],
    )

    content = response.choices[0].message.content
    return json.loads(content)
