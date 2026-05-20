"""
Analytics module — Pydantic schemas.

Response shapes match NestJS AnalyticsService return values exactly.

Routes:
 GET /analytics/me          → AnalyticsResponseSchema
 GET /analytics/progression → ProgressionResponseSchema
 GET /analytics/topics/{topic_id} → TopicAnalyticsResponseSchema

Matches NestJS: apps/backend/src/modules/analytics/analytics.service.ts
"""
import uuid
from typing import Optional

from pydantic import BaseModel


# ── GET /analytics/me ─────────────────────────────────────────────────────────

class TrendItemSchema(BaseModel):
    """One data point in the chronological score trend."""
    session_id: uuid.UUID
    topic_name: str
    interview_type: Optional[str]
    analyzed_at: str          # ISO-8601
    overall_score: float
    confidence_score: float
    clarity_score: float
    structure_score: float
    depth_score: float


class ImprovementSchema(BaseModel):
    """Delta between the user's first and latest analyzed sessions."""
    overall_delta: float
    confidence_delta: float
    clarity_delta: float
    top_improved_dimension: Optional[str]  # dimension with largest positive delta
    top_weak_dimension: Optional[str]      # dimension with largest negative delta


class TopicBreakdownSchema(BaseModel):
    """Average performance across all analyzed sessions for a topic."""
    topic_id: uuid.UUID
    topic_name: str
    session_count: int
    avg_overall_score: float


class AnalyticsResponseSchema(BaseModel):
    total_sessions: int
    analyzed_sessions: int
    trend: list[TrendItemSchema]
    improvement: ImprovementSchema
    by_topic: list[TopicBreakdownSchema]


class TopicTrendItemSchema(BaseModel):
    session_id: uuid.UUID
    analyzed_at: str
    overall_score: float
    confidence_score: float
    clarity_score: float
    structure_score: float
    depth_score: float
    interview_type: Optional[str]
    interview_mode: Optional[str]
    difficulty: str


class TopicAnalyticsResponseSchema(BaseModel):
    topic_id: uuid.UUID
    total_sessions: int
    analyzed_sessions: int
    average_score: float
    score_delta: Optional[float]
    latest_score: Optional[float]
    last_session_at: Optional[str]
    trend: list[TopicTrendItemSchema]


# ── GET /analytics/progression ────────────────────────────────────────────────

class SessionRefSchema(BaseModel):
    """Minimal session summary for the progression delta banner."""
    session_id: uuid.UUID
    overall_score: Optional[float]
    analyzed_at: Optional[str]   # ISO-8601


class ProgressionResponseSchema(BaseModel):
    """
    Dopamine-loop endpoint — latest vs previous session delta.
    Designed for a "you improved by +X.X points!" banner in the app.
    """
    last_session: Optional[SessionRefSchema]
    previous_session: Optional[SessionRefSchema]
    delta: Optional[float]
