"""
Usage service — enforces SaaS plan limits and monthly reset.

Plan limits are read from Settings (free_monthly_session_limit, pro_monthly_session_limit)
to keep them out of source code and overridable via env vars.

Monthly reset is a standalone coroutine called by the APScheduler job in Phase 8.
"""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import case, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ForbiddenException
from app.db.models.user import User
from app.db.models.interview_session import InterviewSession

logger = logging.getLogger(__name__)


def _get_limit(plan_type: str) -> int:
    settings = get_settings()
    if plan_type == "PRO":
        return settings.pro_monthly_session_limit
    return settings.free_monthly_session_limit


def get_evaluation_credit_limit(plan_type: str) -> int:
    settings = get_settings()
    if plan_type == "PRO":
        return settings.pro_monthly_evaluation_credit_limit
    return 0


async def get_usage_counts(db: AsyncSession, user_id: uuid.UUID, usage_period_start: datetime) -> tuple[int, int]:
    """Return (voice_count, chat_count) since usage_period_start."""
    voice_query = select(func.count(InterviewSession.id)).where(
        InterviewSession.user_id == user_id,
        InterviewSession.created_at >= usage_period_start,
        InterviewSession.is_voice == True,
        InterviewSession.deleted_at.is_(None),
    )
    voice_res = await db.execute(voice_query)
    voice_count = voice_res.scalar() or 0

    chat_query = select(func.count(InterviewSession.id)).where(
        InterviewSession.user_id == user_id,
        InterviewSession.created_at >= usage_period_start,
        InterviewSession.is_voice == False,
        InterviewSession.deleted_at.is_(None),
    )
    chat_res = await db.execute(chat_query)
    chat_count = chat_res.scalar() or 0

    return voice_count, chat_count


async def check_session_limit(db: AsyncSession, user_id: uuid.UUID, is_voice: bool = True) -> None:
    """
    Raise 403 ForbiddenException if the user has reached their monthly session limit.
    Called before creating a new session.
    """
    result = await db.execute(
        select(User.plan_type, User.monthly_session_count, User.usage_period_start).where(User.id == user_id)
    )
    row = result.one_or_none()
    if not row:
        return  # User not found — let the session service handle it

    plan_type, monthly_session_count, usage_period_start = row
    plan = (plan_type or "FREE").upper()
    settings = get_settings()

    if plan == "PRO":
        limit = settings.pro_monthly_session_limit
        if monthly_session_count >= limit:
            raise ForbiddenException(
                f"Monthly session limit reached ({limit} sessions on PRO plan)."
            )
    else:
        # FREE plan
        voice_count, chat_count = await get_usage_counts(db, user_id, usage_period_start)
        if is_voice:
            limit = 1
            if voice_count >= limit:
                raise ForbiddenException(
                    "Monthly voice session limit reached (1 session on FREE plan). "
                    "Upgrade to PRO for unlimited voice sessions."
                )
        else:
            limit = 3
            if chat_count >= limit:
                raise ForbiddenException(
                    "Monthly chat session limit reached (3 sessions on FREE plan). "
                    "Upgrade to PRO for unlimited chat sessions."
                )


async def increment_session_count(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Increment monthly_session_count. Called fire-and-forget after session creation."""
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(monthly_session_count=User.monthly_session_count + 1)
    )
    await db.commit()


async def consume_evaluation_credit(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(
        update(User)
        .where(User.id == user_id, User.monthly_evaluation_credits > 0)
        .values(monthly_evaluation_credits=User.monthly_evaluation_credits - 1)
    )
    await db.flush()


async def get_user_usage(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Return current usage info for a user (for dashboard display)."""
    result = await db.execute(
        select(
            User.plan_type,
            User.monthly_session_count,
            User.monthly_evaluation_credits,
            User.usage_period_start,
        ).where(User.id == user_id)
    )
    row = result.one_or_none()
    if not row:
        return {}

    plan_type, monthly_session_count, monthly_evaluation_credits, usage_period_start = row
    plan = (plan_type or "FREE").upper()
    session_limit = _get_limit(plan)
    evaluation_credit_limit = get_evaluation_credit_limit(plan)

    voice_count, chat_count = await get_usage_counts(db, user_id, usage_period_start)
    voice_limit = 1 if plan == "FREE" else 999999
    chat_limit = 3 if plan == "FREE" else 999999

    return {
        "plan": plan,
        "monthly_session_count": monthly_session_count,
        "session_limit": session_limit,
        "sessions_remaining": max(0, session_limit - monthly_session_count),
        "voice_session_count": voice_count,
        "chat_session_count": chat_count,
        "voice_session_limit": voice_limit,
        "chat_session_limit": chat_limit,
        "monthly_evaluation_credits": monthly_evaluation_credits,
        "evaluation_credit_limit": evaluation_credit_limit,
        "usage_period_start": usage_period_start,
    }


async def reset_monthly_usage(db: AsyncSession) -> int:
    """
    Reset all users' monthly counters. Called by the APScheduler monthly cron job.
    Returns the number of users updated.
    """
    result = await db.execute(
        update(User).values(
            monthly_session_count=0,
            monthly_evaluation_credits=case(
                (User.plan_type == "PRO", get_evaluation_credit_limit("PRO")),
                else_=0,
            ),
            usage_period_start=datetime.now(timezone.utc),
        )
    )
    await db.commit()
    count: int = result.rowcount
    logger.info("Monthly usage reset complete — %d users updated.", count)
    return count
