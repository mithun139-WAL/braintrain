import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.interview_journey_session import InterviewJourneySession
    from app.db.models.user import User


class InterviewJourney(Base):
    __tablename__ = "interview_journeys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    company_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role_title: Mapped[str] = mapped_column(String, nullable=False)

    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    resume_text: Mapped[str] = mapped_column(Text, nullable=False)

    extracted_skills: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    extracted_signals: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    candidate_level: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role_category: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    generated_plan: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(String, default="CREATED", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="journeys", lazy="raise")
    sessions: Mapped[List["InterviewJourneySession"]] = relationship(
        "InterviewJourneySession", back_populates="journey", lazy="raise",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_interview_journeys_user_id", "user_id"),
        Index("ix_interview_journeys_user_id_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<InterviewJourney id={self.id} status={self.status} role={self.role_title}>"
