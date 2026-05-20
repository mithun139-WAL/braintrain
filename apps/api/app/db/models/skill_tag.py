"""
SkillTag model — maps to Prisma `SkillTag` model.

Global skill tags are seeded via alembic seed scripts (equivalent of prisma/seed.ts).
Users cannot create their own skill tags — they only pick from the global catalog.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user_skill_preference import UserSkillPreference


class SkillTag(Base):
    __tablename__ = "skill_tags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    is_global: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    user_preferences: Mapped[List["UserSkillPreference"]] = relationship(
        "UserSkillPreference", back_populates="skill_tag", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<SkillTag id={self.id} name={self.name}>"
