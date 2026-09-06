"""
POST /api/sessions  — create a new session and enqueue decomposition task.
Accepts multipart/form-data so the user can optionally upload files.
"""

from __future__ import annotations

import os

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from models.schemas import Session, SessionCreate, SessionStatus
from models.session_store import save
from tasks.decompose_task import run_decompose
from utils.upload_handler import save_upload

input_bp = Blueprint("input", __name__)

_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


@input_bp.post("/sessions")
def create_session():
    """
    Create a session, optionally accept file uploads, enqueue RQ task.

    Form fields (multipart/form-data):
      topic        string  required
      skill_level  string  optional  [beginner | intermediate | advanced]
      goal         string  optional

    File fields:
      files[]      file    optional  (multiple allowed, .pdf/.txt/.md/.rst)

    Returns:
      201  { session_id, status, topic, skill_level, subtopics, created_at, updated_at }
      422  { detail, code }
    """
    # ── Parse form fields ──────────────────────────────────────────────────────
    try:
        body = SessionCreate(
            topic=request.form.get("topic", ""),
            skill_level=request.form.get("skill_level", "beginner"),
            goal=request.form.get("goal") or None,
        )
    except ValidationError as exc:
        return jsonify({"detail": exc.errors(), "code": "VALIDATION_ERROR"}), 422

    # ── Build session ──────────────────────────────────────────────────────────
    session = Session(
        topic=body.topic,
        skill_level=body.skill_level,
        goal=body.goal,
        status=SessionStatus.pending,
    )

    # ── Handle file uploads ────────────────────────────────────────────────────
    uploaded_files = request.files.getlist("files[]")
    for file in uploaded_files:
        if not file.filename:
            continue
        try:
            uf = save_upload(file)
            session.uploaded_files.append(uf)
        except ValueError as exc:
            return jsonify({"detail": str(exc), "code": "UPLOAD_ERROR"}), 422

    # ── Persist session ────────────────────────────────────────────────────────
    save(current_app.redis, session)

    # ── Enqueue RQ task ────────────────────────────────────────────────────────
    job = current_app.task_queue.enqueue(
        run_decompose,
        args=(session.session_id, _REDIS_URL),
        job_timeout=120,          # 2 minutes max for decomposition
        result_ttl=600,
        failure_ttl=600,
    )
    session.rq_job_id = job.id
    save(current_app.redis, session)

    return (
        jsonify(
            {
                "session_id":  session.session_id,
                "status":      session.status.value,
                "topic":       session.topic,
                "skill_level": session.skill_level.value,
                "subtopics":   [],
                "created_at":  session.created_at.isoformat(),
                "updated_at":  session.updated_at.isoformat(),
            }
        ),
        201,
    )
