import base64
import os
from typing import Optional

import streamlit as st


def _img_to_data_uri(path: Optional[str]) -> Optional[str]:
    """Return a data URI for a local image (png/jpg/webp), or None if missing."""
    if not path or not os.path.exists(path):
        return None

    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    ext = os.path.splitext(path)[1].lower().strip(".")
    mime = "png" if ext == "png" else "webp" if ext == "webp" else "jpeg"
    return f"data:image/{mime};base64,{b64}"


def apply_enterprise_ui(
    watermark_logo_path: Optional[str] = None,
    watermark_size_px: int = 190,
    watermark_opacity: float = 0.10,
):
    """Apply a minimal enterprise UI and (optionally) a watermark logo bottom-right."""

    watermark_css = ""
    watermark_uri = _img_to_data_uri(watermark_logo_path)
    if watermark_uri:
        watermark_css = f"""
        body::after {{
            content: "";
            position: fixed;
            right: 24px;
            bottom: 24px;
            width: {watermark_size_px}px;
            height: {watermark_size_px}px;
            background-image: url("{watermark_uri}");
            background-repeat: no-repeat;
            background-size: contain;
            opacity: {watermark_opacity};
            pointer-events: none;
            z-index: 0;
        }}
        """

    st.markdown(
        f"""
<style>
/* Layout polish */
.block-container {{ padding-top: 1.25rem; padding-bottom: 3rem; }}
h1, h2, h3 {{ letter-spacing: -0.01em; }}

/* Slightly lift content above watermark layer */
section.main > div {{ position: relative; z-index: 1; }}

{watermark_css}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_topbar(header_logo_path: Optional[str] = None):
    logo_uri = _img_to_data_uri(header_logo_path)

    left, right = st.columns([3, 2], gap="small")

    with left:
        cols = st.columns([1, 10], gap="small") if logo_uri else None
        if logo_uri and cols:
            with cols[0]:
                st.image(header_logo_path, width=48)
            with cols[1]:
                st.markdown("## YTALI Translator")
                st.caption("Auto-detect IT/EN and translate to the other language. Literal + Neutral styles.")
        else:
            st.markdown("## YTALI Translator")
            st.caption("Auto-detect IT/EN and translate to the other language. Literal + Neutral styles.")

    with right:
        st.markdown(
            """
<div style="text-align:right; padding-top: 0.25rem">
<b>Models</b><br/>
Gemini 2.5 Flash · GPT-5.2
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
