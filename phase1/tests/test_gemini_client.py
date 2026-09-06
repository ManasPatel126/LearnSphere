"""
Tests for the Gemini client — patches the SDK so no real API calls are made.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))

from models.schemas import SkillLevel
from utils.gemini_client import decompose_topic_mock


class TestMockDecompose:
    """Test the mock function (no API key needed)."""

    def test_returns_subtopics(self):
        subtopics = decompose_topic_mock("Machine Learning", SkillLevel.beginner)
        assert len(subtopics) > 0

    def test_has_prerequisites(self):
        subtopics = decompose_topic_mock("VLSI", SkillLevel.advanced)
        has_prereq = any(st.is_prerequisite for st in subtopics)
        assert has_prereq

    def test_ordered(self):
        subtopics = decompose_topic_mock("Rust", SkillLevel.intermediate)
        orders = [st.order for st in subtopics]
        assert orders == sorted(orders)


class TestRealDecomposeWithMockSDK:
    """Test the real function with a mocked Gemini SDK response."""

    def test_valid_response_parsed(self):
        mock_subtopics = [
            {
                "name": "Linear Algebra",
                "description": "Vectors, matrices, eigenvalues",
                "order": 0,
                "is_prerequisite": True,
                "estimated_hours": 4.0,
            },
            {
                "name": "Calculus",
                "description": "Derivatives and integrals",
                "order": 1,
                "is_prerequisite": True,
                "estimated_hours": 3.0,
            },
        ]
        fake_response_text = json.dumps({"subtopics": mock_subtopics})

        mock_model = MagicMock()
        mock_model.generate_content.return_value = MagicMock(text=fake_response_text)

        with patch("utils.gemini_client.genai.GenerativeModel", return_value=mock_model):
            from utils.gemini_client import decompose_topic
            result = decompose_topic("Machine Learning", SkillLevel.beginner)

        assert len(result) == 2
        assert result[0].name == "Linear Algebra"
        assert result[0].is_prerequisite is True

    def test_retries_on_bad_json(self):
        """Gemini returns garbage twice, then valid JSON on the third attempt."""
        valid = json.dumps({
            "subtopics": [
                {"name": "X", "description": ".", "order": 0}
            ]
        })
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = [
            MagicMock(text="not json at all"),
            MagicMock(text='{"oops": 1}'),
            MagicMock(text=valid),
        ]

        with patch("utils.gemini_client.genai.GenerativeModel", return_value=mock_model):
            with patch("utils.gemini_client._RETRY_DELAY", 0):
                from utils.gemini_client import decompose_topic
                result = decompose_topic("Topic", SkillLevel.beginner)

        assert len(result) == 1
        assert mock_model.generate_content.call_count == 3
