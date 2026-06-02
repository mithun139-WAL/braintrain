"""
EvaluationJob model — maps to Prisma `EvaluationJob` model.

One job per session (UniqueConstraint on session_id).
Created atomically when a session transitions to COMPLETED.

Retry / backoff logic (enforced in EvaluationJobRepository):
  attempt 1 → retry in 30s
  attempt 2 → retry in 2 minutes
  attempt 3 → FAILED permanently

Zombie recovery (EvaluationWorker, every 5 minutes):
  PROCESSING jobs stuck > 10 minutes → reset to PENDING + 30s next_retry_at

Claim query (SELECT FOR UPDATE SKIP LOCKED):
  WHERE status = PENDING AND (next_retry_at IS NULL OR next_retry_at <= NOW())
  ORDER BY created_at ASC
  This prevents double-claim in concurrent worker scenarios.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import EvaluationJobStatus

if TYPE_CHECKING:
    from app.db.models.interview_session import InterviewSession


class EvaluationJob(Base):
    __tablename__ = "evaluation_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String, default=EvaluationJobStatus.PENDING, nullable=False
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # NULL = ready immediately; set for exponential backoff
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    evaluation_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    evaluation_completed_at: Mapped[Optional[datetime]] = mapped_column(
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

    # ── Relationships ──────────────────────────────────────────────────────────
    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="evaluation_job", lazy="raise"
    )

    # ── Constraints & Indexes ─────────────────────────────────────────────────
    __table_args__ = (
        # One job per session
        UniqueConstraint("session_id", name="uq_evaluation_job_session_id"),
        # Worker claim query: PENDING jobs where next_retry_at IS NULL or <= now()
        Index(
            "ix_evaluation_jobs_status_next_retry_at_created_at",
            "status",
            "next_retry_at",
            "created_at",
        ),
        # Zombie recovery: PROCESSING jobs older than N minutes
        Index(
            "ix_evaluation_jobs_status_evaluation_started_at",
            "status",
            "evaluation_started_at",
        ),
    )

    def __repr__(self) -> str:
        return f"<EvaluationJob id={self.id} session_id={self.session_id} status={self.status} attempts={self.attempts}>"
