import re
from typing import List


def safe_decode(raw: bytes) -> str:
    """Decode bytes into text, preferring utf-8 and falling back to latin-1."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def chunk_text(text: str, max_chars: int = 9000) -> List[str]:
    """Chunk a long text by paragraphs to keep each chunk under max_chars."""
    text = (text or "").strip()
    if not text:
        return []

    paras = re.split(r"\n{2,}", text)

    chunks: List[str] = []
    buf: List[str] = []
    buf_len = 0

    for p in paras:
        p = p.strip()
        if not p:
            continue

        add_len = len(p) + 2
        if buf and (buf_len + add_len > max_chars):
            chunks.append("\n\n".join(buf))
            buf, buf_len = [p], len(p)
        else:
            buf.append(p)
            buf_len += add_len

    if buf:
        chunks.append("\n\n".join(buf))

    return chunks


def join_parts(parts: List[str]) -> str:
    return "\n\n".join([p.strip() for p in parts if p and p.strip()]).strip()
