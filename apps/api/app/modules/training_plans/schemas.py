"""
Training plans module — Pydantic schemas.

Field names are snake_case here; the axios interceptor on the frontend
converts them to camelCase automatically, so:
  task_type          → taskType
  focus_area         → focusArea
  duration_minutes   → durationMinutes
  focus_areas        → focusAreas
  ai_reasoning       → aiReasoning
  generated_at       → generatedAt
  expires_at         → expiresAt
  completed_task_count → completedTaskCount
  total_task_count   → totalTaskCount
  completion_percentage → completionPercentage
"""
import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


# ── Request schemas ────────────────────────────────────────────────────────────


class GeneratePlanRequest(BaseModel):
    session_id: Optional[uuid.UUID] = None   # source session for context


# ── Response schemas ───────────────────────────────────────────────────────────


class TrainingTaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    task_type: str                          # DRILL | EXERCISE | REFLECTION | PRACTICE | READING
    focus_area: str                         # e.g. "confidence", "clarity"
    duration_minutes: int
    difficulty: str                         # BEGINNER | INTERMEDIATE | ADVANCED
    completed: bool
    completed_at: Optional[datetime] = None
    instructions: List[str] = []
    success_criteria: str = ""

    model_config = {"from_attributes": True}


class TrainingPlanResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str                             # ACTIVE | COMPLETED | ARCHIVED
    focus_areas: List[str]
    ai_reasoning: str
    generated_at: datetime
    expires_at: date
    tasks: List[TrainingTaskResponse] = []
    completed_task_count: int = 0
    total_task_count: int = 0
    completion_percentage: float = 0.0

    model_config = {"from_attributes": True}


class CompleteTaskResponse(BaseModel):
    task: TrainingTaskResponse
    plan: TrainingPlanResponse
    message: str


class TrainingPlanListResponse(BaseModel):
    data: List[TrainingPlanResponse]
    total: int
