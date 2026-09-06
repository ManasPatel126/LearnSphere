"""
Orchestrator — Phase 2
Runs all fetchers (YouTube, GitHub, Reddit, Articles) in parallel per subtopic,
then scores all results with Gemini, and saves the final JSON to Redis keyed by session_id.

Entry point: run_research_phase(session_id, subtopics)
Output shape saved to Redis:
{
  "session_id": "abc123",
  "subtopics": ["Neural Networks", "Backpropagation", ...],
  "resources": {
    "Neural Networks": [
      {
        "title": "...",
        "url": "...",
        "source": "youtube|github|reddit|perplexity|newsapi",
        "subtopic": "Neural Networks",
        "content_preview": "...",
        "quality_score": 0.87,
        "gemini_score": 0.9,
        "signal_score": 0.75,
        "score_reason": "..."
      },
      ...
    ],
    ...
  }
}
"""

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import redis

from .youtube_fetcher import fetch_youtube_resources
from .github_fetcher import fetch_github_resources
from .reddit_fetcher import fetch_reddit_resources
from .articles_fetcher import fetch_article_resources
from .quality_scorer import batch_score_resources

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RESEARCH_RESULTS_TTL = 60 * 60 * 24  # 24 hours

# How many subtopics to research in parallel
MAX_SUBTOPIC_WORKERS = 4
# How many sources to fetch in parallel per subtopic
MAX_SOURCE_WORKERS = 4


def _fetch_all_sources_for_subtopic(subtopic: str) -> list[dict]:
    """
    Runs all 4 fetchers concurrently for a single subtopic.
    Returns a merged, scored list of resources.
    """
    fetchers = [
        fetch_youtube_resources,
        fetch_github_resources,
        fetch_reddit_resources,
        fetch_article_resources,
    ]

    all_resources = []
    with ThreadPoolExecutor(max_workers=MAX_SOURCE_WORKERS) as executor:
        future_to_fetcher = {executor.submit(fn, subtopic): fn.__name__ for fn in fetchers}
        for future in as_completed(future_to_fetcher):
            fetcher_name = future_to_fetcher[future]
            try:
                results = future.result()
                logger.info(f"[{fetcher_name}] returned {len(results)} results for '{subtopic}'")
                all_resources.extend(results)
            except Exception as e:
                logger.error(f"[{fetcher_name}] raised exception for '{subtopic}': {e}")

    # Score and sort
    scored = batch_score_resources(all_resources)
    logger.info(f"Subtopic '{subtopic}': {len(scored)} total resources after scoring")
    return scored


def run_research_phase(session_id: str, subtopics: list[str]) -> dict:
    """
    Main entry point. Researches all subtopics in parallel.
    Saves results to Redis and returns the full results dict.

    Args:
        session_id: Unique session identifier from Phase 1.
        subtopics: List of subtopic strings from Phase 1 decomposition.

    Returns:
        Full results dict (also saved to Redis).
    """
    logger.info(f"[Phase 2] Starting research for session {session_id} — {len(subtopics)} subtopics")

    resources_by_subtopic: dict[str, list[dict]] = {}

    with ThreadPoolExecutor(max_workers=MAX_SUBTOPIC_WORKERS) as executor:
        future_to_subtopic = {
            executor.submit(_fetch_all_sources_for_subtopic, subtopic): subtopic
            for subtopic in subtopics
        }
        for future in as_completed(future_to_subtopic):
            subtopic = future_to_subtopic[future]
            try:
                resources = future.result()
                resources_by_subtopic[subtopic] = resources
            except Exception as e:
                logger.error(f"Research failed for subtopic '{subtopic}': {e}")
                resources_by_subtopic[subtopic] = []

    output = {
        "session_id": session_id,
        "subtopics": subtopics,
        "resources": resources_by_subtopic,
    }

    # Persist to Redis
    try:
        r = redis.from_url(REDIS_URL)
        redis_key = f"phase2:{session_id}"
        r.setex(redis_key, RESEARCH_RESULTS_TTL, json.dumps(output))
        logger.info(f"[Phase 2] Saved results to Redis at key '{redis_key}'")
    except Exception as e:
        logger.error(f"[Phase 2] Redis save failed: {e}")

    logger.info(f"[Phase 2] Complete for session {session_id}")
    return output


def load_research_results(session_id: str) -> dict | None:
    """
    Load Phase 2 results from Redis for a given session_id.
    Returns None if not found or expired.
    """
    try:
        r = redis.from_url(REDIS_URL)
        redis_key = f"phase2:{session_id}"
        data = r.get(redis_key)
        if data:
            return json.loads(data)
        logger.warning(f"No Phase 2 results found in Redis for session {session_id}")
        return None
    except Exception as e:
        logger.error(f"Redis load failed for session {session_id}: {e}")
        return None
