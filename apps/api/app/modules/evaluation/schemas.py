"""
Evaluation module — Pydantic schemas.

Response shape matches the NestJS SessionEvaluationResponseDto /
evaluation-response.mapper.ts output exactly.

Matches NestJS:
  apps/backend/src/modules/evaluation/dto/session-evaluation-response.dto.ts
  apps/backend/src/modules/evaluation/dto/evaluation-response.mapper.ts
"""
import uuid
from typing import Optional

from pydantic import BaseModel


class EvaluationDimensionsSchema(BaseModel):
    """Per-dimension scores — all 0–100 except technical (may be null for behavioral).

    hesitation was removed in v1.1.0: the field was always 0.0 in all production
    providers (effectively returning a fake 100 after inversion). The signal it
    was intended to capture (composure under pressure) is now correctly measured
    by pressure_score and thinking_depth_score. See PerformanceSignal comment.
    """
    clarity: float
    structure: float
    depth: float
    confidence: float
    communication: float
    technical: Optional[float]  # null for behavioral sessions
    pressure: float             # server-computed from response_time_ms
    thinking_depth: float       # server-computed from thinking_time_ms


class DifficultyProgressionSchema(BaseModel):
    """Session-level difficulty arc: where the adaptive engine started vs ended."""
    started_at: str   # session base difficulty (e.g. "MEDIUM")
    ended_at: str     # difficulty of the last question asked


class SessionEvaluationResponseSchema(BaseModel):
    """
    Full evaluation result returned by:
      GET  /sessions/:id/evaluation
      POST /sessions/:id/evaluation/analyze
    """
    session_id: uuid.UUID
    overall_score: float
    first_answer_score: Optional[float] = None
    post_followup_score: Optional[float] = None
    summary: str
    dimensions: EvaluationDimensionsSchema
    strengths: list[str]
    improvements: list[str]
    difficulty_progression: DifficultyProgressionSchema
    evaluated_at: str  # ISO-8601 string
