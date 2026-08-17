"""
Responses repository — DB read/write for response instances.

Rules:
  - No business logic, no HTTP, no imports from other feature modules
"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.interview_session import InterviewSession
from app.db.models.question_instance import QuestionInstance
from app.db.models.response_instance import ResponseInstance


async def get_question_with_session(
    db: AsyncSession, question_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[QuestionInstance]:
    """
    Load a question along with its parent session.
    Validates both question and session ownership belong to user_id.
    """
    result = await db.execute(
        select(QuestionInstance)
        .where(
            QuestionInstance.id == question_id,
            QuestionInstance.deleted_at.is_(None),
        )
        .options(selectinload(QuestionInstance.session))
    )
    question = result.scalar_one_or_none()
    if not question:
        return None

    # Ownership check: session must belong to this user and not be deleted
    if question.session.user_id != user_id or question.session.deleted_at is not None:
        return None

    return question


async def get_existing_responses(
    db: AsyncSession, question_id: uuid.UUID
) -> list[ResponseInstance]:
    """Return existing non-deleted responses for this question."""
    result = await db.execute(
        select(ResponseInstance).where(
            ResponseInstance.question_id == question_id,
            ResponseInstance.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def create_response(
    db: AsyncSession,
    *,
    question_id: uuid.UUID,
    session_id: uuid.UUID,
    answer_text: Optional[str],
    audio_url: Optional[str],
    response_time_ms: int,
    thinking_time_ms: int,
    answer_length: int,
    audio_processing_status: str,
    is_followup: bool = False,
) -> ResponseInstance:
    response = ResponseInstance(
        question_id=question_id,
        session_id=session_id,
        answer_text=answer_text,
        audio_url=audio_url,
        response_time_ms=response_time_ms,
        thinking_time_ms=thinking_time_ms,
        answer_length=answer_length,
        audio_processing_status=audio_processing_status,
        is_followup=is_followup,
    )
    db.add(response)
    await db.flush()
    return response


async def get_response_by_id(
    db: AsyncSession, response_id: uuid.UUID
) -> Optional[ResponseInstance]:
    """Load a response by its primary key (no ownership check — caller must validate)."""
    result = await db.execute(
        select(ResponseInstance).where(
            ResponseInstance.id == response_id,
            ResponseInstance.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()
