"""
Phase 3 — Roadmap Generator
Takes scored resources from Phase 2 and generates a validated JSON roadmap
using Gemini structured output.
"""

import json
import time
import logging
from typing import Optional
import google.generativeai as genai
from pydantic import BaseModel, ValidationError, field_validator
from app.models import LearningPath, Module, Resource, Project, Checkpoint
from app.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Pydantic schema (strict — Phase 5 depends on this)
# ─────────────────────────────────────────────

class ResourceSchema(BaseModel):
    title: str
    url: str
    type: str          # "video" | "article" | "repo" | "book"
    description: str
    is_free: bool = True

class CheckpointSchema(BaseModel):
    week: int
    title: str
    description: str
    criteria: list[str]  # observable pass/fail criteria

class ModuleSchema(BaseModel):
    id: str            # e.g. "m1", "m2"
    week_start: int
    week_end: int
    title: str
    description: str
    concepts: list[str]
    resources: list[ResourceSchema]
    project: Optional[str] = None
    checkpoint: CheckpointSchema

    @field_validator("resources")
    @classmethod
    def at_least_one_resource(cls, v):
        if not v:
            raise ValueError("Each module needs at least one resource")
        return v

class RoadmapSchema(BaseModel):
    session_id: str
    topic: str
    skill_level: str
    total_weeks: int
    modules: list[ModuleSchema]
    prerequisites: list[str]
    final_project: str

    @field_validator("modules")
    @classmethod
    def at_least_two_modules(cls, v):
        if len(v) < 2:
            raise ValueError("Roadmap needs at least 2 modules")
        return v


# ─────────────────────────────────────────────
# Prompt builder
# ─────────────────────────────────────────────

TOP_K = 5  # top resources per subtopic to inject into prompt

def _pick_top_resources(scored_resources: list[dict], top_k: int = TOP_K) -> list[dict]:
    """Select top-K resources sorted by Gemini quality score."""
    sorted_res = sorted(scored_resources, key=lambda x: x.get("score", 0), reverse=True)
    return sorted_res[:top_k]

def _build_prompt(
    session_id: str,
    topic: str,
    skill_level: str,
    scored_resources: list[dict],
    user_notes: Optional[str] = None,
) -> str:
    top_resources = _pick_top_resources(scored_resources)

    resource_block = "\n".join(
        f"- [{r['type']}] {r['title']} ({r['url']}) — score: {r.get('score', 0):.2f}"
        for r in top_resources
    )

    user_notes_block = (
        f"\n\nUser has also uploaded personal notes/PDFs. Incorporate relevant content:\n{user_notes[:3000]}"
        if user_notes
        else ""
    )

    return f"""You are an expert curriculum designer. Generate a complete, structured learning roadmap.

TOPIC: {topic}
SKILL LEVEL: {skill_level}
SESSION ID: {session_id}

TOP CURATED RESOURCES (use these — do not invent URLs):
{resource_block}
{user_notes_block}

OUTPUT REQUIREMENTS:
- Return ONLY valid JSON matching the schema below. No markdown, no preamble, no explanation.
- session_id must be exactly: {session_id}
- Include 4–8 modules progressing from prerequisites → fundamentals → intermediate → advanced → capstone
- Each module must have week_start, week_end, at least 2 concepts, at least 1 resource (from the list above), and a checkpoint
- checkpoint.criteria must list 2–4 observable pass/fail criteria (e.g. "Can implement X from scratch")
- final_project must be a concrete, portfolio-worthy project description
- All resource URLs must come from the provided resource list. Do NOT invent URLs.
- is_free must be accurate (GitHub, YouTube, ArXiv = true; Coursera paid = false)

JSON SCHEMA:
{{
  "session_id": "string",
  "topic": "string",
  "skill_level": "string",
  "total_weeks": number,
  "prerequisites": ["string"],
  "modules": [
    {{
      "id": "m1",
      "week_start": 1,
      "week_end": 2,
      "title": "string",
      "description": "string",
      "concepts": ["string"],
      "resources": [
        {{
          "title": "string",
          "url": "string",
          "type": "video|article|repo|book",
          "description": "string",
          "is_free": true
        }}
      ],
      "project": "string or null",
      "checkpoint": {{
        "week": 2,
        "title": "string",
        "description": "string",
        "criteria": ["string"]
      }}
    }}
  ],
  "final_project": "string"
}}"""


# ─────────────────────────────────────────────
# Core generator with retry logic
# ─────────────────────────────────────────────

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def generate_roadmap(
    session_id: str,
    topic: str,
    skill_level: str,
    scored_resources: list[dict],
    user_notes: Optional[str] = None,
) -> RoadmapSchema:
    """
    Call Gemini to generate a validated roadmap.
    Retries up to MAX_RETRIES times on validation failure.
    Raises RuntimeError if all retries fail.
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=genai.GenerationConfig(
            temperature=0.3,         # low temp for structured output
            response_mime_type="application/json",
        ),
    )

    prompt = _build_prompt(session_id, topic, skill_level, scored_resources, user_notes)
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"[roadmap_generator] attempt {attempt}/{MAX_RETRIES} for session={session_id}")
        try:
            response = model.generate_content(prompt)
            raw_text = response.text.strip()

            # strip accidental markdown fences
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]

            data = json.loads(raw_text)
            roadmap = RoadmapSchema(**data)
            logger.info(f"[roadmap_generator] success on attempt {attempt}")
            return roadmap

        except (json.JSONDecodeError, ValidationError, KeyError) as e:
            last_error = e
            logger.warning(f"[roadmap_generator] attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)

    raise RuntimeError(
        f"Roadmap generation failed after {MAX_RETRIES} attempts. Last error: {last_error}"
    )


# ─────────────────────────────────────────────
# ORM bridge — convert schema → your DB model
# ─────────────────────────────────────────────

def roadmap_to_db_model(roadmap: RoadmapSchema) -> LearningPath:
    """Convert the validated Pydantic schema into the existing LearningPath ORM model."""
    modules = []
    for m in roadmap.modules:
        resources = [
            Resource(
                title=r.title,
                url=r.url,
                type=r.type,
                description=r.description,
                is_free=r.is_free,
            )
            for r in m.resources
        ]
        checkpoint = Checkpoint(
            week=m.checkpoint.week,
            title=m.checkpoint.title,
            description=m.checkpoint.description,
            criteria=m.checkpoint.criteria,
        )
        modules.append(
            Module(
                id=m.id,
                week_start=m.week_start,
                week_end=m.week_end,
                title=m.title,
                description=m.description,
                concepts=m.concepts,
                resources=resources,
                project=m.project,
                checkpoint=checkpoint,
            )
        )

    return LearningPath(
        session_id=roadmap.session_id,
        topic=roadmap.topic,
        skill_level=roadmap.skill_level,
        total_weeks=roadmap.total_weeks,
        modules=modules,
        prerequisites=roadmap.prerequisites,
        final_project=roadmap.final_project,
    )
