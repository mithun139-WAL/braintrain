"""
TrainingTask model — a single micro-exercise within a TrainingPlan.

Tasks are ordered by day_number (1-7) and sequence_order within a day.
Users complete tasks to track progress through their plan.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.training_plan import TrainingPlan


class TrainingTask(Base):
    __tablename__ = "training_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    training_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("training_plans.id"), nullable=False
    )

    day_number: Mapped[int] = mapped_column(Integer, nullable=False)          # 1–7
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)       # within day

    # Task content
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    exercise_type: Mapped[str] = mapped_column(String, nullable=False)         # e.g. "mirror_practice", "recording", "writing"
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    # Completion tracking
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    training_plan: Mapped["TrainingPlan"] = relationship(
        "TrainingPlan", back_populates="tasks", lazy="raise"
    )

    # ── Indexes ────────────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_training_tasks_plan_id_day_order", "training_plan_id", "day_number", "sequence_order"),
    )

    def __repr__(self) -> str:
        return f"<TrainingTask id={self.id} day={self.day_number} completed={self.is_completed}>"
