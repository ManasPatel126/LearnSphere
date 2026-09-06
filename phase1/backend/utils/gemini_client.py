"""
Gemini API wrapper for Phase 1 — topic decomposition only.
Returns a validated list of Subtopic objects.

Uses google-generativeai SDK (pip install google-generativeai).
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Optional

import google.generativeai as genai
from pydantic import ValidationError

from models.schemas import GeminiDecomposition, SkillLevel, Subtopic

# ── Configure SDK once at import time ─────────────────────────────────────────
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

_MODEL_NAME  = "gemini-1.5-flash"      # fast + cheap; swap to 1.5-pro if needed
_MAX_RETRIES = 3
_RETRY_DELAY = 2   # seconds between retries


# ── Prompt builder ─────────────────────────────────────────────────────────────

def _build_prompt(
    topic: str,
    skill_level: SkillLevel,
    goal: Optional[str],
    extracted_text: Optional[str],
) -> str:
    goal_line = f"\nThe learner's stated goal: {goal}" if goal else ""
    notes_section = (
        f"\n\nThe learner also uploaded personal notes. "
        f"Use them to refine the subtopics if relevant:\n---\n{extracted_text[:3000]}\n---"
        if extracted_text
        else ""
    )

    return f"""You are a world-class curriculum designer.

Break the following topic into subtopics for a {skill_level.value}-level learner.{goal_line}

TOPIC: {topic}{notes_section}

Rules:
1. Return ONLY valid JSON — no markdown fences, no preamble, no trailing text.
2. Produce between 5 and 12 subtopics.
3. Order them from prerequisites → fundamentals → intermediate → advanced.
4. Mark truly prerequisite subtopics with "is_prerequisite": true.
5. Estimate realistic self-study hours per subtopic.

JSON schema:
{{
  "subtopics": [
    {{
      "name": "string",
      "description": "one sentence explaining what this subtopic covers",
      "order": 0,
      "is_prerequisite": false,
      "estimated_hours": 4.0
    }}
  ]
}}

Return the JSON now:"""


# ── Core function ──────────────────────────────────────────────────────────────

def decompose_topic(
    topic:          str,
    skill_level:    SkillLevel,
    goal:           Optional[str]  = None,
    extracted_text: Optional[str]  = None,
) -> list[Subtopic]:
    """
    Call Gemini to decompose a topic into subtopics.
    Retries up to _MAX_RETRIES times on bad output.
    Raises RuntimeError if all retries fail.
    """
    prompt = _build_prompt(topic, skill_level, goal, extracted_text)
    model  = genai.GenerativeModel(_MODEL_NAME)

    last_error: Optional[Exception] = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,       # low = more deterministic structure
                    max_output_tokens=2048,
                ),
            )
            raw_text = response.text.strip()

            # Strip accidental markdown fences (Gemini sometimes adds them)
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$",            "", raw_text)

            data      = json.loads(raw_text)
            validated = GeminiDecomposition(**data)

            # Convert raw dicts → typed Subtopic objects
            subtopics = []
            for idx, item in enumerate(validated.subtopics):
                item.setdefault("order", idx)
                subtopics.append(Subtopic(**item))

            return subtopics

        except (json.JSONDecodeError, ValidationError, KeyError) as exc:
            last_error = exc
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY)
            continue

        except Exception as exc:
            # Network error, quota, etc. — don't retry blindly
            raise RuntimeError(f"Gemini API error: {exc}") from exc

    raise RuntimeError(
        f"Gemini decomposition failed after {_MAX_RETRIES} attempts. "
        f"Last error: {last_error}"
    )


# ── Mock (for dev without API key) ────────────────────────────────────────────

def decompose_topic_mock(
    topic: str,
    skill_level: SkillLevel,
    **_kwargs,
) -> list[Subtopic]:
    """
    Returns a hardcoded subtopic list so you can build/test the UI
    without spending Gemini quota.
    Swap decompose_topic → decompose_topic_mock in the RQ task.
    """
    mock_names = [
        ("Prerequisites & Setup",             True,  2.0),
        ("Core Concepts & Terminology",        False, 4.0),
        ("Fundamental Techniques",             False, 6.0),
        ("Intermediate Application",           False, 8.0),
        ("Advanced Patterns",                  False, 10.0),
        ("Real-World Projects",                False, 12.0),
        ("Community & Resources",              False, 2.0),
    ]
    return [
        Subtopic(
            name=name,
            description=f"Covers {name.lower()} within {topic}.",
            order=i,
            is_prerequisite=prereq,
            estimated_hours=hours,
        )
        for i, (name, prereq, hours) in enumerate(mock_names)
    ]
