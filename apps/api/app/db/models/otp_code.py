"""
OtpCode model — maps to Prisma `OtpCode` model.

OTP codes are bcrypt-hashed before storage (same approach as passwords).
Rate limiting: 1 OTP per 60s per identifier (enforced in IdentityService).
Email OTPs expire in 2 minutes; SMS OTPs expire in 1 minute.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User


class OtpCode(Base):
    __tablename__ = "otp_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Nullable: OTP can be requested before a user account exists (first-time registration)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )

    # email address or phone number — used as lookup key
    identifier: Mapped[str] = mapped_column(String, nullable=False)

    # bcrypt-hashed 6-digit code — never stored plaintext
    code: Mapped[str] = mapped_column(String, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    user: Mapped[Optional["User"]] = relationship("User", back_populates="otp_codes", lazy="raise")

    # ── Indexes ────────────────────────────────────────────────────────────────
    __table_args__ = (
        # Fast lookup by identifier alone (e.g., rate limit check)
        Index("ix_otp_codes_identifier", "identifier"),
        # Primary OTP validation query: find active non-expired code for identifier
        Index("ix_otp_codes_identifier_is_used_expires_at", "identifier", "is_used", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<OtpCode id={self.id} identifier={self.identifier} is_used={self.is_used}>"
