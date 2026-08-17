"""
ResponseInstance model — maps to Prisma `ResponseInstance` model.

One response per question (UniqueConstraint on question_id).
Scores are nullable until the EvaluationWorker processes the session.

Score architecture (from ARCHITECTURE.md §5.6):
  LLM-scored (6 content dimensions):
    clarity_score, structure_score, depth_score, confidence_score,
    communication_score, technical_score
  Server-computed (deterministic, not LLM):
    pressure_score     — from response_time_ms (timing curve, peak 15–45s)
    thinking_depth_score — from thinking_time_ms (timing curve, peak 4–12s)
    overall_score      — type-aware weighted formula (Behavioral vs Technical rubrics)

Audio processing state machine:
  PENDING → PROCESSING → COMPLETED | FAILED | SKIPPED
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import AudioProcessingStatus

if TYPE_CHECKING:
    from app.db.models.interview_session import InterviewSession
    from app.db.models.question_instance import QuestionInstance


class ResponseInstance(Base):
    __tablename__ = "response_instances"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_instances.id"),
        nullable=False,
    )
    # Direct session FK — required NOT NULL by the DB schema (mirrors the DB column
    # created in migration 0001). Stored here to avoid a join when looking up all
    # responses for a session without loading question_instances first.
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id"),
        nullable=False,
    )

    # Audio-first: at least one of answer_text / audio_url must be present
    # (enforced in ResponsesService, not at DB level)
    answer_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Behavioral timing — flows into server-computed pressure/thinking scores
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    thinking_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_length: Mapped[int] = mapped_column(Integer, nullable=False)
    is_followup: Mapped[bool] = mapped_column(Boolean, server_default="false", default=False, nullable=False)

    # ── Audio Signal Layer (Phase 4 — Whisper transcription) ──────────────────
    # transcribed_text is null until EvaluationWorker processes the session
    transcribed_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    audio_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    audio_processing_status: Mapped[str] = mapped_column(
        String, default=AudioProcessingStatus.SKIPPED, nullable=False
    )

    # ── PerformanceSignal scores (populated after AI evaluation) ─────────────
    clarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    clarity_evidence: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    structure_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    structure_evidence: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    depth_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    depth_evidence: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_evidence: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    communication_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    communication_evidence: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hesitation_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    technical_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # null for behavioral
    technical_evidence: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    pressure_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    thinking_depth_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evaluation_explanation: Mapped[Optional[str]] = mapped_column(String, nullable=True)


    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    question: Mapped["QuestionInstance"] = relationship(
        "QuestionInstance", back_populates="responses", lazy="raise"
    )
    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", lazy="raise"
    )

    # ── Constraints & Indexes ─────────────────────────────────────────────────
    __table_args__ = (
        # One response per question
        UniqueConstraint("question_id", name="uq_response_instance_question_id"),
        # Adaptive engine: reads overall_score for last N responses per session
        Index("ix_response_instances_question_id_overall_score", "question_id", "overall_score"),
        # Audio processing worker: find PENDING transcription jobs
        Index(
            "ix_response_instances_audio_processing_status_created_at",
            "audio_processing_status",
            "created_at",
        ),
    )

    def __repr__(self) -> str:
        return f"<ResponseInstance id={self.id} question_id={self.question_id} overall_score={self.overall_score}>"
