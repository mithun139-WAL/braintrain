"""
InterviewSession model — maps to Prisma `InterviewSession` model.

State machine (enforced in SessionsService):
  CREATED → ACTIVE → COMPLETED → ANALYZED
                              └→ CANCELLED

Key invariant: when status transitions to COMPLETED, an EvaluationJob(PENDING)
is atomically created in the same transaction (see sessions/service.py).
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import DifficultyLevel, InterviewMode, InterviewType, SessionStatus

if TYPE_CHECKING:
    from app.db.models.evaluation_job import EvaluationJob
    from app.db.models.evaluation_report import EvaluationReport
    from app.db.models.question_instance import QuestionInstance
    from app.db.models.topic import Topic
    from app.db.models.user import User


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False
    )

    # Stored as strings to avoid PostgreSQL enum migration complexity.
    # Values are validated at the Pydantic schema layer.
    interview_mode: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    interview_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    difficulty: Mapped[str] = mapped_column(String, nullable=False)
    adaptive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_voice: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Stores AI interviewer personality configuration (Panel mode etc.)
    personality_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(String, default=SessionStatus.CREATED, nullable=False)

    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="sessions", lazy="raise")
    topic: Mapped["Topic"] = relationship("Topic", back_populates="sessions", lazy="raise")
    questions: Mapped[List["QuestionInstance"]] = relationship(
        "QuestionInstance", back_populates="session", lazy="raise"
    )
    # One-to-one: a session has at most one evaluation report
    evaluation: Mapped[Optional["EvaluationReport"]] = relationship(
        "EvaluationReport", back_populates="session", uselist=False, lazy="raise"
    )
    # One-to-one: a session has at most one evaluation job
    evaluation_job: Mapped[Optional["EvaluationJob"]] = relationship(
        "EvaluationJob", back_populates="session", uselist=False, lazy="raise"
    )

    # ── Indexes ────────────────────────────────────────────────────────────────
    __table_args__ = (
        # Hot path: GET /sessions?status=COMPLETED — every user dashboard load
        Index("ix_interview_sessions_user_id_status_deleted_at", "user_id", "status", "deleted_at"),
        # Analytics trend: sessions by userId ordered by createdAt DESC
        Index("ix_interview_sessions_user_id_created_at", "user_id", "created_at"),
        # Topic analytics: all sessions for a topic
        Index("ix_interview_sessions_topic_id_user_id", "topic_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<InterviewSession id={self.id} status={self.status}>"
