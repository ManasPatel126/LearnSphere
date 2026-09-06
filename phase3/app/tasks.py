"""
RQ task: generate_roadmap_task
Enqueued by the Flask route after Phase 2 completes.
Writes the resulting roadmap JSON to the DB + Redis cache.
"""

import json
import logging
import redis
from app.config import settings
from app.roadmap_generator import generate_roadmap, roadmap_to_db_model

logger = logging.getLogger(__name__)


def generate_roadmap_task(
    session_id: str,
    topic: str,
    skill_level: str,
    scored_resources: list[dict],
    user_notes: str | None = None,
) -> dict:
    """
    RQ entry point. Returns the roadmap as a plain dict so RQ can serialise it.

    Workflow:
    1. Call Gemini via roadmap_generator.generate_roadmap()
    2. Validate with Pydantic (already done inside generate_roadmap)
    3. Convert to LearningPath ORM model
    4. Cache JSON in Redis under key  roadmap:<session_id>
    5. Return dict (RQ stores this as the job result)
    """
    logger.info(f"[task] generate_roadmap_task started for session={session_id}")

    # 1 + 2: generate + validate
    roadmap_schema = generate_roadmap(
        session_id=session_id,
        topic=topic,
        skill_level=skill_level,
        scored_resources=scored_resources,
        user_notes=user_notes,
    )

    # 3: ORM model (ready for DB insert in your existing SQLAlchemy setup)
    learning_path = roadmap_to_db_model(roadmap_schema)
    roadmap_dict = learning_path.to_dict()

    # 4: cache in Redis (Phase 5 reads this for the chatbot + UI)
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.set(
            f"roadmap:{session_id}",
            json.dumps(roadmap_dict),
            ex=60 * 60 * 24 * 7,   # 7-day TTL
        )
        logger.info(f"[task] roadmap cached in Redis for session={session_id}")
    except Exception as e:
        logger.warning(f"[task] Redis cache failed (non-fatal): {e}")

    logger.info(f"[task] generate_roadmap_task complete for session={session_id}")
    return roadmap_dict
