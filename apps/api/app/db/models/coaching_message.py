"""
CoachingMessage model — a single turn in an AI coaching conversation.

role: "user" | "assistant"
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.coaching_session import CoachingSession


class CoachingMessage(Base):
    __tablename__ = "coaching_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    coaching_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coaching_sessions.id"), nullable=False
    )

    # "user" | "assistant"
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    coaching_session: Mapped["CoachingSession"] = relationship(
        "CoachingSession", back_populates="messages", lazy="raise"
    )

    # ── Indexes ────────────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_coaching_messages_coaching_session_id_created_at", "coaching_session_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<CoachingMessage id={self.id} role={self.role}>"
