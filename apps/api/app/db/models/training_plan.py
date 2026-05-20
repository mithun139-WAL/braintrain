"""
TrainingPlan model — a 7-day AI-generated improvement plan scoped to a user.

Generated based on the user's most recent evaluation report and weak dimensions.
Each plan has N TrainingTasks. Only one plan can be ACTIVE per user at a time.
"""
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.training_task import TrainingTask
    from app.db.models.user import User


class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Source session the plan was generated from
    source_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=True
    )

    # ACTIVE | COMPLETED | SUPERSEDED
    status: Mapped[str] = mapped_column(String, default="ACTIVE", nullable=False)

    # Plan metadata
    focus_dimension: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "clarity"
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="training_plans", lazy="raise")
    tasks: Mapped[List["TrainingTask"]] = relationship(
        "TrainingTask", back_populates="training_plan", lazy="raise",
        order_by="TrainingTask.day_number, TrainingTask.sequence_order"
    )

    # ── Indexes ────────────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_training_plans_user_id_status", "user_id", "status"),
        Index("ix_training_plans_user_id_created_at", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<TrainingPlan id={self.id} user_id={self.user_id} status={self.status}>"
