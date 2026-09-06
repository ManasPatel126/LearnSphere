"""
Thin wrapper around Redis for session CRUD.
All Phase 1 state lives here; later phases read the same keys.
"""

from __future__ import annotations

import json
from typing import Optional

from redis import Redis

from models.schemas import Session, SessionStatus

_SESSION_PREFIX = "session:"
_TTL_SECONDS    = 60 * 60 * 24 * 7   # 7 days


def _key(session_id: str) -> str:
    return f"{_SESSION_PREFIX}{session_id}"


def save(redis: Redis, session: Session) -> None:
    """Persist (or overwrite) a session. Resets the TTL."""
    session.mark_updated()
    redis.setex(_key(session.session_id), _TTL_SECONDS, session.to_redis())


def get(redis: Redis, session_id: str) -> Optional[Session]:
    raw = redis.get(_key(session_id))
    if raw is None:
        return None
    return Session.from_redis(raw)


def update_status(
    redis: Redis,
    session_id: str,
    status: SessionStatus,
    error: Optional[str] = None,
) -> Optional[Session]:
    session = get(redis, session_id)
    if session is None:
        return None
    session.status = status
    if error:
        session.error = error
    save(redis, session)
    return session


def list_sessions(redis: Redis, limit: int = 50) -> list[Session]:
    """Scan Redis for all session keys (dev/debug helper)."""
    keys   = redis.keys(f"{_SESSION_PREFIX}*")
    result = []
    for key in keys[:limit]:
        raw = redis.get(key)
        if raw:
            try:
                result.append(Session.from_redis(raw))
            except Exception:
                pass
    return sorted(result, key=lambda s: s.created_at, reverse=True)
