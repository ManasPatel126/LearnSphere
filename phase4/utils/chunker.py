"""
utils/chunker.py
================
Splits long text into overlapping chunks suitable for embedding.

Strategy:
  1. Split on paragraph boundaries first (preserves semantic units).
  2. If a paragraph exceeds max_tokens, split on sentences.
  3. Slide a window of max_tokens with stride (max_tokens - overlap) tokens.

Token counting: uses a simple whitespace approximation (1 token ≈ 0.75 words)
which avoids a tiktoken/sentencepiece dependency while staying close enough
for Gemini's 512-token sweet spot.
"""

import re
from typing import Generator


# ── Config ────────────────────────────────────────────────────────────────────

CHUNK_TOKENS = 512      # Target chunk size in tokens
OVERLAP_TOKENS = 64     # Overlap between consecutive chunks
WORDS_PER_TOKEN = 0.75  # Approximation: 1 word ≈ 1.33 tokens → 1 token ≈ 0.75 words


# ── Public API ────────────────────────────────────────────────────────────────

def chunk_text(
    text: str,
    max_tokens: int = CHUNK_TOKENS,
    overlap_tokens: int = OVERLAP_TOKENS,
) -> list[str]:
    """
    Split *text* into overlapping chunks of at most *max_tokens* tokens.

    Returns a list of non-empty strings, each at most ~max_tokens tokens long.
    """
    text = text.strip()
    if not text:
        return []

    max_words = int(max_tokens / WORDS_PER_TOKEN)
    overlap_words = int(overlap_tokens / WORDS_PER_TOKEN)

    words = text.split()
    if len(words) <= max_words:
        return [text]

    chunks: list[str] = []
    start = 0
    stride = max_words - overlap_words

    while start < len(words):
        end = min(start + max_words, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += stride

    return [c for c in chunks if c.strip()]


def chunk_text_by_paragraph(
    text: str,
    max_tokens: int = CHUNK_TOKENS,
    overlap_tokens: int = OVERLAP_TOKENS,
) -> list[str]:
    """
    Paragraph-aware chunker: tries to keep paragraphs together before falling
    back to word-window chunking. Better for article/blog content.
    """
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    if not paragraphs:
        return chunk_text(text, max_tokens, overlap_tokens)

    max_words = int(max_tokens / WORDS_PER_TOKEN)
    overlap_words = int(overlap_tokens / WORDS_PER_TOKEN)

    chunks: list[str] = []
    current_words: list[str] = []

    for para in paragraphs:
        para_words = para.split()

        # If a single paragraph is too long, sub-chunk it
        if len(para_words) > max_words:
            if current_words:
                chunks.append(" ".join(current_words))
                current_words = current_words[-overlap_words:] if overlap_words else []
            for sub_chunk in _sliding_window(para_words, max_words, overlap_words):
                chunks.append(sub_chunk)
            current_words = []
            continue

        # Would adding this paragraph exceed the limit?
        if current_words and len(current_words) + len(para_words) > max_words:
            chunks.append(" ".join(current_words))
            current_words = current_words[-overlap_words:] if overlap_words else []

        current_words.extend(para_words)

    if current_words:
        chunks.append(" ".join(current_words))

    return [c for c in chunks if c.strip()]


# ── Internal ──────────────────────────────────────────────────────────────────

def _sliding_window(words: list[str], window: int, overlap: int) -> Generator[str, None, None]:
    stride = window - overlap
    start = 0
    while start < len(words):
        end = min(start + window, len(words))
        yield " ".join(words[start:end])
        if end == len(words):
            break
        start += stride


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample = " ".join([f"word{i}" for i in range(1000)])
    result = chunk_text(sample)
    print(f"chunks={len(result)}  sizes={[len(c.split()) for c in result]}")
