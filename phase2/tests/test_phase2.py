"""
Phase 2 Tests
Run with: pytest tests/ -v

These tests use a hardcoded subtopic list so Phase 2 can be developed
and tested completely independently of Phase 1.

Set GEMINI_API_KEY (and optionally YOUTUBE_API_KEY, GITHUB_TOKEN, etc.)
before running live tests. Use --mock flag (via env var MOCK=1) to skip
real API calls and use stub data instead.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

MOCK = os.getenv("MOCK", "0") == "1"

# Hardcoded test subtopics — use these to test Phase 2 independently
TEST_SUBTOPICS = [
    "Neural Networks fundamentals",
    "Backpropagation algorithm",
    "Convolutional Neural Networks",
]
TEST_SESSION_ID = "test-session-phase2-001"


# ─── Unit tests ───────────────────────────────────────────────────────────────

class TestQualityScorer:
    def test_signal_score_github(self):
        from research_engine.quality_scorer import _compute_signal_score
        resource = {"source": "github", "star_score": 0.8, "has_transcript": False, "content_length": 500}
        score = _compute_signal_score(resource)
        assert 0.0 <= score <= 1.0
        assert score >= 0.5  # high stars should push above neutral

    def test_signal_score_youtube_with_transcript(self):
        from research_engine.quality_scorer import _compute_signal_score
        resource = {"source": "youtube", "has_transcript": True, "content_length": 3000}
        score = _compute_signal_score(resource)
        assert score > 0.5

    def test_batch_score_sorts_descending(self):
        from research_engine.quality_scorer import batch_score_resources
        resources = [
            {"title": "Low quality", "source": "reddit", "subtopic": "test",
             "content_preview": "short", "content_length": 10, "star_score": 0.1},
            {"title": "High quality", "source": "github", "subtopic": "test",
             "content_preview": "very detailed content " * 50, "content_length": 2000, "star_score": 0.9},
        ]
        with patch("research_engine.quality_scorer.GEMINI_API_KEY", None):
            scored = batch_score_resources(resources)
        assert scored[0]["quality_score"] >= scored[1]["quality_score"]


class TestGitHubFetcher:
    @pytest.mark.skipif(not os.getenv("GITHUB_TOKEN"), reason="GITHUB_TOKEN not set")
    def test_search_returns_results(self):
        from research_engine.github_fetcher import search_github_repos
        repos = search_github_repos("neural networks", max_results=3)
        assert len(repos) > 0
        assert "url" in repos[0]
        assert "stars" in repos[0]

    def test_fetch_github_resources_no_token(self):
        """Should return empty list gracefully when no token is set."""
        from research_engine.github_fetcher import fetch_github_resources
        with patch("research_engine.github_fetcher.GITHUB_TOKEN", None):
            # Without auth the API rate limit is low but not zero — mock the response
            with patch("requests.get") as mock_get:
                mock_get.return_value.raise_for_status = MagicMock()
                mock_get.return_value.json.return_value = {"items": []}
                results = fetch_github_resources("test topic")
        assert isinstance(results, list)


class TestYouTubeFetcher:
    def test_no_api_key_returns_empty(self):
        from research_engine.youtube_fetcher import fetch_youtube_resources
        with patch("research_engine.youtube_fetcher.YOUTUBE_API_KEY", None):
            results = fetch_youtube_resources("neural networks")
        assert results == []

    def test_transcript_fetch_handles_disabled(self):
        from research_engine.youtube_fetcher import fetch_transcript
        from youtube_transcript_api import TranscriptsDisabled
        with patch("research_engine.youtube_fetcher.YouTubeTranscriptApi.get_transcript",
                   side_effect=TranscriptsDisabled("fake_id")):
            result = fetch_transcript("fake_id")
        assert result is None


class TestRedditFetcher:
    def test_no_credentials_returns_empty(self):
        from research_engine.reddit_fetcher import fetch_reddit_resources
        with patch("research_engine.reddit_fetcher.REDDIT_CLIENT_ID", None):
            results = fetch_reddit_resources("neural networks")
        assert results == []


class TestArticlesFetcher:
    def test_no_perplexity_key_returns_empty(self):
        from research_engine.articles_fetcher import fetch_perplexity_articles
        with patch("research_engine.articles_fetcher.PERPLEXITY_API_KEY", None):
            results = fetch_perplexity_articles("neural networks")
        assert results == []


# ─── Integration test (requires real API keys) ─────────────────────────────────

@pytest.mark.skipif(MOCK, reason="MOCK=1 — skipping live integration test")
@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY required for integration test")
class TestFullPipeline:
    def test_run_research_phase_single_subtopic(self):
        """
        Live end-to-end test: research one subtopic, check output shape.
        Only runs if GEMINI_API_KEY is set and MOCK != 1.
        """
        from research_engine.orchestrator import run_research_phase

        # Use a single subtopic to keep test fast
        result = run_research_phase(TEST_SESSION_ID, [TEST_SUBTOPICS[0]])

        assert "session_id" in result
        assert result["session_id"] == TEST_SESSION_ID
        assert "resources" in result
        assert TEST_SUBTOPICS[0] in result["resources"]

        resources = result["resources"][TEST_SUBTOPICS[0]]
        assert isinstance(resources, list)

        if resources:
            first = resources[0]
            assert "title" in first
            assert "url" in first
            assert "quality_score" in first
            assert 0.0 <= first["quality_score"] <= 1.0
            print(f"\nTop resource: {first['title']} | score={first['quality_score']}")


# ─── Standalone runner (not pytest) ────────────────────────────────────────────

if __name__ == "__main__":
    """
    Run directly to test the full pipeline manually:
        python tests/test_phase2.py
    """
    from research_engine.orchestrator import run_research_phase

    print(f"Running Phase 2 research for subtopics: {TEST_SUBTOPICS}")
    result = run_research_phase(TEST_SESSION_ID, TEST_SUBTOPICS)

    print(f"\n{'='*60}")
    print(f"Session: {result['session_id']}")
    print(f"Subtopics researched: {len(result['subtopics'])}")
    total = sum(len(v) for v in result["resources"].values())
    print(f"Total resources found: {total}")
    print(f"{'='*60}")

    for subtopic, resources in result["resources"].items():
        print(f"\n📚 {subtopic} ({len(resources)} resources):")
        for r in resources[:3]:
            print(f"  [{r['quality_score']:.2f}] {r['title']} [{r['source']}]")

    # Optionally dump to file for inspection
    with open("phase2_sample_output.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\n✅ Full output saved to phase2_sample_output.json")
