"""
Session read routes:
  GET  /api/sessions/:id          — poll for status + subtopics
  GET  /api/sessions              — list all (dev helper)
  DELETE /api/sessions/:id        — remove session
"""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from models.session_store import get, list_sessions, save
from models.schemas import SessionStatus

session_bp = Blueprint("sessions", __name__)


@session_bp.get("/sessions/<session_id>")
def get_session(session_id: str):
    """
    Poll this endpoint after POST /api/sessions until status == 'done' or 'failed'.
    Frontend polls every 2 seconds.

    Returns:
      200  full session JSON
      404  { detail: "Session not found" }
    """
    session = get(current_app.redis, session_id)
    if session is None:
        return jsonify({"detail": "Session not found"}), 404

    return jsonify(
        {
            "session_id":    session.session_id,
            "status":        session.status.value,
            "topic":         session.topic,
            "skill_level":   session.skill_level.value,
            "goal":          session.goal,
            "subtopics": [
                {
                    "id":              st.id,
                    "name":            st.name,
                    "description":     st.description,
                    "order":           st.order,
                    "is_prerequisite": st.is_prerequisite,
                    "estimated_hours": st.estimated_hours,
                }
                for st in session.subtopics
            ],
            "uploaded_files": [
                {
                    "filename":   uf.filename,
                    "size_bytes": uf.size_bytes,
                    "page_count": uf.page_count,
                }
                for uf in session.uploaded_files
            ],
            "error":      session.error,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
    )


@session_bp.get("/sessions")
def list_all_sessions():
    """Dev-only — list recent sessions."""
    sessions = list_sessions(current_app.redis)
    return jsonify(
        [
            {
                "session_id":  s.session_id,
                "topic":       s.topic,
                "status":      s.status.value,
                "created_at":  s.created_at.isoformat(),
            }
            for s in sessions
        ]
    )


@session_bp.delete("/sessions/<session_id>")
def delete_session(session_id: str):
    session = get(current_app.redis, session_id)
    if session is None:
        return jsonify({"detail": "Session not found"}), 404
    current_app.redis.delete(f"session:{session_id}")
    return jsonify({"deleted": session_id})
