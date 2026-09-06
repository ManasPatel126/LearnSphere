"""
Flask Routes — Phase 2
Exposes two endpoints:
  POST /api/research/start  — enqueues the RQ research task
  GET  /api/research/<session_id>  — returns cached results from Redis

Register this blueprint in your main app.py:
    from phase2.routes import research_bp
    app.register_blueprint(research_bp)
"""

import os
from flask import Blueprint, request, jsonify
from redis import Redis
from rq import Queue
from rq.job import Job, NoSuchJobError

from research_engine.tasks import research_task
from research_engine.orchestrator import load_research_results

research_bp = Blueprint("research", __name__, url_prefix="/api/research")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis_conn = Redis.from_url(REDIS_URL)
_queue = Queue("research", connection=_redis_conn)


@research_bp.route("/start", methods=["POST"])
def start_research():
    """
    Body: { "session_id": "abc123", "subtopics": ["Neural Networks", ...] }
    Returns: { "job_id": "rq-job-id", "session_id": "abc123" }
    """
    data = request.get_json(force=True)
    session_id = data.get("session_id")
    subtopics = data.get("subtopics", [])

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400
    if not subtopics or not isinstance(subtopics, list):
        return jsonify({"error": "subtopics must be a non-empty list"}), 400

    job = _queue.enqueue(
        research_task,
        session_id,
        subtopics,
        job_timeout=600,  # 10 min max — parallelism keeps it well under this
    )

    return jsonify({"job_id": job.id, "session_id": session_id, "status": "queued"}), 202


@research_bp.route("/status/<job_id>", methods=["GET"])
def job_status(job_id: str):
    """
    Poll job status.
    Returns: { "status": "queued|started|finished|failed", "job_id": "..." }
    """
    try:
        job = Job.fetch(job_id, connection=_redis_conn)
        return jsonify({"job_id": job_id, "status": job.get_status().value})
    except NoSuchJobError:
        return jsonify({"error": "Job not found"}), 404


@research_bp.route("/<session_id>", methods=["GET"])
def get_research_results(session_id: str):
    """
    Retrieve completed Phase 2 results from Redis.
    Returns the full resources JSON or 404 if not ready yet.
    """
    results = load_research_results(session_id)
    if not results:
        return jsonify({"error": "Results not found or expired. Check job status first."}), 404
    return jsonify(results), 200
