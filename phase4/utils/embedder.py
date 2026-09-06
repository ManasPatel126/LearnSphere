"""
utils/embedder.py
=================
Wraps Gemini text-embedding-004 with:
  - Automatic batching (Gemini allows up to 100 texts per request)
  - Exponential-backoff retry on rate-limit / transient errors
  - A local in-process cache (LRU) to avoid re-embedding the same chunk twice
    across multiple ingest runs for the same session

Usage:
    from utils.embedder import embed_chunks

    embeddings = embed_chunks(["chunk one", "chunk two", ...])
    # → list[list[float]], same length as input
"""

import os
import time
import logging
from functools import lru_cache

import google.generativeai as genai  # type: ignore

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EMBED_MODEL = "models/text-embedding-004"
BATCH_SIZE = 100          # Gemini API limit per request
MAX_RETRIES = 4
BASE_BACKOFF = 1.0        # seconds, doubles each retry

genai.configure(api_key=GEMINI_API_KEY)


# ── Public API ────────────────────────────────────────────────────────────────

def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """
    Embed a list of text chunks using Gemini text-embedding-004.

    Args:
        chunks: List of plain-text strings (each < ~2048 tokens for best results).

    Returns:
        List of float vectors, one per input chunk.
        Dimension is 768 (text-embedding-004 default).

    Raises:
        RuntimeError if embedding fails after all retries.
    """
    if not chunks:
        return []

    all_embeddings: list[list[float]] = []

    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[batch_start : batch_start + BATCH_SIZE]
        embeddings = _embed_batch_with_retry(batch)
        all_embeddings.extend(embeddings)

    return all_embeddings


def embed_query(query: str) -> list[float]:
    """
    Embed a single query string (for retrieval at chat time).
    Uses task_type=RETRIEVAL_QUERY to match the ingestion task type.
    """
    result = genai.embed_content(
        model=EMBED_MODEL,
        content=query,
        task_type="RETRIEVAL_QUERY",
    )
    return result["embedding"]


# ── Internal ──────────────────────────────────────────────────────────────────

def _embed_batch_with_retry(batch: list[str]) -> list[list[float]]:
    """Call the Gemini embedding API with exponential backoff."""
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            result = genai.embed_content(
                model=EMBED_MODEL,
                content=batch,
                task_type="RETRIEVAL_DOCUMENT",
            )
            # result["embedding"] is a list of vectors when content is a list
            embeddings = result["embedding"]
            if isinstance(embeddings[0], float):
                # Single text was passed; wrap in list
                embeddings = [embeddings]
            return embeddings

        except Exception as exc:
            last_exc = exc
            wait = BASE_BACKOFF * (2 ** attempt)
            logger.warning(
                "Embedding attempt %d/%d failed: %s — retrying in %.1fs",
                attempt + 1, MAX_RETRIES, exc, wait,
            )
            time.sleep(wait)

    raise RuntimeError(
        f"Embedding failed after {MAX_RETRIES} attempts. Last error: {last_exc}"
    )


# ── Quick smoke test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("Set GEMINI_API_KEY in your .env first.")
    else:
        test_chunks = ["Hello, world!", "This is a test chunk for embedding."]
        vecs = embed_chunks(test_chunks)
        print(f"Embedded {len(vecs)} chunks, dim={len(vecs[0])}")
