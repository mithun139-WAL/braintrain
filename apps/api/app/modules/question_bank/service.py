"""
Question Bank service — business logic for question bank CRUD and bank-first selection.

The pick_question() method is called by the questions module (Phase 6);
it is deliberately exposed at the service layer so modules stay decoupled
(questions module calls this service function, not the repository directly).
"""
import uuid
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.question_bank import repository as repo
from app.modules.question_bank.schemas import (
    CreateQuestionBankRequest,
    QuestionBankResponse,
)

logger = logging.getLogger(__name__)


async def list_questions(
    db: AsyncSession,
    topic_id: uuid.UUID,
    user_id: uuid.UUID,
    interview_type: Optional[str] = None,
    difficulty: Optional[str] = None,
) -> list[QuestionBankResponse]:
    items = await repo.list_questions(
        db,
        topic_id=topic_id,
        user_id=user_id,
        interview_type=interview_type,
        difficulty=difficulty,
    )
    return [QuestionBankResponse.model_validate(i) for i in items]


async def get_by_id(db: AsyncSession, question_id: uuid.UUID) -> QuestionBankResponse:
    item = await repo.get_by_id(db, question_id)
    if not item:
        raise NotFoundException("Question not found")
    return QuestionBankResponse.model_validate(item)


async def create_question(
    db: AsyncSession, dto: CreateQuestionBankRequest, user_id: uuid.UUID
) -> QuestionBankResponse:
    from app.db.models.topic import Topic
    from sqlalchemy import select

    # Validate topic exists
    result = await db.execute(
        select(Topic).where(Topic.id == dto.topic_id, Topic.deleted_at.is_(None))
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise NotFoundException("Topic not found")

    item = await repo.create_question(
        db,
        content=dto.content,
        topic_id=dto.topic_id,
        difficulty=dto.difficulty,
        interview_type=dto.interview_type,
        is_global=dto.is_global,
        user_id=user_id,
        source="HUMAN",
    )
    await db.commit()

    # Reload with topic relationship
    item = await repo.get_by_id(db, item.id)
    return QuestionBankResponse.model_validate(item)


async def pick_question(
    db: AsyncSession,
    topic_id: uuid.UUID,
    interview_type: str,
    difficulty: str,
    user_id: uuid.UUID,
) -> Optional[str]:
    """
    Bank-first random selection.
    Returns the question content string, or None if no candidates exist.
    Called by the questions module (Phase 6) — never called from a router directly.
    """
    item = await repo.pick_random_question(
        db,
        topic_id=topic_id,
        interview_type=interview_type,
        difficulty=difficulty,
        user_id=user_id,
    )
    if item is None:
        return None
    await db.commit()
    return item.content
