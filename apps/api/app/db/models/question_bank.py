"""
QuestionBank model — maps to Prisma `QuestionBank` model.

Two sources:
  HUMAN     — manually contributed via POST /question-bank
  GENERATED — auto-saved by OpenAIQuestionGenerationProvider (dataset flywheel)

Bank-first question selection strategy (QuestionsService):
  1. Try QuestionBankService.pick_question() — picks from bank, increments usage_count
  2. Fall back to LLM generation if no bank match
  This index supports the bank-first query: (topic_id, difficulty, deleted_at)
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import DifficultyLevel, InterviewType

if TYPE_CHECKING:
    from app.db.models.topic import Topic
    from app.db.models.user import User


class QuestionBank(Base):
    __tablename__ = "question_bank"   # matches migration — do NOT rename to question_banks

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content: Mapped[str] = mapped_column(String, nullable=False)
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False
    )

    difficulty: Mapped[DifficultyLevel] = mapped_column(
        String,  # stored as string to avoid enum migration complexity
        nullable=False,
    )
    interview_type: Mapped[Optional[InterviewType]] = mapped_column(
        String, nullable=True
    )

    # "HUMAN" | "GENERATED" — not a PG enum, stored as plain string (matches Prisma)
    source: Mapped[str] = mapped_column(String, default="HUMAN", nullable=False)
    is_global: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Incremented each time this question is picked during a session
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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
    topic: Mapped["Topic"] = relationship("Topic", back_populates="question_bank_items", lazy="raise")
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="question_bank_items", lazy="raise"
    )

    # ── Indexes ────────────────────────────────────────────────────────────────
    __table_args__ = (
        # Primary bank-first selection query: topic + difficulty (excludes deleted)
        Index("ix_question_banks_topic_difficulty_deleted_at", "topic_id", "difficulty", "deleted_at"),
        # Filter HUMAN vs GENERATED for analytics/admin
        Index("ix_question_banks_source_topic_id", "source", "topic_id"),
        # Retained for query compatibility
        Index("ix_question_banks_topic_id_difficulty", "topic_id", "difficulty"),
    )

    def __repr__(self) -> str:
        return f"<QuestionBank id={self.id} difficulty={self.difficulty} source={self.source}>"
