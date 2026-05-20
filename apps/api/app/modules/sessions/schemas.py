"""
Sessions module — Pydantic request / response schemas.

Mirrors NestJS CreateSessionDto, ListSessionsDto and the enriched session
response shapes from SessionsService.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, field_validator


# ── Literals ───────────────────────────────────────────────────────────────────

SessionStatusLiteral = Literal["CREATED", "ACTIVE", "COMPLETED", "ANALYZED", "CANCELLED"]
InterviewModeLiteral = Literal["ONE_ON_ONE_AI", "PANEL_AI", "HYBRID"]
InterviewTypeLiteral = Literal["TECHNICAL", "BEHAVIORAL", "MIXED", "GROUP_DISCUSSION", "RAPID_FIRE"]
DifficultyLiteral = Literal["EASY", "MEDIUM", "HARD"]


# ── Request schemas ────────────────────────────────────────────────────────────


class CreateSessionRequest(BaseModel):
    topic_id: uuid.UUID
    interview_mode: InterviewModeLiteral
    interview_type: InterviewTypeLiteral
    difficulty: DifficultyLiteral
    adaptive: bool
    duration_minutes: int
    personality_config: Optional[Dict[str, Any]] = None

    @field_validator("duration_minutes")
    @classmethod
    def duration_min(cls, v: int) -> int:
        if v < 5:
            raise ValueError("duration_minutes must be at least 5")
        return v


# ── Response schemas ───────────────────────────────────────────────────────────


class TopicRefResponse(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class ResponseSummaryResponse(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    answer_text: Optional[str] = None
    audio_url: Optional[str] = None
    response_time_ms: int
    thinking_time_ms: int
    overall_score: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionSummaryResponse(BaseModel):
    id: uuid.UUID
    content: str
    difficulty: str
    sequence_order: int
    generated_at: datetime
    responses: list[ResponseSummaryResponse] = []

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    topic_id: uuid.UUID
    topic_name: Optional[str] = None
    interview_mode: Optional[str] = None
    interview_type: Optional[str] = None
    difficulty: str
    adaptive: bool
    duration_minutes: int
    personality_config: Optional[Dict[str, Any]] = None
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    topic: Optional[TopicRefResponse] = None
    questions: list[QuestionSummaryResponse] = []

    model_config = {"from_attributes": True}


class EvaluationJobStatusRefResponse(BaseModel):
    status: str
    attempts: int
    last_error: Optional[str] = None

    model_config = {"from_attributes": True}


class SessionStatusResponse(BaseModel):
    session_id: uuid.UUID
    session_status: str
    evaluation_job_status: Optional[str] = None
    evaluation_attempts: int = 0
    last_error: Optional[str] = None
    overall_score: Optional[float] = None


class EvaluationScoreRefResponse(BaseModel):
    overall_score: float

    model_config = {"from_attributes": True}


class SessionListItemResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    topic_id: uuid.UUID
    interview_mode: Optional[str] = None
    interview_type: Optional[str] = None
    difficulty: str
    adaptive: bool
    duration_minutes: int
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    topic: Optional[TopicRefResponse] = None
    evaluation: Optional[EvaluationScoreRefResponse] = None
    question_count: int = 0

    model_config = {"from_attributes": True}


class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int


class SessionListResponse(BaseModel):
    data: list[SessionListItemResponse]
    meta: PaginationMeta
