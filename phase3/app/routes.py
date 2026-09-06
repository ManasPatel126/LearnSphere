"""
Flask blueprint: /roadmap
POST /roadmap/generate  — enqueue roadmap generation task
GET  /roadmap/<session_id> — fetch completed roadmap from Redis cache
"""

import json
import logging
from flask import Blueprint, request, jsonify
import redis
from rq import Queue
from app.config import settings
from app.tasks import generate_roadmap_task

logger = logging.getLogger(__name__)
bp = Blueprint("roadmap", __name__, url_prefix="/roadmap")

# RQ queue (same Redis connection as Phase 1 used)
_redis_conn = redis.from_url(settings.REDIS_URL)
_queue = Queue("roadmap", connection=_redis_conn)


@bp.post("/generate")
def enqueue_roadmap():
    """
    Expected JSON body:
    {
      "session_id": "abc123",
      "topic": "Machine Learning",
      "skill_level": "beginner",
      "scored_resources": [...],   // array from Phase 2
      "user_notes": "..."          // optional — from uploaded PDF
    }
    """
    data = request.get_json(force=True)
    required = ("session_id", "topic", "skill_level", "scored_resources")
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    job = _queue.enqueue(
        generate_roadmap_task,
        kwargs={
            "session_id": data["session_id"],
            "topic": data["topic"],
            "skill_level": data["skill_level"],
            "scored_resources": data["scored_resources"],
            "user_notes": data.get("user_notes"),
        },
        job_timeout=300,         # 5 min max
        result_ttl=60 * 60 * 24, # keep result 24 h
    )
    logger.info(f"[routes] enqueued job {job.id} for session={data['session_id']}")
    return jsonify({"job_id": job.id, "session_id": data["session_id"]}), 202


@bp.get("/<session_id>")
def get_roadmap(session_id: str):
    """Fetch the completed roadmap from Redis cache."""
    r = redis.from_url(settings.REDIS_URL)
    raw = r.get(f"roadmap:{session_id}")
    if not raw:
        return jsonify({"error": "Roadmap not found. Job may still be running."}), 404
    return jsonify(json.loads(raw)), 200


@bp.get("/status/<job_id>")
def job_status(job_id: str):
    """Poll job status. Frontend uses this to know when to switch to /roadmap/<session_id>."""
    from rq.job import Job
    try:
        job = Job.fetch(job_id, connection=_redis_conn)
        return jsonify({
            "job_id": job_id,
            "status": job.get_status().value,
            "error": str(job.exc_info) if job.is_failed else None,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404
