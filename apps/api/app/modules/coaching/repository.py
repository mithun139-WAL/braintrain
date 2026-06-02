"""
Coaching repository — all DB queries for coaching sessions and messages.
"""
import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.coaching_message import CoachingMessage
from app.db.models.coaching_session import CoachingSession


async def create_coaching_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    focus_area: str,
    interview_session_id: Optional[uuid.UUID] = None,
) -> CoachingSession:
    session = CoachingSession(
        user_id=user_id,
        focus_area=focus_area,
        interview_session_id=interview_session_id,
        status="ACTIVE",
    )
    db.add(session)
    await db.flush()
    return session


async def get_coaching_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Optional[CoachingSession]:
    result = await db.execute(
        select(CoachingSession)
        .where(
            CoachingSession.id == session_id,
            CoachingSession.user_id == user_id,
        )
        .options(selectinload(CoachingSession.messages))
    )
    return result.scalar_one_or_none()


async def list_coaching_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
) -> Tuple[List[CoachingSession], int]:
    offset = (page - 1) * limit

    count_result = await db.execute(
        select(func.count()).where(CoachingSession.user_id == user_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(CoachingSession)
        .where(CoachingSession.user_id == user_id)
        .options(selectinload(CoachingSession.messages))
        .order_by(CoachingSession.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all(), total


async def create_message(
    db: AsyncSession,
    coaching_session_id: uuid.UUID,
    role: str,
    content: str,
) -> CoachingMessage:
    message = CoachingMessage(
        coaching_session_id=coaching_session_id,
        role=role,
        content=content,
    )
    db.add(message)
    await db.flush()
    return message


async def get_messages(
    db: AsyncSession,
    coaching_session_id: uuid.UUID,
) -> List[CoachingMessage]:
    result = await db.execute(
        select(CoachingMessage)
        .where(CoachingMessage.coaching_session_id == coaching_session_id)
        .order_by(CoachingMessage.created_at)
    )
    return result.scalars().all()


async def end_coaching_session(
    db: AsyncSession,
    session: CoachingSession,
) -> CoachingSession:
    from datetime import datetime, timezone
    session.status = "ENDED"
    session.ended_at = datetime.now(timezone.utc)
    await db.flush()
    return session
