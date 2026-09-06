"""
Phase 5 — /result/<session_id>
Returns the stored roadmap JSON for a given session.
Assumes roadmap was saved to DB/cache in Phase 3.
"""

import json
import os
import redis
from flask import Blueprint, jsonify

result_bp = Blueprint("result", __name__)

_redis = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    decode_responses=True,
)


@result_bp.route("/result/<session_id>", methods=["GET"])
def get_result(session_id: str):
    """Return saved roadmap JSON for session_id."""
    raw = _redis.get(f"roadmap:{session_id}")
    if not raw:
        return jsonify({"error": "Session not found or expired"}), 404

    try:
        roadmap = json.loads(raw)
    except json.JSONDecodeError:
        return jsonify({"error": "Corrupt roadmap data"}), 500

    return jsonify({"session_id": session_id, "roadmap": roadmap})
