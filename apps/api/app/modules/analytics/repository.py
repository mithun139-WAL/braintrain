"""
Analytics repository — read-only DB queries for the analytics module.

Two queries:
  1. get_sessions_with_evaluations — full history, ordered ASC for trend charts
  2. get_last_two_analyzed_sessions — last 2 ANALYZED sessions for progression delta

Both use selectinload for topic + evaluation; no N+1 loading.
No writes: analytics is a pure read path.
"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.evaluation_report import EvaluationReport
from app.db.models.interview_session import InterviewSession
from app.db.models.topic import Topic


async def get_sessions_with_evaluations(
    db: AsyncSession, user_id: uuid.UUID
) -> list[InterviewSession]:
    """
    All non-deleted sessions for the user, ordered by created_at ASC.
    Eagerly loads topic (for name) and evaluation (for scores).
    Used to build the trend array and per-topic breakdown.
    """
    result = await db.execute(
        select(InterviewSession)
        .where(
            InterviewSession.user_id == user_id,
            InterviewSession.deleted_at.is_(None),
        )
        .options(
            selectinload(InterviewSession.topic),
            selectinload(InterviewSession.evaluation),
        )
        .order_by(InterviewSession.created_at.asc())
    )
    return list(result.scalars().all())


async def get_last_two_analyzed_sessions(
    db: AsyncSession, user_id: uuid.UUID
) -> list[InterviewSession]:
    """
    Last 2 ANALYZED sessions for the user, ordered by created_at DESC.
    Used by the progression delta endpoint (dopamine-loop banner).
    """
    result = await db.execute(
        select(InterviewSession)
        .where(
            InterviewSession.user_id == user_id,
            InterviewSession.status == "ANALYZED",
            InterviewSession.deleted_at.is_(None),
        )
        .options(
            selectinload(InterviewSession.evaluation),
        )
        .order_by(InterviewSession.created_at.desc())
        .limit(2)
    )
    return list(result.scalars().all())


async def get_topic_sessions_with_evaluations(
    db: AsyncSession,
    user_id: uuid.UUID,
    topic_id: uuid.UUID,
) -> list[InterviewSession]:
    result = await db.execute(
        select(InterviewSession)
        .where(
            InterviewSession.user_id == user_id,
            InterviewSession.topic_id == topic_id,
            InterviewSession.deleted_at.is_(None),
        )
        .options(
            selectinload(InterviewSession.evaluation),
        )
        .order_by(InterviewSession.created_at.asc())
    )
    return list(result.scalars().all())
