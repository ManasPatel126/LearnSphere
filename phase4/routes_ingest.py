"""
routes_ingest.py
================
Flask blueprint that exposes two endpoints for Phase 4:

  POST /api/ingest
      Body: { "session_id": str, "roadmap": {...}, "uploaded_texts": [...] }
      Enqueues an RQ job and returns the job_id immediately.

  GET  /api/ingest/status/<job_id>
      Polls the RQ job status. Returns progress / result / error.

Register in your app factory:
    from routes_ingest import ingest_bp
    app.register_blueprint(ingest_bp)
"""

import os
import json
import logging
from flask import Blueprint, request, jsonify
from redis import Redis
from rq import Queue
from rq.job import Job, NoSuchJobError
from tasks.ingest import ingest_roadmap

logger = logging.getLogger(__name__)

ingest_bp = Blueprint("ingest", __name__)

# ── Redis / RQ setup ──────────────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_conn = Redis.from_url(REDIS_URL)
ingest_queue = Queue("ingest", connection=redis_conn)

JOB_TIMEOUT = 60 * 30   # 30 minutes max per ingestion job


# ── POST /api/ingest ──────────────────────────────────────────────────────────

@ingest_bp.route("/api/ingest", methods=["POST"])
def start_ingestion():
    """
    Kick off a Phase 4 vector ingestion job.

    Request JSON:
    {
        "session_id":     "abc123",          # required
        "roadmap":        { ... },            # required — Phase 3 output
        "uploaded_texts": [                   # optional
            {"filename": "notes.pdf", "text": "raw extracted text..."}
        ]
    }

    Response:
    { "job_id": "rq-job-id", "status": "queued" }
    """
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id", "").strip()
    roadmap = data.get("roadmap")
    uploaded_texts = data.get("uploaded_texts", [])

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400
    if not roadmap or not isinstance(roadmap, dict):
        return jsonify({"error": "roadmap must be a non-empty object"}), 400

    job = ingest_queue.enqueue(
        ingest_roadmap,
        session_id,
        roadmap,
        uploaded_texts,
        job_timeout=JOB_TIMEOUT,
        result_ttl=60 * 60 * 24,  # keep result for 24 h
        failure_ttl=60 * 60 * 24,
    )

    logger.info("Enqueued ingestion job %s for session %s", job.id, session_id)
    return jsonify({"job_id": job.id, "status": "queued"}), 202


# ── GET /api/ingest/status/<job_id> ──────────────────────────────────────────

@ingest_bp.route("/api/ingest/status/<job_id>", methods=["GET"])
def ingestion_status(job_id: str):
    """
    Poll ingestion job status.

    Response (while running):
    { "status": "started"|"queued"|"deferred", "job_id": "..." }

    Response (on success):
    { "status": "finished", "result": { chunks_written, urls_processed, ... } }

    Response (on failure):
    { "status": "failed", "error": "..." }
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except NoSuchJobError:
        return jsonify({"error": "Job not found"}), 404

    status = job.get_status()

    if status == "finished":
        return jsonify({"status": "finished", "result": job.result, "job_id": job_id})

    if status == "failed":
        return jsonify({
            "status": "failed",
            "error": str(job.exc_info or "Unknown error"),
            "job_id": job_id,
        }), 500

    return jsonify({"status": str(status), "job_id": job_id})
