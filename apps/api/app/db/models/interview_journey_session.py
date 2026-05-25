import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.interview_journey import InterviewJourney


class InterviewJourneySession(Base):
    __tablename__ = "interview_journey_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    journey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_journeys.id"), nullable=False
    )

    round_name: Mapped[str] = mapped_column(String, nullable=False)
    round_type: Mapped[str] = mapped_column(String, nullable=False)

    interviewer_persona: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    round_focus: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    difficulty: Mapped[str] = mapped_column(String, nullable=False, default="MEDIUM")

    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    journey: Mapped["InterviewJourney"] = relationship(
        "InterviewJourney", back_populates="sessions", lazy="raise"
    )

    __table_args__ = (
        Index("ix_interview_journey_sessions_journey_id", "journey_id"),
        Index("ix_interview_journey_sessions_journey_order", "journey_id", "order_index"),
    )

    def __repr__(self) -> str:
        return f"<InterviewJourneySession id={self.id} round={self.round_name} order={self.order_index}>"
