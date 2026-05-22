"""
Identity repository — all DB read/write operations for the identity module.

Rules:
  - No business logic (validation, bcrypt, JWT) lives here
  - Every method receives an AsyncSession and returns ORM objects or None
  - Use selectinload() when relationships must be traversed (never lazy access)
  - No module ever imports from another module's repository
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.otp_code import OtpCode
from app.db.models.skill_tag import SkillTag
from app.db.models.user import User
from app.db.models.user_skill_preference import UserSkillPreference


# ── User queries ───────────────────────────────────────────────────────────────


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_user_by_id_with_preferences(
    db: AsyncSession, user_id: uuid.UUID
) -> Optional[User]:
    """Load user + skill_preferences + each preference's skill_tag in one query."""
    result = await db.execute(
        select(User)
        .where(User.id == user_id, User.deleted_at.is_(None))
        .options(
            selectinload(User.skill_preferences).selectinload(
                UserSkillPreference.skill_tag
            )
        )
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.email == email, User.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_user_by_phone(db: AsyncSession, phone_number: str) -> Optional[User]:
    result = await db.execute(
        select(User).where(
            User.phone_number == phone_number, User.deleted_at.is_(None)
        )
    )
    return result.scalar_one_or_none()


async def get_user_by_google_id_or_email(
    db: AsyncSession, google_id: str, email: str
) -> Optional[User]:
    result = await db.execute(
        select(User).where(
            and_(
                User.deleted_at.is_(None),
            ),
            (User.google_id == google_id) | (User.email == email),
        )
    )
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    *,
    email: Optional[str] = None,
    phone_number: Optional[str] = None,
    password_hash: Optional[str] = None,
    display_name: Optional[str] = None,
    google_id: Optional[str] = None,
    avatar_url: Optional[str] = None,
    email_verified: bool = False,
    email_confirmation_token: Optional[str] = None,
    email_confirmation_expires_at: Optional[datetime] = None,
) -> User:
    user = User(
        email=email,
        phone_number=phone_number,
        password_hash=password_hash,
        display_name=display_name,
        google_id=google_id,
        avatar_url=avatar_url,
        email_verified=email_verified,
        email_confirmation_token=email_confirmation_token,
        email_confirmation_expires_at=email_confirmation_expires_at,
    )
    db.add(user)
    await db.flush()  # get generated id before commit
    return user


async def get_user_by_confirmation_token(
    db: AsyncSession, token: str
) -> Optional[User]:
    """Return an unverified user whose confirmation token matches."""
    result = await db.execute(
        select(User).where(
            User.email_confirmation_token == token,
            User.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def update_user(
    db: AsyncSession,
    user: User,
    **fields,
) -> User:
    for key, value in fields.items():
        setattr(user, key, value)
    await db.flush()
    return user


# ── OTP queries ────────────────────────────────────────────────────────────────


async def get_recent_otp(
    db: AsyncSession, identifier: str, since: datetime
) -> Optional[OtpCode]:
    """Return the most recent OTP for `identifier` created after `since`."""
    result = await db.execute(
        select(OtpCode)
        .where(OtpCode.identifier == identifier, OtpCode.created_at > since)
        .order_by(OtpCode.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_valid_otp(
    db: AsyncSession, identifier: str
) -> Optional[OtpCode]:
    """Return the latest unused, unexpired OTP for `identifier`."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(OtpCode)
        .where(
            OtpCode.identifier == identifier,
            OtpCode.is_used.is_(False),
            OtpCode.expires_at > now,
        )
        .order_by(OtpCode.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_otp(
    db: AsyncSession,
    *,
    identifier: str,
    hashed_code: str,
    expires_at: datetime,
    user_id: Optional[uuid.UUID] = None,
) -> OtpCode:
    otp = OtpCode(
        identifier=identifier,
        code=hashed_code,
        expires_at=expires_at,
        user_id=user_id,
    )
    db.add(otp)
    await db.flush()
    return otp


async def mark_otp_used(db: AsyncSession, otp: OtpCode) -> None:
    otp.is_used = True
    await db.flush()


async def increment_otp_attempts(db: AsyncSession, otp: OtpCode) -> None:
    otp.attempt_count += 1
    await db.flush()


# ── SkillTag queries ───────────────────────────────────────────────────────────


async def get_all_global_skill_tags(db: AsyncSession) -> list[SkillTag]:
    result = await db.execute(
        select(SkillTag).where(SkillTag.is_global.is_(True)).order_by(SkillTag.name)
    )
    return list(result.scalars().all())


async def get_skill_tag_by_id(
    db: AsyncSession, skill_tag_id: uuid.UUID
) -> Optional[SkillTag]:
    result = await db.execute(
        select(SkillTag).where(SkillTag.id == skill_tag_id)
    )
    return result.scalar_one_or_none()


async def get_skill_tag_by_name(
    db: AsyncSession, name: str
) -> Optional[SkillTag]:
    result = await db.execute(select(SkillTag).where(SkillTag.name == name))
    return result.scalar_one_or_none()


async def create_skill_tag(db: AsyncSession, name: str) -> SkillTag:
    tag = SkillTag(name=name, is_global=True)
    db.add(tag)
    await db.flush()
    return tag


# ── UserSkillPreference queries ────────────────────────────────────────────────


async def get_skill_preference(
    db: AsyncSession, user_id: uuid.UUID, skill_tag_id: uuid.UUID
) -> Optional[UserSkillPreference]:
    result = await db.execute(
        select(UserSkillPreference).where(
            UserSkillPreference.user_id == user_id,
            UserSkillPreference.skill_tag_id == skill_tag_id,
        )
    )
    return result.scalar_one_or_none()


async def upsert_skill_preference(
    db: AsyncSession,
    user_id: uuid.UUID,
    skill_tag_id: uuid.UUID,
    level: str,
) -> UserSkillPreference:
    """Insert or update a skill preference, then load with skill_tag populated."""
    existing = await get_skill_preference(db, user_id, skill_tag_id)
    if existing:
        existing.level = level
        await db.flush()
        pref = existing
    else:
        pref = UserSkillPreference(
            user_id=user_id, skill_tag_id=skill_tag_id, level=level
        )
        db.add(pref)
        await db.flush()

    # Reload with skill_tag eagerly so the router can serialise it
    result = await db.execute(
        select(UserSkillPreference)
        .where(UserSkillPreference.id == pref.id)
        .options(selectinload(UserSkillPreference.skill_tag))
    )
    return result.scalar_one()


async def delete_skill_preference(
    db: AsyncSession, user_id: uuid.UUID, skill_tag_id: uuid.UUID
) -> bool:
    """Delete and return True, or return False if it did not exist."""
    existing = await get_skill_preference(db, user_id, skill_tag_id)
    if not existing:
        return False
    await db.delete(existing)
    await db.flush()
    return True
