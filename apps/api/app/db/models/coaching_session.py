"""
CoachingSession model — a persistent AI coaching conversation scoped to a user.

Each session holds N CoachingMessages and optionally links to an InterviewSession
for context-aware coaching (e.g. "let's review what went wrong in your last session").
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.coaching_message import CoachingMessage
    from app.db.models.user import User


class CoachingSession(Base):
    __tablename__ = "coaching_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Optional: link to a specific interview session for context-aware coaching
    interview_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=True
    )

    # What the user wants to improve: e.g. "confidence", "clarity", "technical", "general"
    focus_area: Mapped[str] = mapped_column(String, default="general", nullable=False)

    # ACTIVE | ENDED
    status: Mapped[str] = mapped_column(String, default="ACTIVE", nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
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
    user: Mapped["User"] = relationship("User", back_populates="coaching_sessions", lazy="raise")
    messages: Mapped[List["CoachingMessage"]] = relationship(
        "CoachingMessage", back_populates="coaching_session", lazy="raise",
        order_by="CoachingMessage.created_at"
    )

    # ── Indexes ────────────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_coaching_sessions_user_id_status", "user_id", "status"),
        Index("ix_coaching_sessions_user_id_created_at", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<CoachingSession id={self.id} user_id={self.user_id} status={self.status}>"
