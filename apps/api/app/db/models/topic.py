"""
Topic model — maps to Prisma `Topic` model.

Self-referential hierarchy: a topic can have one parent and many subtopics.
Soft-delete pattern: deleted_at IS NULL = active topic.
Access control (enforced in service layer):
  - Global topics: readable by all, not deletable by users
  - User-owned topics: readable + deletable by owner only
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.interview_session import InterviewSession
    from app.db.models.question_bank import QuestionBank
    from app.db.models.user import User


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_global: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    # Self-referential FK for topic hierarchy
    parent_topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topics.id"),
        nullable=True,
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

    # ── Relationships ──────────────────────────────────────────────────────────
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="topics", lazy="raise"
    )
    # Self-referential: parent ↔ subtopics
    parent_topic: Mapped[Optional["Topic"]] = relationship(
        "Topic",
        remote_side="Topic.id",
        back_populates="subtopics",
        lazy="raise",
    )
    subtopics: Mapped[List["Topic"]] = relationship(
        "Topic",
        back_populates="parent_topic",
        lazy="raise",
    )
    sessions: Mapped[List["InterviewSession"]] = relationship(
        "InterviewSession", back_populates="topic", lazy="raise"
    )
    question_bank_items: Mapped[List["QuestionBank"]] = relationship(
        "QuestionBank", back_populates="topic", lazy="raise"
    )

    # ── Constraints & Indexes ─────────────────────────────────────────────────
    __table_args__ = (
        # Prevent duplicate topic names within the same scope (global vs user-owned)
        UniqueConstraint("name", "is_global", name="uq_topic_name_is_global"),
        # List topics: filter by (isGlobal OR createdByUserId) + not deleted
        Index("ix_topics_is_global_deleted_at", "is_global", "deleted_at"),
        Index("ix_topics_created_by_user_id_deleted_at", "created_by_user_id", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<Topic id={self.id} name={self.name} is_global={self.is_global}>"
