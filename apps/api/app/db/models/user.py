"""
User model — maps to Prisma `User` model.

Soft-delete pattern: deleted_at IS NULL = active user.
Plan enforcement: plan_type + monthly_session_count + monthly_evaluation_credits.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.coaching_session import CoachingSession
    from app.db.models.interview_journey import InterviewJourney
    from app.db.models.interview_session import InterviewSession
    from app.db.models.otp_code import OtpCode
    from app.db.models.question_bank import QuestionBank
    from app.db.models.skill_tag import UserSkillPreference
    from app.db.models.topic import Topic
    from app.db.models.training_plan import TrainingPlan
    from app.db.models.user_context_input import UserContextInput
    from app.db.models.user_skill_preference import UserSkillPreference
    from app.db.models.candidate_mind_state import CandidateMindState


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # ── Email verification ─────────────────────────────────────────────────────
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")
    email_confirmation_token: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    email_confirmation_expires_at: Mapped[Optional[datetime]] = mapped_column(
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

    # ── SaaS Plan & Usage Limits (Phase 3) ────────────────────────────────────
    plan_type: Mapped[str] = mapped_column(String, default="FREE", nullable=False)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    stripe_subscription_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    monthly_session_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    monthly_evaluation_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    usage_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    # lazy="raise" prevents accidental N+1 lazy loading in async context.
    # Use selectinload() / joinedload() in repository queries when needed.
    sessions: Mapped[List["InterviewSession"]] = relationship(
        "InterviewSession", back_populates="user", lazy="raise"
    )
    topics: Mapped[List["Topic"]] = relationship(
        "Topic", back_populates="created_by_user", lazy="raise"
    )
    context_inputs: Mapped[List["UserContextInput"]] = relationship(
        "UserContextInput", back_populates="user", lazy="raise"
    )
    otp_codes: Mapped[List["OtpCode"]] = relationship(
        "OtpCode", back_populates="user", lazy="raise"
    )
    skill_preferences: Mapped[List["UserSkillPreference"]] = relationship(
        "UserSkillPreference", back_populates="user", lazy="raise"
    )
    question_bank_items: Mapped[List["QuestionBank"]] = relationship(
        "QuestionBank", back_populates="created_by_user", lazy="raise"
    )
    coaching_sessions: Mapped[List["CoachingSession"]] = relationship(
        "CoachingSession", back_populates="user", lazy="raise"
    )
    training_plans: Mapped[List["TrainingPlan"]] = relationship(
        "TrainingPlan", back_populates="user", lazy="raise"
    )
    journeys: Mapped[List["InterviewJourney"]] = relationship(
        "InterviewJourney", back_populates="user", lazy="raise"
    )
    mind_state: Mapped[Optional["CandidateMindState"]] = relationship(
        "CandidateMindState", back_populates="candidate", lazy="raise", uselist=False
    )

    # ── Indexes ────────────────────────────────────────────────────────────────
    __table_args__ = (
        # Soft-delete scans: WHERE deleted_at IS NULL
        Index("ix_users_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
