"""
UserSkillPreference model — maps to Prisma `UserSkillPreference` model.

Junction table between User and SkillTag.
Unique constraint: one preference per (user, skill_tag) pair.
Level values: BEGINNER | INTERMEDIATE | ADVANCED
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.skill_tag import SkillTag
    from app.db.models.user import User


class UserSkillPreference(Base):
    __tablename__ = "user_skill_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skill_tags.id", ondelete="CASCADE"),
        nullable=False,
    )
    # BEGINNER | INTERMEDIATE | ADVANCED — stored as plain string (matches Prisma)
    level: Mapped[str] = mapped_column(String, nullable=False)

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
    user: Mapped["User"] = relationship("User", back_populates="skill_preferences", lazy="raise")
    skill_tag: Mapped["SkillTag"] = relationship(
        "SkillTag", back_populates="user_preferences", lazy="raise"
    )

    # ── Constraints ───────────────────────────────────────────────────────────
    __table_args__ = (
        # One preference per user per skill — enforces upsert semantics
        UniqueConstraint("user_id", "skill_tag_id", name="uq_user_skill_preference"),
    )

    def __repr__(self) -> str:
        return f"<UserSkillPreference user_id={self.user_id} skill_tag_id={self.skill_tag_id} level={self.level}>"
