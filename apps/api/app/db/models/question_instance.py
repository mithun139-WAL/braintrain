"""
QuestionInstance model — maps to Prisma `QuestionInstance` model.

Represents a specific question asked within a session.
sequence_order is 1-based and unique within a session.
Max 20 questions per session (enforced in QuestionsService).
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import DifficultyLevel

if TYPE_CHECKING:
    from app.db.models.interview_session import InterviewSession
    from app.db.models.response_instance import ResponseInstance


class QuestionInstance(Base):
    __tablename__ = "question_instances"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(String, nullable=False)
    difficulty: Mapped[str] = mapped_column(String, nullable=False)  # DifficultyLevel string
    reference_facts: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-based
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="questions", lazy="raise"
    )
    # One-to-one: one response per question (enforced by UniqueConstraint on ResponseInstance)
    responses: Mapped[List["ResponseInstance"]] = relationship(
        "ResponseInstance", back_populates="question", lazy="raise"
    )

    # ── Constraints & Indexes ─────────────────────────────────────────────────
    __table_args__ = (
        # Enforce unique sequence positions within a session
        UniqueConstraint("session_id", "sequence_order", name="uq_question_instance_session_order"),
        # Load all questions for a session in order (most frequent query)
        Index(
            "ix_question_instances_session_id_sequence_order_deleted_at",
            "session_id",
            "sequence_order",
            "deleted_at",
        ),
    )

    def __repr__(self) -> str:
        return f"<QuestionInstance id={self.id} session_id={self.session_id} order={self.sequence_order}>"
