"""
Interview Journey Pydantic schemas — request and response models.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# ── Request Schemas ────────────────────────────────────────────────────────────

class CreateJourneyRequest(BaseModel):
    role_title: str = Field(..., min_length=1, max_length=200)
    job_description: str = Field(..., min_length=10)
    resume_text: str = Field(..., min_length=10)
    company_name: str | None = None


class EditJourneyRequest(BaseModel):
    role_title: str | None = Field(None, min_length=1, max_length=200)
    job_description: str | None = Field(None, min_length=10)
    resume_text: str | None = Field(None, min_length=10)
    company_name: str | None = None


class AnalyzeJourneyRequest(BaseModel):
    journey_id: uuid.UUID


class StartRoundRequest(BaseModel):
    journey_id: uuid.UUID
    round_index: int = Field(..., ge=0)


# ── Response Schemas ───────────────────────────────────────────────────────────

class JourneyRoundResponse(BaseModel):
    id: uuid.UUID
    round_name: str
    round_type: str
    difficulty: str
    order_index: int
    completed: bool
    session_id: uuid.UUID | None = None
    interviewer_persona: dict | None = None
    round_focus: dict | None = None
    created_at: datetime


class JourneyPrerequisites(BaseModel):
    topics: list[str]
    issues: list[str]
    minimum_criteria: list[str]


class JourneyResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    company_name: str | None = None
    role_title: str
    status: str
    candidate_level: str | None = None
    role_category: str | None = None
    extracted_skills: dict | None = None
    extracted_signals: dict | None = None
    generated_plan: dict | None = None
    prerequisites: JourneyPrerequisites | None = None
    created_at: datetime
    updated_at: datetime
    sessions: list[JourneyRoundResponse] = []


class JourneyListResponse(BaseModel):
    data: list[JourneyResponse]
    total: int
    page: int
    limit: int


class AnalyzeResponse(BaseModel):
    journey_id: str
    status: str
    candidate_level: str
    role_category: str
    strengths: list[str]
    weaknesses: list[str]
    rounds: list[dict]
    verified_profile: dict
    prerequisites: JourneyPrerequisites | None = None



class StartRoundResponse(BaseModel):
    journey_session_id: str
    journey_id: str
    round_name: str
    round_type: str
    difficulty: str
    persona: dict | None = None
    round_focus: dict | None = None
    session_context: dict
    interview_session_id: str | None = None


class CompleteRoundRequest(BaseModel):
    journey_session_id: uuid.UUID
    interview_session_id: uuid.UUID


class CompleteRoundResponse(BaseModel):
    journey_session_id: str
    completed: bool
    journey_completed: bool


class JourneyFinalReportResponse(BaseModel):
    journey_id: str
    role_title: str
    company_name: str | None = None
    candidate_level: str
    hire_recommendation: str
    overall_hiring_signal: str
    strongest_round: str | None = None
    weakest_round: str | None = None
    hiring_risk_areas: list[str]
    company_fit: str
    communication_summary: str
    technical_summary: str
    recruiter_notes: str
    round_reports: list[dict]
