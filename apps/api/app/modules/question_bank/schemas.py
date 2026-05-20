"""
Question Bank module — Pydantic request / response schemas.

Mirrors the NestJS CreateQuestionBankDto.
"""
import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, field_validator


# ── Request schemas ────────────────────────────────────────────────────────────

DifficultyLiteral = Literal["EASY", "MEDIUM", "HARD"]
InterviewTypeLiteral = Literal["TECHNICAL", "BEHAVIORAL", "MIXED", "GROUP_DISCUSSION", "RAPID_FIRE"]


class CreateQuestionBankRequest(BaseModel):
    content: str
    topic_id: uuid.UUID
    difficulty: DifficultyLiteral
    interview_type: InterviewTypeLiteral
    is_global: bool = False

    @field_validator("content")
    @classmethod
    def content_max(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("content must not be blank")
        if len(v) > 1000:
            raise ValueError("content must be 1000 characters or fewer")
        return v


# ── Response schemas ───────────────────────────────────────────────────────────


class TopicRefResponse(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class QuestionBankResponse(BaseModel):
    id: uuid.UUID
    content: str
    topic_id: uuid.UUID
    difficulty: str
    interview_type: Optional[str] = None
    source: str
    is_global: bool
    created_by_user_id: Optional[uuid.UUID] = None
    usage_count: int
    created_at: datetime
    updated_at: datetime
    topic: Optional[TopicRefResponse] = None

    model_config = {"from_attributes": True}
