"""
Topics module — Pydantic request / response schemas.

Mirrors the NestJS CreateTopicDto (from @braintrain/shared) and the
enriched topic response shape returned by TopicsService.listTopics /
getTopicById (avgScore, lastSessionDate, sessionCount).
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


# ── Request schemas ────────────────────────────────────────────────────────────


class CreateTopicRequest(BaseModel):
    name: str
    description: Optional[str] = None
    parent_topic_id: Optional[uuid.UUID] = None

    model_config = {"populate_by_name": True}

    @field_validator("name")
    @classmethod
    def name_max(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        if len(v) > 150:
            raise ValueError("name must be 150 characters or fewer")
        return v

    @field_validator("description")
    @classmethod
    def description_max(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip() or None  # blank → null
            if v and len(v) > 500:
                raise ValueError("description must be 500 characters or fewer")
        return v


# ── Response schemas ───────────────────────────────────────────────────────────


class TopicRefResponse(BaseModel):
    """Lightweight topic reference used inside parent_topic and subtopics."""
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class TopicResponse(BaseModel):
    """Full topic response with computed analytics fields."""
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_global: bool
    created_by_user_id: Optional[uuid.UUID] = None
    parent_topic_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    # Eagerly loaded relationships
    parent_topic: Optional[TopicRefResponse] = None
    subtopics: list[TopicRefResponse] = []

    # Computed analytics (server-side)
    avg_score: int = 0
    last_session_date: Optional[datetime] = None
    session_count: int = 0

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str
