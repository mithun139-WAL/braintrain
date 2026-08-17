"""
Questions repository — DB read/write for question instances.

Rules:
  - No business logic, no HTTP, no imports from other feature modules
"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.interview_session import InterviewSession
from app.db.models.question_instance import QuestionInstance
from app.db.models.topic import Topic


async def get_session_for_questions(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[InterviewSession]:
    """Load a session with its topic (needed for question generation)."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(InterviewSession)
        .where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
            InterviewSession.deleted_at.is_(None),
        )
        .options(selectinload(InterviewSession.topic))
    )
    return result.scalar_one_or_none()


async def count_active_questions(
    db: AsyncSession, session_id: uuid.UUID
) -> int:
    from sqlalchemy import func

    result = await db.execute(
        select(func.count(QuestionInstance.id)).where(
            QuestionInstance.session_id == session_id,
            QuestionInstance.deleted_at.is_(None),
        )
    )
    return result.scalar_one()


async def get_question_contents(
    db: AsyncSession, session_id: uuid.UUID
) -> list[str]:
    """Return content strings for all active questions (duplicate prevention)."""
    result = await db.execute(
        select(QuestionInstance.content)
        .where(
            QuestionInstance.session_id == session_id,
            QuestionInstance.deleted_at.is_(None),
        )
        .order_by(QuestionInstance.sequence_order.asc())
    )
    return [row[0] for row in result.all()]


async def create_question(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    content: str,
    difficulty: str,
    sequence_order: int,
    reference_facts: str | None = None,
) -> QuestionInstance:
    question = QuestionInstance(
        session_id=session_id,
        content=content,
        difficulty=difficulty,
        sequence_order=sequence_order,
        reference_facts=reference_facts,
    )
    db.add(question)
    await db.flush()
    return question
