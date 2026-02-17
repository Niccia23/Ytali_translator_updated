import os
import streamlit as st

# 🔐 Inject Streamlit secrets into environment BEFORE any OpenAI imports
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

from datetime import datetime
from src.ui import apply_enterprise_ui, render_topbar
from src.text_utils import safe_decode
from src.config import AppSettings
from src.translate import run_translation
from src.editor import copyedit_and_generate_titles
from typing import List

APP_TITLE = "YTALI Translator (IT ↔ EN) — Gemini 2.5 Flash vs GPT-5.2"


# -------------------------
# Helpers
# -------------------------
def _get_secrets_safe() -> dict:
    try:
        return dict(st.secrets)
    except Exception:
        return {}


def _load_input_text(uploaded) -> str:
    if uploaded is None:
        return ""
    return safe_decode(uploaded.read()).strip()


def safe_copyedit(text: str, target_language: str) -> dict:
    """
    Runs copyediting safely.
    Never crashes if the model returns invalid / empty JSON.
    """
    try:
        result = copyedit_and_generate_titles(
            text=text,
            target_language=target_language,
        )
        if not isinstance(result, dict) or "edited_text" not in result:
            raise ValueError("Invalid editor output")
        return result
    except Exception:
        return {
            "edited_text": text,
            "title_suggestions": [],
        }


def generate_titles_only(text: str, target_language: str) -> List[str]:
    """
    Best-effort title generation retry.
    Never crashes.
    """
    try:
        result = copyedit_and_generate_titles(
            text=text,
            target_language=target_language,
        )
        titles = result.get("title_suggestions", [])
        return titles if isinstance(titles, list) else []
    except Exception:
        return []


# -------------------------
# Sidebar
# -------------------------
def sidebar_settings() -> AppSettings:
    st.subheader("Settings")

    secrets = _get_secrets_safe()

    st.markdown("### Branding")
    header_logo_path = st.text_input(
        "Header logo path (top-left)",
        value="assets/logo.webp",
    )
    watermark_logo_path = st.text_input(
        "Watermark logo path (bottom-right)",
        value="assets/logo.webp",
    )

    with st.expander("Watermark styling", expanded=False):
        watermark_size_px = st.slider("Watermark size (px)", 80, 320, 190, 10)
        watermark_opacity = st.slider("Watermark opacity", 0.02, 0.25, 0.10, 0.01)

    st.divider()

    st.markdown("### Providers")
    openai_key = st.text_input(
        "OpenAI API key",
        value=secrets.get("OPENAI_API_KEY", ""),
        type="password",
    )
    gemini_key = st.text_input(
        "Gemini API key",
        value=secrets.get("GEMINI_API_KEY", ""),
        type="password",
    )

    mode = st.radio(
        "Run mode",
        ["Compare (Gemini vs OpenAI)", "Gemini only", "OpenAI only"],
        index=0,
    )

    st.divider()

    with st.expander("Advanced", expanded=False):
        debug = st.toggle("Show debug info", False)

    return AppSettings(
        header_logo_path=header_logo_path or None,
        watermark_logo_path=watermark_logo_path or None,
        watermark_size_px=watermark_size_px,
        watermark_opacity=watermark_opacity,
        openai_api_key=openai_key.strip(),
        gemini_api_key=gemini_key.strip(),
        run_mode=mode,
        chunk_chars=None,
        compare_first_n_chunks=None,
        save_local=False,
        debug=debug,
    )


# -------------------------
# Main
# -------------------------
def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")

    with st.sidebar:
        cfg = sidebar_settings()

    apply_enterprise_ui(
        watermark_logo_path=cfg.watermark_logo_path,
        watermark_size_px=cfg.watermark_size_px,
        watermark_opacity=cfg.watermark_opacity,
    )
    render_topbar(cfg.header_logo_path)

    st.markdown(
        """
### IT ↔ EN auto-translate (single-pass)

- Designed for **short articles**
- **No chunking**
- One request per model
- Outputs are **copyedited**
- Title suggestions are **guaranteed or explicitly retried**
"""
    )

    # -------- FORM --------
    with st.form("input_form", clear_on_submit=False):
        uploaded = st.file_uploader("Upload a text file (.txt)", type=["txt"])
        pasted = st.text_area(
            "Or paste text here",
            value=st.session_state.get("pasted_text", ""),
            height=220,
        )
        submitted = st.form_submit_button(
            "Generate outputs", type="primary", use_container_width=True
        )

    if not submitted and "results" not in st.session_state:
        st.stop()

    # -------- RUN --------
    if submitted:
        input_text = pasted.strip() if pasted.strip() else _load_input_text(uploaded)
        if not input_text:
            st.error("Please upload a .txt file or paste some text.")
            st.stop()

        st.session_state["pasted_text"] = pasted
        progress = st.progress(0, text="Translating…")

        results = run_translation(
            settings=cfg,
            chunks=[input_text],  # NO CHUNKING
            progress=progress,
        )

        detected = results.get("_meta", {}).get("detected_language")
        direction = results.get("_meta", {}).get("direction") or ""

        edited_outputs = {}

        for label, out in results.items():
            if label == "_meta":
                continue

            edited_literal = safe_copyedit(out["literal"], direction)
            edited_neutral = safe_copyedit(out["neutral"], direction)

            titles = edited_neutral.get("title_suggestions", [])


            # Retry titles explicitly if missing
            if not titles:
                titles = generate_titles_only(
                    text=edited_neutral["edited_text"],
                    target_language=direction,
                )

            # only one title
            titles = titles[:1]

            edited_outputs[label] = {
                "literal": edited_literal["edited_text"],
                "neutral": edited_neutral["edited_text"],
                "titles": titles,
            }

        st.session_state["results"] = results
        st.session_state["edited_outputs"] = edited_outputs

        st.success("Done. Outputs are ready.")
        if detected and direction:
            st.info(f"Detected: **{detected}** → Translating: **{direction}**")

    # -------- RENDER --------
    results = st.session_state["results"]
    edited_outputs = st.session_state["edited_outputs"]
    labels = [k for k in results.keys() if k != "_meta"]

    tab_review, _ = st.tabs(["Review", ""])

    with tab_review:
        st.markdown("## 📝 Review outputs (side-by-side)")

        def render_stage(title, key, show_titles=False):
            st.markdown(f"### {title}")
            cols = st.columns(len(labels))

            for col, label in zip(cols, labels):
                with col:
                    st.markdown(f"### 🤖 {label}")
                    st.text_area(
                        f"{label}_{key}",
                        edited_outputs[label][key],
                        height=360,
                        label_visibility="collapsed",
                    )

                    if show_titles:
                        st.markdown("**Title suggestions:**")
                        if edited_outputs[label]["titles"]:
                            for i, t in enumerate(edited_outputs[label]["titles"], 1):
                                st.write(f"{i}. {t}")
                        else:
                            st.caption("No title suggestions could be generated.")

        render_stage("📘 Literal + cultural notes (copyedited)", "literal")
        render_stage(
            "📗 Neutral reader-friendly (copyedited)",
            "neutral",
            show_titles=True,
        )

    if cfg.debug:
        st.markdown("### Debug")
        st.json(results.get("_meta", {}))


if __name__ == "__main__":
    main()

