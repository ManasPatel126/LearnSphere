"""
Tests for Phase 3 — roadmap_generator.py

Run with:  pytest tests/ -v

These tests use a mock Gemini response so they work without an API key.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from app.roadmap_generator import (
    _pick_top_resources,
    _build_prompt,
    generate_roadmap,
    roadmap_to_db_model,
    RoadmapSchema,
    TOP_K,
)
from app.models import LearningPath


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

SESSION_ID = "test-session-001"
TOPIC = "Machine Learning"
SKILL_LEVEL = "beginner"

SAMPLE_SCORED_RESOURCES = [
    {"title": "ML Crash Course", "url": "https://developers.google.com/ml", "type": "article", "score": 0.95},
    {"title": "3Blue1Brown Neural Nets", "url": "https://youtube.com/watch?v=xxx", "type": "video", "score": 0.91},
    {"title": "scikit-learn GitHub", "url": "https://github.com/scikit-learn/scikit-learn", "type": "repo", "score": 0.88},
    {"title": "Hands-On ML Book", "url": "https://github.com/ageron/handson-ml2", "type": "book", "score": 0.85},
    {"title": "Fast.ai Course", "url": "https://fast.ai", "type": "video", "score": 0.80},
    {"title": "Low quality post", "url": "https://random.blog/ml", "type": "article", "score": 0.20},
]

VALID_ROADMAP_JSON = {
    "session_id": SESSION_ID,
    "topic": TOPIC,
    "skill_level": SKILL_LEVEL,
    "total_weeks": 8,
    "prerequisites": ["Basic Python", "High school math"],
    "modules": [
        {
            "id": "m1",
            "week_start": 1,
            "week_end": 2,
            "title": "Python & Math Foundations",
            "description": "Set up the environment and brush up on linear algebra.",
            "concepts": ["Vectors", "Matrices", "NumPy"],
            "resources": [
                {
                    "title": "ML Crash Course",
                    "url": "https://developers.google.com/ml",
                    "type": "article",
                    "description": "Google's free ML intro",
                    "is_free": True,
                }
            ],
            "project": None,
            "checkpoint": {
                "week": 2,
                "title": "Foundations Check",
                "description": "Can you multiply matrices by hand and in NumPy?",
                "criteria": ["Implement dot product from scratch", "Pass NumPy exercise sheet"],
            },
        },
        {
            "id": "m2",
            "week_start": 3,
            "week_end": 5,
            "title": "Supervised Learning",
            "description": "Learn regression and classification fundamentals.",
            "concepts": ["Linear Regression", "Logistic Regression", "Decision Trees"],
            "resources": [
                {
                    "title": "3Blue1Brown Neural Nets",
                    "url": "https://youtube.com/watch?v=xxx",
                    "type": "video",
                    "description": "Visual explanation of neural nets",
                    "is_free": True,
                }
            ],
            "project": "Predict house prices with scikit-learn",
            "checkpoint": {
                "week": 5,
                "title": "Supervised Learning Check",
                "description": "Build and evaluate a classifier.",
                "criteria": [
                    "Train a logistic regression model with >80% accuracy",
                    "Explain precision vs recall",
                ],
            },
        },
    ],
    "final_project": "Build an end-to-end ML pipeline: data collection, preprocessing, model training, and a simple web demo.",
}


# ─────────────────────────────────────────────
# Unit tests
# ─────────────────────────────────────────────

class TestPickTopResources:
    def test_returns_top_k(self):
        result = _pick_top_resources(SAMPLE_SCORED_RESOURCES, top_k=3)
        assert len(result) == 3

    def test_sorted_by_score_desc(self):
        result = _pick_top_resources(SAMPLE_SCORED_RESOURCES, top_k=5)
        scores = [r["score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_excludes_low_quality(self):
        result = _pick_top_resources(SAMPLE_SCORED_RESOURCES, top_k=TOP_K)
        urls = [r["url"] for r in result]
        assert "https://random.blog/ml" not in urls

    def test_handles_fewer_than_k(self):
        result = _pick_top_resources(SAMPLE_SCORED_RESOURCES[:2], top_k=10)
        assert len(result) == 2


class TestBuildPrompt:
    def test_contains_session_id(self):
        prompt = _build_prompt(SESSION_ID, TOPIC, SKILL_LEVEL, SAMPLE_SCORED_RESOURCES)
        assert SESSION_ID in prompt

    def test_contains_topic(self):
        prompt = _build_prompt(SESSION_ID, TOPIC, SKILL_LEVEL, SAMPLE_SCORED_RESOURCES)
        assert TOPIC in prompt

    def test_includes_user_notes(self):
        prompt = _build_prompt(SESSION_ID, TOPIC, SKILL_LEVEL, SAMPLE_SCORED_RESOURCES, user_notes="My custom notes here")
        assert "My custom notes here" in prompt

    def test_truncates_long_user_notes(self):
        long_notes = "x" * 10000
        prompt = _build_prompt(SESSION_ID, TOPIC, SKILL_LEVEL, SAMPLE_SCORED_RESOURCES, user_notes=long_notes)
        # notes should be capped at 3000 chars inside prompt
        assert "x" * 3001 not in prompt

    def test_no_invented_resource_urls(self):
        """Prompt should instruct Gemini not to invent URLs."""
        prompt = _build_prompt(SESSION_ID, TOPIC, SKILL_LEVEL, SAMPLE_SCORED_RESOURCES)
        assert "Do NOT invent URLs" in prompt


class TestRoadmapSchema:
    def test_valid_schema_passes(self):
        schema = RoadmapSchema(**VALID_ROADMAP_JSON)
        assert schema.session_id == SESSION_ID

    def test_missing_modules_fails(self):
        bad = {**VALID_ROADMAP_JSON, "modules": []}
        with pytest.raises(ValidationError):
            RoadmapSchema(**bad)

    def test_single_module_fails(self):
        bad = {**VALID_ROADMAP_JSON, "modules": [VALID_ROADMAP_JSON["modules"][0]]}
        with pytest.raises(ValidationError):
            RoadmapSchema(**bad)

    def test_empty_resources_in_module_fails(self):
        bad_modules = [
            {**VALID_ROADMAP_JSON["modules"][0], "resources": []},
            VALID_ROADMAP_JSON["modules"][1],
        ]
        bad = {**VALID_ROADMAP_JSON, "modules": bad_modules}
        with pytest.raises(ValidationError):
            RoadmapSchema(**bad)


class TestGenerateRoadmap:
    def _mock_gemini_response(self, return_json: dict):
        mock_response = MagicMock()
        mock_response.text = json.dumps(return_json)
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        return mock_model

    @patch("app.roadmap_generator.genai.GenerativeModel")
    @patch("app.roadmap_generator.genai.configure")
    def test_successful_generation(self, mock_configure, mock_model_cls):
        mock_model_cls.return_value = self._mock_gemini_response(VALID_ROADMAP_JSON)
        result = generate_roadmap(SESSION_ID, TOPIC, SKILL_LEVEL, SAMPLE_SCORED_RESOURCES)
        assert isinstance(result, RoadmapSchema)
        assert result.session_id == SESSION_ID
        assert len(result.modules) == 2

    @patch("app.roadmap_generator.genai.GenerativeModel")
    @patch("app.roadmap_generator.genai.configure")
    def test_strips_markdown_fences(self, mock_configure, mock_model_cls):
        mock_response = MagicMock()
        mock_response.text = f"```json\n{json.dumps(VALID_ROADMAP_JSON)}\n```"
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_cls.return_value = mock_model

        result = generate_roadmap(SESSION_ID, TOPIC, SKILL_LEVEL, SAMPLE_SCORED_RESOURCES)
        assert result.session_id == SESSION_ID

    @patch("app.roadmap_generator.time.sleep")  # skip actual sleeping
    @patch("app.roadmap_generator.genai.GenerativeModel")
    @patch("app.roadmap_generator.genai.configure")
    def test_retries_on_bad_json(self, mock_configure, mock_model_cls, mock_sleep):
        mock_response = MagicMock()
        mock_response.text = "this is not json"
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_cls.return_value = mock_model

        with pytest.raises(RuntimeError, match="failed after"):
            generate_roadmap(SESSION_ID, TOPIC, SKILL_LEVEL, SAMPLE_SCORED_RESOURCES)
        assert mock_model.generate_content.call_count == 3  # MAX_RETRIES


class TestRoadmapToDbModel:
    def test_converts_to_learning_path(self):
        schema = RoadmapSchema(**VALID_ROADMAP_JSON)
        lp = roadmap_to_db_model(schema)
        assert isinstance(lp, LearningPath)
        assert lp.session_id == SESSION_ID
        assert len(lp.modules) == 2

    def test_resources_preserved(self):
        schema = RoadmapSchema(**VALID_ROADMAP_JSON)
        lp = roadmap_to_db_model(schema)
        first_resource = lp.modules[0].resources[0]
        assert first_resource.url == "https://developers.google.com/ml"

    def test_checkpoint_criteria_preserved(self):
        schema = RoadmapSchema(**VALID_ROADMAP_JSON)
        lp = roadmap_to_db_model(schema)
        criteria = lp.modules[0].checkpoint.criteria
        assert len(criteria) == 2
        assert "Implement dot product from scratch" in criteria
