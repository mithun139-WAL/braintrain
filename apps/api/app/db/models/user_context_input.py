"""
UserContextInput model — maps to Prisma `UserContextInput` model.

Stores raw user context inputs that have been parsed for intent and topic extraction.
Used for future context-aware question generation features.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User


class UserContextInput(Base):
    __tablename__ = "user_context_inputs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    raw_input: Mapped[str] = mapped_column(String, nullable=False)
    parsed_intent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    extracted_topics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    extracted_questions: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="context_inputs", lazy="raise")

    # ── Indexes ────────────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_user_context_inputs_user_id_created_at", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<UserContextInput id={self.id} user_id={self.user_id}>"
