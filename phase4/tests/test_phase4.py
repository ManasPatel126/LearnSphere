"""
tests/test_phase4.py
====================
Run with:  pytest tests/test_phase4.py -v

Tests cover:
  - chunker correctness (sizes, overlap, edge cases)
  - fetcher URL dispatch logic (mocked HTTP)
  - full ingest_roadmap flow with mocked Gemini + ChromaDB
  - retriever with mocked ChromaDB
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, MagicMock


# ── Chunker tests (no external deps) ─────────────────────────────────────────

from utils.chunker import chunk_text, chunk_text_by_paragraph

class TestChunker:
    def test_short_text_returns_single_chunk(self):
        text = "Hello world, this is a short text."
        chunks = chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_splits_correctly(self):
        # ~1000 words → should produce multiple chunks
        words = [f"word{i}" for i in range(1000)]
        text = " ".join(words)
        chunks = chunk_text(text, max_tokens=512, overlap_tokens=64)
        assert len(chunks) > 1

    def test_all_words_covered(self):
        words = [f"w{i}" for i in range(800)]
        text = " ".join(words)
        chunks = chunk_text(text, max_tokens=256, overlap_tokens=32)
        # Last chunk must include the last word
        assert "w799" in chunks[-1]
        # First chunk must include the first word
        assert "w0" in chunks[0]

    def test_overlap_present(self):
        words = [f"word{i}" for i in range(500)]
        text = " ".join(words)
        chunks = chunk_text(text, max_tokens=200, overlap_tokens=50)
        if len(chunks) >= 2:
            # Last words of chunk 0 should appear in chunk 1
            tail_of_chunk0 = set(chunks[0].split()[-30:])
            head_of_chunk1 = set(chunks[1].split()[:30])
            assert tail_of_chunk0 & head_of_chunk1  # non-empty intersection

    def test_empty_text(self):
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_paragraph_chunker(self):
        paragraphs = [f"Paragraph {i}. " + " ".join([f"word{j}" for j in range(50)]) for i in range(10)]
        text = "\n\n".join(paragraphs)
        chunks = chunk_text_by_paragraph(text, max_tokens=256)
        assert len(chunks) >= 1
        for c in chunks:
            assert c.strip()

    def test_no_empty_chunks(self):
        text = "\n\n".join([f"Para {i}" for i in range(20)])
        chunks = chunk_text(text)
        for c in chunks:
            assert c.strip()


# ── Fetcher dispatch tests ────────────────────────────────────────────────────

from utils.fetcher import _extract_youtube_id, _parse_github_repo

class TestFetcherDispatching:
    def test_youtube_id_standard(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert _extract_youtube_id(url) == "dQw4w9WgXcQ"

    def test_youtube_id_short(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert _extract_youtube_id(url) == "dQw4w9WgXcQ"

    def test_github_repo_basic(self):
        url = "https://github.com/openai/tiktoken"
        result = _parse_github_repo(url)
        assert result == ("openai", "tiktoken")

    def test_github_repo_subpath(self):
        url = "https://github.com/openai/tiktoken/tree/main/src"
        result = _parse_github_repo(url)
        assert result == ("openai", "tiktoken")

    def test_github_repo_invalid(self):
        url = "https://github.com"
        result = _parse_github_repo(url)
        assert result is None

    @patch("utils.fetcher.requests.get")
    def test_generic_fetch_returns_text(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "text/html"}
        mock_resp.text = "<html><body><main><p>Hello world</p></main></body></html>"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from utils.fetcher import _fetch_generic
        text = _fetch_generic("https://example.com")
        assert "Hello world" in text

    @patch("utils.fetcher.requests.get")
    def test_generic_fetch_timeout_returns_empty(self, mock_get):
        import requests as req
        mock_get.side_effect = req.Timeout("timed out")

        from utils.fetcher import _fetch_generic
        text = _fetch_generic("https://example.com", timeout=1)
        assert text == ""


# ── Embedder tests (mocked Gemini) ───────────────────────────────────────────

class TestEmbedder:
    @patch("utils.embedder.genai.embed_content")
    def test_embed_chunks_returns_correct_count(self, mock_embed):
        mock_embed.return_value = {"embedding": [[0.1, 0.2, 0.3]] * 3}
        from utils.embedder import embed_chunks
        vecs = embed_chunks(["a", "b", "c"])
        assert len(vecs) == 3

    @patch("utils.embedder.genai.embed_content")
    def test_embed_empty_returns_empty(self, mock_embed):
        from utils.embedder import embed_chunks
        assert embed_chunks([]) == []
        mock_embed.assert_not_called()

    @patch("utils.embedder.genai.embed_content")
    def test_embed_query(self, mock_embed):
        mock_embed.return_value = {"embedding": [0.1, 0.2, 0.3]}
        from utils.embedder import embed_query
        vec = embed_query("What is backprop?")
        assert vec == [0.1, 0.2, 0.3]
        mock_embed.assert_called_once()
        call_kwargs = mock_embed.call_args
        assert "RETRIEVAL_QUERY" in str(call_kwargs)


# ── Ingest task integration test (fully mocked) ───────────────────────────────

class TestIngestTask:
    SAMPLE_ROADMAP = {
        "modules": [
            {
                "week": 1,
                "title": "Foundations",
                "concepts": ["linear algebra", "calculus"],
                "resources": [
                    {"url": "https://example.com/article1", "title": "Intro Article", "type": "article"},
                    {"url": "https://github.com/ml-org/ml-repo", "title": "ML Repo", "type": "repo"},
                ],
                "project": {"title": "Implement matrix multiply"},
                "checkpoint": "Can you multiply matrices by hand?",
            }
        ]
    }

    @patch("tasks.ingest.embed_chunks", return_value=[[0.1]*768, [0.2]*768])
    @patch("tasks.ingest.chunk_text", return_value=["chunk one", "chunk two"])
    @patch("tasks.ingest.fetch_url_text", return_value="Long article text here " * 50)
    @patch("tasks.ingest.get_chroma_collection")
    def test_ingest_roadmap_success(self, mock_collection, mock_fetch, mock_chunk, mock_embed):
        mock_col = MagicMock()
        mock_collection.return_value = mock_col

        from tasks.ingest import ingest_roadmap
        result = ingest_roadmap(
            session_id="test-session-001",
            roadmap=self.SAMPLE_ROADMAP,
        )

        assert result["session_id"] == "test-session-001"
        assert result["urls_processed"] == 2
        assert result["urls_failed"] == 0
        assert mock_col.upsert.call_count == 2  # one per URL

    @patch("tasks.ingest.embed_chunks", return_value=[[0.1]*768])
    @patch("tasks.ingest.chunk_text", return_value=["chunk"])
    @patch("tasks.ingest.fetch_url_text", return_value="")   # empty → skip
    @patch("tasks.ingest.get_chroma_collection")
    def test_ingest_skips_empty_content(self, mock_collection, mock_fetch, mock_chunk, mock_embed):
        mock_col = MagicMock()
        mock_collection.return_value = mock_col

        from tasks.ingest import ingest_roadmap
        result = ingest_roadmap("s1", self.SAMPLE_ROADMAP)

        assert result["urls_failed"] == 2  # both URLs returned empty
        assert result["urls_processed"] == 0

    @patch("tasks.ingest.embed_chunks", return_value=[[0.1]*768])
    @patch("tasks.ingest.chunk_text", return_value=["upload chunk"])
    @patch("tasks.ingest.fetch_url_text", return_value="article text " * 50)
    @patch("tasks.ingest.get_chroma_collection")
    def test_ingest_user_uploads(self, mock_collection, mock_fetch, mock_chunk, mock_embed):
        mock_col = MagicMock()
        mock_collection.return_value = mock_col

        uploaded = [{"filename": "notes.pdf", "text": "User notes " * 100}]
        from tasks.ingest import ingest_roadmap
        result = ingest_roadmap("s2", self.SAMPLE_ROADMAP, uploaded_texts=uploaded)

        # upsert should be called for URLs + 1 upload
        assert mock_col.upsert.call_count >= 3

    @patch("tasks.ingest.get_chroma_collection")
    def test_ingest_no_urls(self, mock_collection):
        mock_col = MagicMock()
        mock_collection.return_value = mock_col

        from tasks.ingest import ingest_roadmap
        result = ingest_roadmap("s3", {"modules": []})
        assert result["urls_processed"] == 0
        assert result["chunks_written"] == 0


# ── Retriever tests (mocked ChromaDB) ────────────────────────────────────────

class TestRetriever:
    @patch("utils.retriever._get_collection")
    @patch("utils.retriever.embed_query", return_value=[0.1]*768)
    def test_retrieve_returns_chunks(self, mock_embed, mock_get_col):
        mock_col = MagicMock()
        mock_col.count.return_value = 5
        mock_col.query.return_value = {
            "documents": [["chunk one text", "chunk two text"]],
            "metadatas": [
                [
                    {"source": "https://example.com", "resource_title": "Test", "week": 1, "module_title": "Foundations"},
                    {"source": "https://github.com/x/y", "resource_title": "Repo", "week": 2, "module_title": "Advanced"},
                ]
            ],
            "distances": [[0.12, 0.25]],
        }
        mock_get_col.return_value = mock_col

        from utils.retriever import retrieve_context
        chunks = retrieve_context("test-session", "backpropagation", k=2)

        assert len(chunks) == 2
        assert chunks[0]["text"] == "chunk one text"
        assert chunks[0]["week"] == 1
        assert chunks[0]["distance"] == 0.12

    @patch("utils.retriever._get_collection", return_value=None)
    def test_retrieve_missing_collection(self, _):
        from utils.retriever import retrieve_context
        chunks = retrieve_context("nonexistent-session", "query")
        assert chunks == []

    @patch("utils.retriever._get_collection")
    def test_get_session_stats(self, mock_get_col):
        mock_col = MagicMock()
        mock_col.count.return_value = 42
        mock_col.name = "session-abc"
        mock_get_col.return_value = mock_col

        from utils.retriever import get_session_stats
        stats = get_session_stats("abc")
        assert stats["exists"] is True
        assert stats["total_chunks"] == 42


# ── Manual smoke test (runs against real APIs if env vars set) ────────────────

if __name__ == "__main__":
    """
    Quick manual test — requires GEMINI_API_KEY set in environment.
    Run: python tests/test_phase4.py
    """
    import json

    SAMPLE_SESSION = "smoke-test-001"
    SAMPLE_ROADMAP = {
        "modules": [
            {
                "week": 1,
                "title": "ML Foundations",
                "concepts": ["gradient descent"],
                "resources": [
                    {
                        "url": "https://github.com/karpathy/micrograd",
                        "title": "micrograd",
                        "type": "repo",
                    }
                ],
            }
        ]
    }

    print("Running smoke test against real Gemini + ChromaDB...")
    from tasks.ingest import ingest_roadmap
    result = ingest_roadmap(SAMPLE_SESSION, SAMPLE_ROADMAP)
    print("Ingest result:", json.dumps(result, indent=2))

    from utils.retriever import retrieve_context
    chunks = retrieve_context(SAMPLE_SESSION, "how does gradient descent work?", k=3)
    print(f"\nRetrieved {len(chunks)} chunks:")
    for c in chunks:
        print(f"  [{c['week']}w] {c['source']} (dist={c['distance']})")
        print(f"  {c['text'][:120]}...")
