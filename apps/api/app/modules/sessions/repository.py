"""
Sessions repository — all DB read/write operations for the sessions module.

Rules:
  - No business logic, no HTTP objects, no imports from other feature modules
  - selectinload used for all nested relationships
  - completeSession transaction: atomically update session + create EvaluationJob
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.evaluation_job import EvaluationJob
from app.db.models.evaluation_report import EvaluationReport
from app.db.models.interview_session import InterviewSession
from app.db.models.question_instance import QuestionInstance
from app.db.models.response_instance import ResponseInstance
from app.db.models.topic import Topic


# ── Helpers ────────────────────────────────────────────────────────────────────


def _full_session_options():
    """Eagerly load topic + questions + each question's responses."""
    return [
        selectinload(InterviewSession.topic),
        selectinload(InterviewSession.questions).selectinload(
            QuestionInstance.responses
        ),
    ]


def _list_session_options():
    """Eagerly load topic + evaluation (for list view)."""
    return [
        selectinload(InterviewSession.topic),
        selectinload(InterviewSession.evaluation),
    ]


# ── Session queries ────────────────────────────────────────────────────────────


async def get_session_by_id(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[InterviewSession]:
    """Load a session with full detail (questions + responses)."""
    result = await db.execute(
        select(InterviewSession)
        .where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
            InterviewSession.deleted_at.is_(None),
        )
        .options(*_full_session_options())
    )
    return result.scalar_one_or_none()


async def get_session_with_status(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[InterviewSession]:
    """Load a session with evaluation_job + evaluation (for status polling)."""
    result = await db.execute(
        select(InterviewSession)
        .where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
            InterviewSession.deleted_at.is_(None),
        )
        .options(
            selectinload(InterviewSession.evaluation_job),
            selectinload(InterviewSession.evaluation),
        )
    )
    return result.scalar_one_or_none()


async def list_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
    status: Optional[str] = None,
    topic_id: Optional[uuid.UUID] = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[InterviewSession], int]:
    """Return paginated sessions and total count."""
    base_where = [
        InterviewSession.user_id == user_id,
        InterviewSession.deleted_at.is_(None),
    ]
    if status:
        base_where.append(InterviewSession.status == status)
    if topic_id:
        base_where.append(InterviewSession.topic_id == topic_id)

    # Count query
    count_result = await db.execute(
        select(func.count(InterviewSession.id)).where(*base_where)
    )
    total: int = count_result.scalar_one()

    # Data query
    offset = (page - 1) * limit
    data_result = await db.execute(
        select(InterviewSession)
        .where(*base_where)
        .options(*_list_session_options())
        .order_by(InterviewSession.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    sessions = list(data_result.scalars().all())
    return sessions, total


async def count_questions(db: AsyncSession, session_id: uuid.UUID) -> int:
    """Count non-deleted questions for a session."""
    result = await db.execute(
        select(func.count(QuestionInstance.id)).where(
            QuestionInstance.session_id == session_id,
            QuestionInstance.deleted_at.is_(None),
        )
    )
    return result.scalar_one()


async def create_session(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    topic_id: uuid.UUID,
    interview_mode: Optional[str],
    interview_type: Optional[str],
    difficulty: str,
    adaptive: bool,
    duration_minutes: int,
    personality_config: Optional[dict] = None,
) -> InterviewSession:
    session = InterviewSession(
        user_id=user_id,
        topic_id=topic_id,
        interview_mode=interview_mode,
        interview_type=interview_type,
        difficulty=difficulty,
        adaptive=adaptive,
        duration_minutes=duration_minutes,
        personality_config=personality_config,
        status="CREATED",
    )
    db.add(session)
    await db.flush()
    return session


async def update_session_status(
    db: AsyncSession,
    session: InterviewSession,
    status: str,
    *,
    started_at: Optional[datetime] = None,
    ended_at: Optional[datetime] = None,
) -> InterviewSession:
    session.status = status
    if started_at is not None:
        session.started_at = started_at
    if ended_at is not None:
        session.ended_at = ended_at
    await db.flush()
    return session


async def create_evaluation_job(
    db: AsyncSession, session_id: uuid.UUID
) -> EvaluationJob:
    job = EvaluationJob(session_id=session_id, status="PENDING")
    db.add(job)
    await db.flush()
    return job
