"""
RQ Task — Phase 2
Wraps run_research_phase as an RQ background job so Flask can enqueue it
and the worker picks it up asynchronously.

Usage from Flask:
    from redis import Redis
    from rq import Queue
    from research_engine.tasks import research_task

    q = Queue(connection=Redis.from_url(REDIS_URL))
    job = q.enqueue(research_task, session_id, subtopics, job_timeout=300)
    return {"job_id": job.id}

Polling from frontend:
    GET /api/job/<job_id>/status
    → {"status": "queued|started|finished|failed", "result": {...} | null}
"""

import logging
from .orchestrator import run_research_phase

logger = logging.getLogger(__name__)


def research_task(session_id: str, subtopics: list[str]) -> dict:
    """
    RQ-compatible task function. Called by the RQ worker process.
    Returns the full research results dict (also stored in Redis by the orchestrator).
    """
    logger.info(f"[RQ Task] research_task started — session={session_id}, subtopics={subtopics}")
    result = run_research_phase(session_id, subtopics)
    logger.info(f"[RQ Task] research_task complete — session={session_id}")
    return result
