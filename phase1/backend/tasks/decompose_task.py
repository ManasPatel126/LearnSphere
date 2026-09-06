"""
RQ background task — Phase 1 core worker.

Flow:
  1. Load session from Redis
  2. Extract text from any uploaded files
  3. Call Gemini to decompose topic → subtopics
  4. Write subtopics back to session in Redis
  5. Set status = done (or failed)

This task is enqueued by POST /api/sessions and polled via GET /api/sessions/:id
"""

from __future__ import annotations

import os
import traceback
from typing import Optional

from redis import Redis

from models.schemas import Session, SessionStatus, UploadedFile
from models.session_store import get, save, update_status
from utils.file_parser import safe_extract
from utils.gemini_client import decompose_topic

# Swap to decompose_topic_mock while developing without API key:
# from utils.gemini_client import decompose_topic_mock as decompose_topic


def run_decompose(session_id: str, redis_url: str) -> None:
    """
    Entry point for RQ worker.
    redis_url is passed in because RQ workers don't share the Flask app context.
    """
    redis = Redis.from_url(redis_url)

    # ── 1. Load session ────────────────────────────────────────────────────────
    session: Optional[Session] = get(redis, session_id)
    if session is None:
        # Nothing we can do — session doesn't exist
        print(f"[decompose_task] ERROR: session {session_id} not found in Redis")
        return

    # Mark as in-progress
    session.status = SessionStatus.decomposing
    save(redis, session)

    try:
        # ── 2. Extract text from uploads ───────────────────────────────────────
        combined_text: Optional[str] = None
        for uf in session.uploaded_files:
            text = safe_extract(uf.storage_path)
            if text:
                uf.extracted_text = text
                combined_text = (combined_text or "") + "\n\n" + text

        # ── 3. Call Gemini ─────────────────────────────────────────────────────
        subtopics = decompose_topic(
            topic=session.topic,
            skill_level=session.skill_level,
            goal=session.goal,
            extracted_text=combined_text,
        )

        # ── 4. Persist results ─────────────────────────────────────────────────
        session.subtopics = subtopics
        session.status    = SessionStatus.done
        save(redis, session)

        print(
            f"[decompose_task] ✓ session {session_id} done — "
            f"{len(subtopics)} subtopics"
        )

    except Exception as exc:
        tb = traceback.format_exc()
        print(f"[decompose_task] ✗ session {session_id} failed:\n{tb}")
        update_status(redis, session_id, SessionStatus.failed, error=str(exc))
