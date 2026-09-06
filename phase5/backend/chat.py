"""
Phase 5 — /chat endpoint
RAG chatbot using ChromaDB (filtered by session_id) + Gemini streaming.
"""

import os
import google.generativeai as genai
import chromadb
from flask import Blueprint, request, Response, stream_with_context, jsonify
import json

chat_bp = Blueprint("chat", __name__)

# ── Clients ──────────────────────────────────────────────────────────────────

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
_chroma = chromadb.HttpClient(host="localhost", port=8000)


def _get_collection(session_id: str):
    """Return (or create) the ChromaDB collection for this session."""
    return _chroma.get_or_create_collection(
        name=f"course_{session_id}",
        metadata={"hnsw:space": "cosine"},
    )


def _embed_query(text: str) -> list[float]:
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_query",
    )
    return result["embedding"]


def _retrieve(session_id: str, query: str, top_k: int = 6) -> list[dict]:
    """Embed query, pull top-k chunks from session namespace."""
    collection = _get_collection(session_id)
    query_embedding = _embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"session_id": session_id},          # hard isolation
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "source": meta.get("source_url", "unknown"),
            "title": meta.get("title", ""),
            "relevance": round(1 - dist, 3),        # cosine distance → similarity
        })
    return chunks


def _build_system_prompt(chunks: list[dict]) -> str:
    context_blocks = "\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in chunks
    )
    return f"""You are a focused study assistant for a personalised learning course.
Answer ONLY from the context below. If the answer is not in the context, say:
"I don't have information on that in your course materials."

Do not mention that you are using context or chunks — just answer naturally and helpfully.
Be concise but thorough. Use markdown for code or lists when it helps clarity.

--- COURSE CONTEXT ---
{context_blocks}
--- END CONTEXT ---"""


# ── Routes ────────────────────────────────────────────────────────────────────

@chat_bp.route("/chat", methods=["POST"])
def chat():
    """
    POST /chat
    Body: { "session_id": str, "message": str, "history": [...] }
    Returns: streaming text/event-stream
    """
    data = request.get_json(force=True)
    session_id = data.get("session_id", "").strip()
    user_message = data.get("message", "").strip()
    history = data.get("history", [])          # [{role, content}, ...]

    if not session_id or not user_message:
        return jsonify({"error": "session_id and message are required"}), 400

    # 1. Retrieve relevant chunks
    try:
        chunks = _retrieve(session_id, user_message)
    except Exception as e:
        return jsonify({"error": f"Retrieval failed: {e}"}), 500

    # 2. Build Gemini chat
    system_prompt = _build_system_prompt(chunks)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt,
    )

    # Convert stored history → Gemini format
    gemini_history = [
        {"role": turn["role"], "parts": [turn["content"]]}
        for turn in history
    ]

    chat_session = model.start_chat(history=gemini_history)

    # 3. Stream response
    def generate():
        try:
            response = chat_session.send_message(user_message, stream=True)
            for chunk in response:
                if chunk.text:
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"

            # Send sources at the end
            sources = [
                {"title": c["title"], "url": c["source"], "relevance": c["relevance"]}
                for c in chunks
                if c["relevance"] > 0.5
            ]
            yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@chat_bp.route("/chat/sources", methods=["POST"])
def get_sources():
    """
    Quick non-streaming retrieval check — useful for debugging.
    POST /chat/sources  { "session_id": str, "query": str }
    """
    data = request.get_json(force=True)
    chunks = _retrieve(data["session_id"], data["query"])
    return jsonify({"chunks": chunks})
