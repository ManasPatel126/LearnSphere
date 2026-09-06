"""
utils/retriever.py
==================
Retrieval helper used by the Phase 5 chatbot endpoint.

Given a session_id and a user query, returns the top-k most relevant chunks
from that session's ChromaDB collection.

Usage:
    from utils.retriever import retrieve_context

    chunks = retrieve_context(session_id="abc123", query="What is backpropagation?", k=5)
    context_str = "\n\n---\n\n".join(chunks)
"""

import os
import logging
import chromadb
from chromadb.config import Settings
from utils.embedder import embed_query

logger = logging.getLogger(__name__)

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_store")


def retrieve_context(
    session_id: str,
    query: str,
    k: int = 5,
) -> list[dict]:
    """
    Retrieve the top-k chunks most semantically similar to *query*
    from the ChromaDB collection for *session_id*.

    Returns:
        List of dicts, each with:
          - "text":     the chunk text
          - "source":   original URL or upload filename
          - "week":     roadmap week number (int)
          - "distance": cosine distance (lower = more similar)
    """
    collection = _get_collection(session_id)
    if collection is None:
        logger.warning("No ChromaDB collection found for session: %s", session_id)
        return []

    query_embedding = embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(k, collection.count() or 1),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, dists):
        chunks.append({
            "text": doc,
            "source": meta.get("source", ""),
            "resource_title": meta.get("resource_title", ""),
            "week": meta.get("week", 0),
            "module_title": meta.get("module_title", ""),
            "distance": round(dist, 4),
        })

    return chunks


def get_session_stats(session_id: str) -> dict:
    """
    Return stats about a session's vector store:
      - total_chunks, collection_name, exists
    Used by the frontend to show ingestion progress.
    """
    collection = _get_collection(session_id)
    if collection is None:
        return {"exists": False, "total_chunks": 0, "collection_name": None}

    return {
        "exists": True,
        "total_chunks": collection.count(),
        "collection_name": collection.name,
        "session_id": session_id,
    }


# ── Internal ──────────────────────────────────────────────────────────────────

def _get_collection(session_id: str) -> chromadb.Collection | None:
    """Return the ChromaDB collection for a session, or None if it doesn't exist."""
    safe_name = f"session-{session_id}"[:63]
    try:
        client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        return client.get_collection(name=safe_name)
    except Exception:
        return None
