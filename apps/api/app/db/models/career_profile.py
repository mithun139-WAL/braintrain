import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User


class CareerProfile(Base):
    __tablename__ = "career_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    
    current_role: Mapped[str] = mapped_column(String(256), nullable=False)
    target_role: Mapped[str] = mapped_column(String(256), nullable=False)
    
    resume_filename: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    resume_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    linkedin_filename: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    linkedin_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    naukri_filename: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    naukri_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    extracted_data: Mapped[dict] = mapped_column(JSONB, default=dict, server_default='{}', nullable=False)
    analysis_result: Mapped[dict] = mapped_column(JSONB, default=dict, server_default='{}', nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="career_profiles", lazy="raise")

    __table_args__ = (
        Index("ix_career_profiles_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<CareerProfile id={self.id} user_id={self.user_id} current_role='{self.current_role}' target_role='{self.target_role}'>"
