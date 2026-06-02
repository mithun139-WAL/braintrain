"""
EvaluationReport model — maps to Prisma `EvaluationReport` model.

One report per session (UniqueConstraint on session_id).
Created atomically with session.status = ANALYZED in a single transaction.

Score breakdown (from ARCHITECTURE.md §5.6):
  overall_score — server-computed weighted aggregate (NOT LLM-supplied)
  6 content dimensions — LLM-scored via GPT-4o-mini
  2 timing signals — server-computed from responseTimeMs/thinkingTimeMs

Cost tracking fields track both GPT-4o-mini and Whisper-1 costs combined.
prompt_version enables score traceability across prompt changes.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.interview_session import InterviewSession


class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id"),
        nullable=False,
    )

    # ── Aggregated PerformanceSignal dimensions (averaged across session) ──────
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    clarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    structure_score: Mapped[float] = mapped_column(Float, nullable=False)
    depth_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    communication_score: Mapped[float] = mapped_column(Float, nullable=False)
    hesitation_score: Mapped[float] = mapped_column(Float, nullable=False)
    technical_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # null for behavioral

    # ── Behavioral timing signals ──────────────────────────────────────────────
    pressure_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    thinking_depth_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Cost & model tracking (Phase 3) ───────────────────────────────────────
    prompt_version: Mapped[Optional[str]] = mapped_column(String, default="stub", nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # "gpt-4o-mini" | "stub"
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Feedback content ──────────────────────────────────────────────────────
    feedback_summary: Mapped[str] = mapped_column(String, nullable=False)
    # JSON array of improvement suggestions grouped by dimension
    # e.g. { "structure": [...], "confidence": [...], "pace": [...] }
    improvement_suggestions: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="evaluation", lazy="raise"
    )

    # ── Constraints & Indexes ─────────────────────────────────────────────────
    __table_args__ = (
        # One report per session
        UniqueConstraint("session_id", name="uq_evaluation_report_session_id"),
        # Cross-session trend sorted by date
        Index("ix_evaluation_reports_created_at", "created_at"),
        # Billing intelligence: cost per model over time
        Index("ix_evaluation_reports_model_used_created_at", "model_used", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<EvaluationReport id={self.id} session_id={self.session_id} overall_score={self.overall_score}>"
