"""
Question Bank repository — all DB read/write operations.

Rules:
  - No business logic, no HTTP, no imports from other feature modules
  - selectinload(topic) used for all queries that return bank items
"""
import random
import uuid
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.question_bank import QuestionBank
from app.db.models.topic import Topic


# ── Helpers ────────────────────────────────────────────────────────────────────

def _with_topic():
    return [selectinload(QuestionBank.topic)]


# ── QuestionBank queries ───────────────────────────────────────────────────────


async def get_by_id(
    db: AsyncSession, question_id: uuid.UUID
) -> Optional[QuestionBank]:
    result = await db.execute(
        select(QuestionBank)
        .where(QuestionBank.id == question_id, QuestionBank.deleted_at.is_(None))
        .options(*_with_topic())
    )
    return result.scalar_one_or_none()


async def list_questions(
    db: AsyncSession,
    topic_id: uuid.UUID,
    user_id: uuid.UUID,
    interview_type: Optional[str] = None,
    difficulty: Optional[str] = None,
) -> list[QuestionBank]:
    q = (
        select(QuestionBank)
        .where(
            QuestionBank.topic_id == topic_id,
            QuestionBank.deleted_at.is_(None),
            or_(
                QuestionBank.is_global.is_(True),
                QuestionBank.created_by_user_id == user_id,
            ),
        )
        .options(*_with_topic())
        .order_by(QuestionBank.is_global.desc(), QuestionBank.created_at.desc())
    )
    if interview_type:
        q = q.where(QuestionBank.interview_type == interview_type)
    if difficulty:
        q = q.where(QuestionBank.difficulty == difficulty)

    result = await db.execute(q)
    return list(result.scalars().all())


async def create_question(
    db: AsyncSession,
    *,
    content: str,
    topic_id: uuid.UUID,
    difficulty: str,
    interview_type: Optional[str],
    is_global: bool,
    user_id: Optional[uuid.UUID],
    source: str = "HUMAN",
) -> QuestionBank:
    item = QuestionBank(
        content=content,
        topic_id=topic_id,
        difficulty=difficulty,
        interview_type=interview_type,
        is_global=is_global,
        created_by_user_id=user_id,
        source=source,
    )
    db.add(item)
    await db.flush()
    return item


async def increment_usage(db: AsyncSession, question: QuestionBank) -> None:
    question.usage_count += 1
    await db.flush()


async def pick_random_question(
    db: AsyncSession,
    topic_id: uuid.UUID,
    interview_type: str,
    difficulty: str,
    user_id: uuid.UUID,
) -> Optional[QuestionBank]:
    """
    Return a random QuestionBank entry matching the given criteria.
    Increments usage_count on the picked item.
    Returns None if no candidates exist (caller falls back to LLM generation).
    """
    result = await db.execute(
        select(QuestionBank)
        .where(
            QuestionBank.topic_id == topic_id,
            QuestionBank.interview_type == interview_type,
            QuestionBank.difficulty == difficulty,
            QuestionBank.deleted_at.is_(None),
            or_(
                QuestionBank.is_global.is_(True),
                QuestionBank.created_by_user_id == user_id,
            ),
        )
    )
    candidates = list(result.scalars().all())
    if not candidates:
        return None

    picked = random.choice(candidates)
    await increment_usage(db, picked)
    return picked
