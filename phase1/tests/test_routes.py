"""
Integration tests for Phase 1 Flask routes.
Uses fakeredis so no real Redis needed.
Run: pytest tests/test_routes.py -v
"""

import pytest
import fakeredis
from unittest.mock import patch, MagicMock

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))

from app import create_app
from models.schemas import Subtopic, SkillLevel


@pytest.fixture
def app():
    application = create_app()
    application.config["TESTING"] = True

    # Replace real Redis with fakeredis
    fake_redis = fakeredis.FakeRedis()
    application.redis = fake_redis

    # Replace RQ queue with a mock that captures enqueued jobs
    mock_queue = MagicMock()
    mock_queue.enqueue.return_value = MagicMock(id="test-job-id")
    application.task_queue = mock_queue

    return application


@pytest.fixture
def client(app):
    return app.test_client()


class TestCreateSession:
    def test_valid_form(self, client):
        resp = client.post(
            "/api/sessions",
            data={"topic": "Python", "skill_level": "beginner"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert "session_id" in data
        assert data["status"] == "pending"
        assert data["topic"] == "Python"

    def test_missing_topic(self, client):
        resp = client.post(
            "/api/sessions",
            data={"skill_level": "beginner"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 422

    def test_invalid_skill_level(self, client):
        resp = client.post(
            "/api/sessions",
            data={"topic": "Rust", "skill_level": "god-tier"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 422


class TestGetSession:
    def test_not_found(self, client):
        resp = client.get("/api/sessions/nonexistent-id")
        assert resp.status_code == 404

    def test_found_after_create(self, client):
        create_resp = client.post(
            "/api/sessions",
            data={"topic": "VLSI", "skill_level": "advanced"},
            content_type="multipart/form-data",
        )
        session_id = create_resp.get_json()["session_id"]

        get_resp = client.get(f"/api/sessions/{session_id}")
        assert get_resp.status_code == 200
        data = get_resp.get_json()
        assert data["session_id"] == session_id
        assert data["topic"] == "VLSI"

    def test_delete_session(self, client):
        create_resp = client.post(
            "/api/sessions",
            data={"topic": "Go", "skill_level": "intermediate"},
            content_type="multipart/form-data",
        )
        session_id = create_resp.get_json()["session_id"]

        del_resp = client.delete(f"/api/sessions/{session_id}")
        assert del_resp.status_code == 200

        get_resp = client.get(f"/api/sessions/{session_id}")
        assert get_resp.status_code == 404
