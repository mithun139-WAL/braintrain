"""
Identity service — all business logic for auth, profile, and skill preferences.

Rules:
  - Never touches HTTP (no Request/Response objects)
  - Never imports from other feature modules
  - All DB work delegated to repository functions
  - All security primitives (bcrypt, JWT, Google) imported from app.core.security
  - Raises domain exceptions from app.core.exceptions (never raw HTTPException)
"""
import logging
import math
import random
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.security import (
    create_access_token,
    hash_password,
    verify_google_access_token,
    verify_google_id_token,
    verify_password,
)
from app.db.models.user import User
from app.modules.identity import repository as repo
from app.modules.identity.providers.email import EmailProvider
from app.modules.identity.providers.sms import SmsProvider
from app.modules.identity.schemas import (
    AddSkillPreferenceRequest,
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    SkillPreferenceResponse,
    SkillTagResponse,
    UpdateProfileRequest,
    UserBasicResponse,
    UserProfileResponse,
    VerifyOtpRequest,
)

logger = logging.getLogger(__name__)

# Instantiated once at module load — providers read settings via get_settings()
_email_provider = EmailProvider()
_sms_provider = SmsProvider()

# OTP configuration
_OTP_RATE_LIMIT_SECONDS = 60
_OTP_EMAIL_EXPIRE_MINUTES = 2
_OTP_SMS_EXPIRE_MINUTES = 1
_OTP_MAX_ATTEMPTS = 3

# Email confirmation token expiry
_CONFIRMATION_EXPIRE_HOURS = 24


# ── Helpers ────────────────────────────────────────────────────────────────────


def _build_auth_response(user: User) -> AuthResponse:
    token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        phone_number=user.phone_number,
    )
    return AuthResponse(
        access_token=token,
        user=UserBasicResponse(
            id=user.id,
            email=user.email,
            phone_number=user.phone_number,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
        ),
    )


def _build_confirmation_url(token: str) -> str:
    from app.core.config import get_settings
    settings = get_settings()
    return f"{settings.frontend_url}/confirm-email?token={token}"


# ── Registration & Login ───────────────────────────────────────────────────────


async def register(db: AsyncSession, dto: RegisterRequest) -> MessageResponse:
    """
    Register a new user with email + password.
    Sends a confirmation email; does NOT issue a JWT until the email is verified.
    """
    if dto.email:
        existing = await repo.get_user_by_email(db, dto.email)
        if existing:
            raise ConflictException("Email already in use")

    if dto.phone_number:
        existing = await repo.get_user_by_phone(db, dto.phone_number)
        if existing:
            raise ConflictException("Phone number already in use")

    password_hash: Optional[str] = None
    if dto.password:
        password_hash = hash_password(dto.password)

    # Generate confirmation token (email registrations only)
    confirmation_token: Optional[str] = None
    confirmation_expires: Optional[datetime] = None
    if dto.email:
        confirmation_token = secrets.token_urlsafe(32)
        confirmation_expires = datetime.now(timezone.utc) + timedelta(
            hours=_CONFIRMATION_EXPIRE_HOURS
        )

    user = await repo.create_user(
        db,
        email=dto.email,
        phone_number=dto.phone_number,
        password_hash=password_hash,
        display_name=dto.name,
        # Phone-based registrations are auto-verified via OTP
        email_verified=dto.email is None,
        email_confirmation_token=confirmation_token,
        email_confirmation_expires_at=confirmation_expires,
    )
    await db.commit()
    await db.refresh(user)

    # Send confirmation email asynchronously
    if dto.email and confirmation_token:
        confirmation_url = _build_confirmation_url(confirmation_token)
        await _email_provider.send_confirmation(
            to_email=dto.email,
            confirmation_url=confirmation_url,
            display_name=dto.name,
        )

    return MessageResponse(
        message="Registration successful! Please check your email to confirm your account."
    )


async def confirm_email(db: AsyncSession, token: str) -> AuthResponse:
    """Verify an email confirmation token and activate the account."""
    user = await repo.get_user_by_confirmation_token(db, token)

    if not user:
        raise BadRequestException("Invalid or expired confirmation link")

    if user.email_verified:
        # Already verified — just log them in
        return _build_auth_response(user)

    now = datetime.now(timezone.utc)
    if user.email_confirmation_expires_at and user.email_confirmation_expires_at < now:
        raise BadRequestException("Confirmation link has expired. Please request a new one.")

    # Mark verified and clear the token
    await repo.update_user(
        db,
        user,
        email_verified=True,
        email_confirmation_token=None,
        email_confirmation_expires_at=None,
    )
    await db.commit()
    await db.refresh(user)

    return _build_auth_response(user)


async def resend_confirmation(db: AsyncSession, email: str) -> MessageResponse:
    """Generate a fresh confirmation token and resend the confirmation email."""
    user = await repo.get_user_by_email(db, email)

    if not user:
        # Return success to prevent user enumeration
        return MessageResponse(message="If that email exists, a confirmation link has been sent.")

    if user.email_verified:
        raise BadRequestException("Email is already verified")

    confirmation_token = secrets.token_urlsafe(32)
    confirmation_expires = datetime.now(timezone.utc) + timedelta(hours=_CONFIRMATION_EXPIRE_HOURS)

    await repo.update_user(
        db,
        user,
        email_confirmation_token=confirmation_token,
        email_confirmation_expires_at=confirmation_expires,
    )
    await db.commit()

    confirmation_url = _build_confirmation_url(confirmation_token)
    await _email_provider.send_confirmation(
        to_email=email,
        confirmation_url=confirmation_url,
        display_name=user.display_name,
    )

    return MessageResponse(message="If that email exists, a confirmation link has been sent.")


async def login(db: AsyncSession, dto: LoginRequest) -> AuthResponse:
    user: Optional[User] = None
    if dto.email:
        user = await repo.get_user_by_email(db, dto.email)
    elif dto.phone_number:
        user = await repo.get_user_by_phone(db, dto.phone_number)

    if not user or not user.password_hash:
        raise UnauthorizedException("Invalid credentials")

    if not verify_password(dto.password or "", user.password_hash):
        raise UnauthorizedException("Invalid credentials")

    # Block unverified email accounts
    if dto.email and not user.email_verified:
        raise UnauthorizedException(
            "Please verify your email before logging in. Check your inbox for a confirmation link."
        )

    return _build_auth_response(user)


# ── OTP flow ───────────────────────────────────────────────────────────────────


async def request_otp(db: AsyncSession, identifier: str) -> MessageResponse:
    # Rate-limit: 1 OTP per 60 s per identifier
    since = datetime.now(timezone.utc) - timedelta(seconds=_OTP_RATE_LIMIT_SECONDS)
    recent = await repo.get_recent_otp(db, identifier, since)
    if recent:
        raise BadRequestException("Please wait before requesting another OTP")

    # Generate 6-digit OTP
    code = str(math.floor(100000 + random.random() * 900000))

    is_email = "@" in identifier
    expire_minutes = _OTP_EMAIL_EXPIRE_MINUTES if is_email else _OTP_SMS_EXPIRE_MINUTES
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    hashed_code = hash_password(code)

    # Find existing user to link OTP (may be None for first-time signups)
    user: Optional[User] = None
    if is_email:
        user = await repo.get_user_by_email(db, identifier)
        if not user:
            raise BadRequestException("This email address is not registered.")
    else:
        user = await repo.get_user_by_phone(db, identifier)

    await repo.create_otp(
        db,
        identifier=identifier,
        hashed_code=hashed_code,
        expires_at=expires_at,
        user_id=user.id if user else None,
    )
    await db.commit()

    # Deliver OTP — fire-and-forget style; transport errors propagate up
    if is_email:
        await _email_provider.send_otp(identifier, code)
    else:
        await _sms_provider.send_otp(identifier, code)

    return MessageResponse(message="OTP sent successfully")


async def verify_otp(db: AsyncSession, dto: VerifyOtpRequest) -> AuthResponse:
    otp_record = await repo.get_valid_otp(db, dto.identifier)

    if not otp_record:
        raise BadRequestException("Invalid or expired OTP")

    # Max-attempt guard
    if otp_record.attempt_count >= _OTP_MAX_ATTEMPTS:
        raise BadRequestException("Invalid or expired OTP")

    if not verify_password(dto.code, otp_record.code):
        await repo.increment_otp_attempts(db, otp_record)
        await db.commit()
        raise BadRequestException("Invalid or expired OTP")

    await repo.mark_otp_used(db, otp_record)

    # Find or create user — OTP login auto-verifies the email
    is_email = "@" in dto.identifier
    if is_email:
        user = await repo.get_user_by_email(db, dto.identifier)
        if not user:
            raise BadRequestException("This email address is not registered.")
    else:
        user = await repo.get_user_by_phone(db, dto.identifier)

    if not user:
        user = await repo.create_user(
            db,
            email=dto.identifier if is_email else None,
            phone_number=dto.identifier if not is_email else None,
            email_verified=True,  # OTP login = verified
        )
    elif is_email and not user.email_verified:
        # Auto-verify existing unverified accounts on OTP login
        await repo.update_user(
            db, user,
            email_verified=True,
            email_confirmation_token=None,
            email_confirmation_expires_at=None,
        )

    await db.commit()
    await db.refresh(user)
    return _build_auth_response(user)


# ── Google OAuth ───────────────────────────────────────────────────────────────


async def google_login(db: AsyncSession, token: str) -> AuthResponse:
    """
    Authenticate with Google. Accepts either:
      - An OAuth access token (from @react-oauth/google useGoogleLogin hook)
      - A Google ID token (from GoogleLogin component)
    """
    try:
        # Try access token first (shorter, non-JWT format from useGoogleLogin)
        # ID tokens are JWTs and start with "eyJ"; access tokens are opaque strings
        if token.startswith("eyJ"):
            payload = verify_google_id_token(token)
        else:
            payload = await verify_google_access_token(token)
    except ValueError as exc:
        logger.warning("Google token verification failed: %s", exc)
        raise UnauthorizedException("Google authentication failed")

    email: str = payload.get("email", "")
    google_id: str = payload.get("sub", "")
    name: Optional[str] = payload.get("name")
    picture: Optional[str] = payload.get("picture")

    if not email or not google_id:
        raise UnauthorizedException("Google authentication failed")

    user = await repo.get_user_by_google_id_or_email(db, google_id, email)

    if not user:
        user = await repo.create_user(
            db,
            email=email,
            google_id=google_id,
            display_name=name,
            avatar_url=picture,
            email_verified=True,  # Google-verified email
        )
    else:
        updates: dict = {}
        if not user.google_id:
            updates["google_id"] = google_id
        if not user.display_name and name:
            updates["display_name"] = name
        if not user.avatar_url and picture:
            updates["avatar_url"] = picture
        if not user.email_verified:
            updates["email_verified"] = True
        if updates:
            user = await repo.update_user(db, user, **updates)

    await db.commit()
    await db.refresh(user)
    return _build_auth_response(user)


# ── Profile ────────────────────────────────────────────────────────────────────


async def get_profile(db: AsyncSession, user_id) -> UserProfileResponse:
    user = await repo.get_user_by_id_with_preferences(db, user_id)
    if not user:
        raise NotFoundException("User not found")
    
    from app.usage import service as usage_svc
    usage = await usage_svc.get_user_usage(db, user_id)
    user.voice_session_count = usage.get("voice_session_count", 0)
    user.chat_session_count = usage.get("chat_session_count", 0)
    user.voice_session_limit = usage.get("voice_session_limit", 0)
    user.chat_session_limit = usage.get("chat_session_limit", 0)

    return UserProfileResponse.model_validate(user)


async def update_profile(
    db: AsyncSession, user_id, dto: UpdateProfileRequest
) -> UserProfileResponse:
    user = await repo.get_user_by_id(db, user_id)
    if not user:
        raise NotFoundException("User not found")

    updates = {
        k: v
        for k, v in {
            "display_name": dto.display_name,
            "bio": dto.bio,
            "avatar_url": dto.avatar_url,
        }.items()
        if v is not None
    }

    if updates:
        user = await repo.update_user(db, user, **updates)
        await db.commit()
        await db.refresh(user)

    # Reload with skill_preferences for full profile response
    user = await repo.get_user_by_id_with_preferences(db, user_id)
    
    from app.usage import service as usage_svc
    usage = await usage_svc.get_user_usage(db, user_id)
    user.voice_session_count = usage.get("voice_session_count", 0)
    user.chat_session_count = usage.get("chat_session_count", 0)
    user.voice_session_limit = usage.get("voice_session_limit", 0)
    user.chat_session_limit = usage.get("chat_session_limit", 0)

    return UserProfileResponse.model_validate(user)


# ── Skill Tags ─────────────────────────────────────────────────────────────────


async def get_skill_tags(db: AsyncSession) -> list[SkillTagResponse]:
    tags = await repo.get_all_global_skill_tags(db)
    return [SkillTagResponse.model_validate(t) for t in tags]


async def create_skill_tag(db: AsyncSession, name: str) -> SkillTagResponse:
    existing = await repo.get_skill_tag_by_name(db, name)
    if existing:
        raise ConflictException(f'Skill tag "{name}" already exists')
    tag = await repo.create_skill_tag(db, name)
    await db.commit()
    await db.refresh(tag)
    return SkillTagResponse.model_validate(tag)


# ── Skill Preferences ──────────────────────────────────────────────────────────


async def add_skill_preference(
    db: AsyncSession, user_id, dto: AddSkillPreferenceRequest
) -> SkillPreferenceResponse:
    tag = await repo.get_skill_tag_by_id(db, dto.skill_tag_id)
    if not tag:
        raise NotFoundException("Skill tag not found")

    pref = await repo.upsert_skill_preference(
        db,
        user_id=user_id,
        skill_tag_id=dto.skill_tag_id,
        level=dto.level,
    )
    await db.commit()
    # Re-fetch with eager skill_tag after commit
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.db.models.user_skill_preference import UserSkillPreference

    result = await db.execute(
        select(UserSkillPreference)
        .where(UserSkillPreference.id == pref.id)
        .options(selectinload(UserSkillPreference.skill_tag))
    )
    pref = result.scalar_one()
    return SkillPreferenceResponse.model_validate(pref)


async def remove_skill_preference(
    db: AsyncSession, user_id, skill_tag_id
) -> MessageResponse:
    deleted = await repo.delete_skill_preference(db, user_id, skill_tag_id)
    if not deleted:
        raise NotFoundException("Skill preference not found")
    await db.commit()
    return MessageResponse(message="Skill preference removed successfully")
