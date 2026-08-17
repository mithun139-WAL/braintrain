"""
Responses module — Pydantic schemas.

Audio-first design: at least one of answer_text or audio_url is required.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator


class SubmitResponseRequest(BaseModel):
    answer_text: Optional[str] = None
    audio_url: Optional[str] = None
    response_time_ms: int
    thinking_time_ms: int
    is_followup: bool = False

    @model_validator(mode="after")
    def at_least_one_input(self) -> "SubmitResponseRequest":
        has_text = bool(self.answer_text and self.answer_text.strip())
        has_audio = bool(self.audio_url and self.audio_url.strip())
        if not has_text and not has_audio:
            raise ValueError("At least one of answer_text or audio_url must be provided")
        return self

    @model_validator(mode="after")
    def non_negative_timings(self) -> "SubmitResponseRequest":
        if self.response_time_ms < 0:
            raise ValueError("response_time_ms must be >= 0")
        if self.thinking_time_ms < 0:
            raise ValueError("thinking_time_ms must be >= 0")
        return self


class ResponseInstanceResponse(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    answer_text: Optional[str] = None
    audio_url: Optional[str] = None
    response_time_ms: int
    thinking_time_ms: int
    answer_length: int
    is_followup: bool
    audio_processing_status: str
    transcribed_text: Optional[str] = None
    overall_score: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Follow-up analysis schemas ─────────────────────────────────────────────────

class FollowupExchangeSchema(BaseModel):
    """One round of follow-up Q&A sent from the frontend."""
    followup_question: str
    followup_answer: str


class FollowupRequest(BaseModel):
    """
    Request body for POST /questions/{question_id}/responses/{response_id}/followup.

    prior_exchanges carries the conversation history so far.
    Empty list = first check (right after the initial answer is submitted).
    """
    prior_exchanges: list[FollowupExchangeSchema] = []


class FollowupResponse(BaseModel):
    """Response returned by the follow-up analysis endpoint."""
    needs_followup: bool
    followup_question: Optional[str] = None   # present when needs_followup=True
    acknowledgement: str                       # brief inline feedback for the user
    gap_identified: Optional[str] = None      # present when needs_followup=True
    exchange_number: int                       # how many rounds have occurred (0-based)
