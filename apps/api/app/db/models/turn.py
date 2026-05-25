"""
Turn model — an individual question-answer exchange within an interview session.

Tracks turn-level metrics and analysis signals.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.interview_session import InterviewSession


class Turn(Base):
    __tablename__ = "turns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)

    transcript: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hesitation_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    filler_word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    response_latency_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    answer_quality: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<Turn id={self.id} session_id={self.session_id} index={self.turn_index}>"
