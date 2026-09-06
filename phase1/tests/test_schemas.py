"""
Unit tests for Phase 1 schemas and utilities.
Run: pytest tests/ -v
"""

import pytest
from pydantic import ValidationError

from backend.models.schemas import (
    Session,
    SessionCreate,
    SessionStatus,
    SkillLevel,
    Subtopic,
    GeminiDecomposition,
)


# ── SessionCreate ──────────────────────────────────────────────────────────────

class TestSessionCreate:
    def test_valid(self):
        s = SessionCreate(topic="Machine Learning", skill_level="beginner")
        assert s.topic == "Machine Learning"
        assert s.skill_level == SkillLevel.beginner

    def test_topic_whitespace_stripped(self):
        s = SessionCreate(topic="  Rust  ")
        assert s.topic == "Rust"

    def test_empty_topic_fails(self):
        with pytest.raises(ValidationError):
            SessionCreate(topic="")

    def test_invalid_skill_level(self):
        with pytest.raises(ValidationError):
            SessionCreate(topic="X", skill_level="expert")


# ── Subtopic ───────────────────────────────────────────────────────────────────

class TestSubtopic:
    def test_valid(self):
        st = Subtopic(name="Linear Algebra", description="Vectors and matrices", order=0)
        assert st.name == "Linear Algebra"
        assert st.is_prerequisite is False

    def test_empty_name_fails(self):
        with pytest.raises(ValidationError):
            Subtopic(name="   ", description="...", order=0)

    def test_id_auto_generated(self):
        a = Subtopic(name="A", description=".", order=0)
        b = Subtopic(name="B", description=".", order=1)
        assert a.id != b.id


# ── GeminiDecomposition ────────────────────────────────────────────────────────

class TestGeminiDecomposition:
    def test_valid(self):
        data = {
            "subtopics": [
                {"name": "A", "description": "desc", "order": 0}
            ]
        }
        gd = GeminiDecomposition(**data)
        assert len(gd.subtopics) == 1

    def test_empty_subtopics_fails(self):
        with pytest.raises(ValidationError):
            GeminiDecomposition(subtopics=[])


# ── Session ────────────────────────────────────────────────────────────────────

class TestSession:
    def test_default_status(self):
        s = Session(topic="VLSI", skill_level=SkillLevel.advanced)
        assert s.status == SessionStatus.pending

    def test_redis_roundtrip(self):
        s = Session(topic="VLSI", skill_level=SkillLevel.advanced)
        s.subtopics = [
            Subtopic(name="Logic Gates", description=".", order=0)
        ]
        raw       = s.to_redis()
        recovered = Session.from_redis(raw)
        assert recovered.session_id == s.session_id
        assert len(recovered.subtopics) == 1
        assert recovered.subtopics[0].name == "Logic Gates"
