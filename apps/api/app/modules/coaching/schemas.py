"""
Coaching module — Pydantic request/response schemas.

Maps to frontend coaching.types.ts (camelCase handled by axios interceptors).
"""
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# ── Request schemas ────────────────────────────────────────────────────────────


class CreateCoachingSessionRequest(BaseModel):
    focus_area: str = "general"              # "confidence" | "clarity" | "technical" | "general"
    interview_session_id: Optional[uuid.UUID] = None  # link to a specific session for context


class SendMessageRequest(BaseModel):
    content: str


# ── Response schemas ───────────────────────────────────────────────────────────


class CoachingMessageResponse(BaseModel):
    id: uuid.UUID
    coaching_session_id: uuid.UUID
    role: str                                # "user" | "assistant"
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CoachingSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    interview_session_id: Optional[uuid.UUID] = None
    focus_area: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    messages: List[CoachingMessageResponse] = []
    message_count: int = 0              # pre-computed so list views don't need to count

    model_config = {"from_attributes": True}


class SendMessageResponse(BaseModel):
    user_message: CoachingMessageResponse
    assistant_message: CoachingMessageResponse


class CoachingSessionListResponse(BaseModel):
    data: List[CoachingSessionResponse]
    total: int
