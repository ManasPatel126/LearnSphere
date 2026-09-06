"""
Phase 4 — Vector Ingestion Pipeline
=====================================
RQ task that:
  1. Accepts a roadmap JSON + session_id
  2. Fetches full text from every URL in the roadmap
  3. Chunks text (512 tokens, 64-token overlap)
  4. Embeds each chunk via Gemini text-embedding-004
  5. Writes to ChromaDB, namespaced by session_id

Also handles user-uploaded file content (already extracted text)
through the same pipeline into the same ChromaDB namespace.

Entry point: ingest_roadmap(session_id, roadmap, uploaded_texts=[])
"""

import os
import time
import logging
from typing import Optional
import chromadb
from chromadb.config import Settings
from utils.fetcher import fetch_url_text
from utils.chunker import chunk_text
from utils.embedder import embed_chunks

logger = logging.getLogger(__name__)

# ── ChromaDB client (persistent) ─────────────────────────────────────────────
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_store")

def get_chroma_collection(session_id: str) -> chromadb.Collection:
    """Return (or create) a ChromaDB collection namespaced to this session."""
    client = chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False),
    )
    # Each session gets its own collection so filtering is trivially fast.
    # Collection names must be 3-63 chars, alphanumeric + hyphens.
    safe_name = f"session-{session_id}"[:63]
    collection = client.get_or_create_collection(
        name=safe_name,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_urls_from_roadmap(roadmap: dict) -> list[dict]:
    """
    Walk the roadmap JSON and collect every URL with its metadata.

    Expected roadmap shape (from Phase 3):
    {
      "modules": [
        {
          "week": 1,
          "title": "...",
          "concepts": [...],
          "resources": [{"url": "...", "title": "...", "type": "video|article|repo"}, ...],
          "project": {...},
          "checkpoint": "..."
        },
        ...
      ]
    }
    Returns a flat list of {"url": str, "week": int, "module_title": str, "resource_type": str}
    """
    urls = []
    for module in roadmap.get("modules", []):
        week = module.get("week", 0)
        module_title = module.get("title", "")
        for resource in module.get("resources", []):
            url = resource.get("url", "").strip()
            if url and url.startswith("http"):
                urls.append({
                    "url": url,
                    "week": week,
                    "module_title": module_title,
                    "resource_type": resource.get("type", "article"),
                    "resource_title": resource.get("title", ""),
                })
    return urls


def _upsert_chunks(
    collection: chromadb.Collection,
    session_id: str,
    chunks: list[str],
    embeddings: list[list[float]],
    metadata_base: dict,
    id_prefix: str,
) -> int:
    """Upsert a batch of chunks+embeddings into ChromaDB. Returns count written."""
    if not chunks:
        return 0

    ids = [f"{id_prefix}-chunk-{i}" for i in range(len(chunks))]
    metadatas = [
        {**metadata_base, "chunk_index": i, "session_id": session_id}
        for i in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )
    return len(chunks)


# ── Main task ─────────────────────────────────────────────────────────────────

def ingest_roadmap(
    session_id: str,
    roadmap: dict,
    uploaded_texts: Optional[list[dict]] = None,
    *,
    fetch_timeout: int = 15,
    max_urls: int = 100,
) -> dict:
    """
    RQ-compatible task. Call via:
        from rq import Queue
        q = Queue(connection=redis_conn)
        q.enqueue(ingest_roadmap, session_id, roadmap, uploaded_texts)

    Args:
        session_id:     Unique identifier from Phase 1.
        roadmap:        Dict parsed from Phase 3 JSON output.
        uploaded_texts: List of {"filename": str, "text": str} from user uploads.
        fetch_timeout:  Per-URL HTTP timeout in seconds.
        max_urls:       Safety cap so one huge roadmap doesn't run forever.

    Returns:
        Summary dict: {chunks_written, urls_processed, urls_failed, session_id}
    """
    uploaded_texts = uploaded_texts or []

    collection = get_chroma_collection(session_id)
    urls = _extract_urls_from_roadmap(roadmap)[:max_urls]

    chunks_written = 0
    urls_processed = 0
    urls_failed = 0

    logger.info(
        "[Phase4] session=%s  urls=%d  uploads=%d",
        session_id, len(urls), len(uploaded_texts),
    )

    # ── 1. Ingest roadmap URLs ────────────────────────────────────────────────
    for item in urls:
        url = item["url"]
        try:
            raw_text = fetch_url_text(url, timeout=fetch_timeout)
            if not raw_text or len(raw_text) < 100:
                logger.warning("[Phase4] Skipping short/empty content: %s", url)
                urls_failed += 1
                continue

            chunks = chunk_text(raw_text)
            embeddings = embed_chunks(chunks)

            metadata_base = {
                "source": url,
                "resource_title": item["resource_title"],
                "resource_type": item["resource_type"],
                "week": item["week"],
                "module_title": item["module_title"],
                "content_type": "roadmap_resource",
            }
            id_prefix = _url_to_id(url)

            written = _upsert_chunks(
                collection, session_id, chunks, embeddings, metadata_base, id_prefix
            )
            chunks_written += written
            urls_processed += 1
            logger.info("[Phase4] ✓ %s  chunks=%d", url, written)

            # Be polite to upstream servers
            time.sleep(0.3)

        except Exception as exc:
            logger.error("[Phase4] ✗ %s  error=%s", url, exc)
            urls_failed += 1

    # ── 2. Ingest user-uploaded content ──────────────────────────────────────
    for upload in uploaded_texts:
        filename = upload.get("filename", "upload")
        text = upload.get("text", "")
        if not text or len(text) < 50:
            continue

        try:
            chunks = chunk_text(text)
            embeddings = embed_chunks(chunks)

            metadata_base = {
                "source": f"upload:{filename}",
                "resource_title": filename,
                "resource_type": "user_upload",
                "week": 0,
                "module_title": "User Upload",
                "content_type": "user_upload",
            }
            id_prefix = f"upload-{filename[:40]}"

            written = _upsert_chunks(
                collection, session_id, chunks, embeddings, metadata_base, id_prefix
            )
            chunks_written += written
            logger.info("[Phase4] ✓ upload:%s  chunks=%d", filename, written)

        except Exception as exc:
            logger.error("[Phase4] ✗ upload:%s  error=%s", filename, exc)

    summary = {
        "session_id": session_id,
        "chunks_written": chunks_written,
        "urls_processed": urls_processed,
        "urls_failed": urls_failed,
        "collection_name": f"session-{session_id}"[:63],
    }
    logger.info("[Phase4] Done. %s", summary)
    return summary


# ── Utilities ─────────────────────────────────────────────────────────────────

def _url_to_id(url: str) -> str:
    """Turn a URL into a safe ChromaDB id prefix (max 40 chars)."""
    import hashlib
    return hashlib.md5(url.encode()).hexdigest()[:16]
