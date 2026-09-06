"""
Pydantic schemas for Phase 1.
These are the canonical data shapes every downstream phase depends on.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


# ── Enums ──────────────────────────────────────────────────────────────────────

class SkillLevel(str, Enum):
    beginner     = "beginner"
    intermediate = "intermediate"
    advanced     = "advanced"


class SessionStatus(str, Enum):
    pending      = "pending"       # created, waiting for RQ worker
    decomposing  = "decomposing"   # Gemini call in progress
    done         = "done"          # subtopics ready
    failed       = "failed"        # something went wrong


# ── Subtopic ───────────────────────────────────────────────────────────────────

class Subtopic(BaseModel):
    """One node in the decomposition tree."""
    id:          str = Field(default_factory=lambda: str(uuid4()))
    name:        str
    description: str
    order:       int                      # zero-based display order
    is_prerequisite: bool = False         # true → must be learned first
    estimated_hours: Optional[float] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Subtopic name cannot be empty")
        return v.strip()


# ── Uploaded file ──────────────────────────────────────────────────────────────

class UploadedFile(BaseModel):
    """Metadata for a user-uploaded PDF or note."""
    filename:     str
    storage_path: str          # absolute path on disk (or S3 key later)
    size_bytes:   int
    extracted_text: Optional[str] = None   # filled after parse step
    page_count:   Optional[int]  = None


# ── Session ────────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    """Request body for POST /api/sessions."""
    topic:       str       = Field(..., min_length=2, max_length=200)
    skill_level: SkillLevel = SkillLevel.beginner
    goal:        Optional[str] = Field(None, max_length=500)

    @field_validator("topic")
    @classmethod
    def topic_not_empty(cls, v: str) -> str:
        return v.strip()


class Session(BaseModel):
    """Full session record — stored in Redis as JSON."""
    session_id:  str = Field(default_factory=lambda: str(uuid4()))
    topic:       str
    skill_level: SkillLevel
    goal:        Optional[str]    = None
    status:      SessionStatus    = SessionStatus.pending
    subtopics:   list[Subtopic]   = []
    uploaded_files: list[UploadedFile] = []
    rq_job_id:   Optional[str]    = None
    error:       Optional[str]    = None
    created_at:  datetime         = Field(default_factory=datetime.utcnow)
    updated_at:  datetime         = Field(default_factory=datetime.utcnow)

    # helpers ──────────────────────────────────────────────────────────────────

    def to_redis(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_redis(cls, raw: str | bytes) -> "Session":
        return cls.model_validate_json(raw)

    def mark_updated(self) -> None:
        self.updated_at = datetime.utcnow()


# ── API response wrappers ──────────────────────────────────────────────────────

class SessionResponse(BaseModel):
    session_id:  str
    status:      SessionStatus
    topic:       str
    skill_level: SkillLevel
    subtopics:   list[Subtopic]
    created_at:  datetime
    updated_at:  datetime
    error:       Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str
    code:   Optional[str] = None


# ── Gemini raw response (for validation) ──────────────────────────────────────

class GeminiDecomposition(BaseModel):
    """
    Expected shape of Gemini's JSON output.
    If validation fails → caught in the task → session.status = failed.
    """
    subtopics: list[dict[str, Any]]

    @field_validator("subtopics")
    @classmethod
    def at_least_one(cls, v):
        if not v:
            raise ValueError("Gemini returned zero subtopics")
        return v
