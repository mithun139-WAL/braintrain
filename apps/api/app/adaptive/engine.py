"""
Adaptive difficulty engine.

Determines the next question difficulty for a session based on the
rolling average of the last 3 scored responses.

Thresholds:
  > 72  → increase difficulty
  < 55  → decrease difficulty
  else  → keep current

At least 2 scored responses are required before any transition occurs.
"""
import logging
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.interview_session import InterviewSession
from app.db.models.question_instance import QuestionInstance
from app.db.models.response_instance import ResponseInstance

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

INCREASE_ABOVE = 72
DECREASE_BELOW = 55
MIN_SCORED_RESPONSES = 2

_INCREASE_MAP = {"EASY": "MEDIUM", "MEDIUM": "HARD", "HARD": "HARD"}
_DECREASE_MAP = {"HARD": "MEDIUM", "MEDIUM": "EASY", "EASY": "EASY"}


async def determine_next_difficulty(db: AsyncSession, session_id: uuid.UUID) -> str:
    """
    Return the recommended difficulty string for the next question in `session_id`.

    Algorithm:
      1. Load session base difficulty + topic/type context
      2. Fetch last 3 questions (same user/topic/type) that have at least one response
      3. Compute rolling average of overall_score from those responses
      4. Apply threshold rules; fall back to current difficulty if insufficient data
    """
    # 1. Load session
    session_result = await db.execute(
        select(
            InterviewSession.difficulty,
            InterviewSession.interview_type,
            InterviewSession.topic_id,
            InterviewSession.user_id,
        ).where(InterviewSession.id == session_id)
    )
    session_row = session_result.one_or_none()
    if not session_row:
        raise ValueError(f"Session {session_id} not found for adaptive logic")

    base_difficulty, interview_type, topic_id, user_id = session_row

    # 2. Find session IDs that share the same user/topic/type context
    sibling_sessions_result = await db.execute(
        select(InterviewSession.id).where(
            InterviewSession.user_id == user_id,
            InterviewSession.topic_id == topic_id,
            InterviewSession.interview_type == interview_type,
            InterviewSession.deleted_at.is_(None),
        )
    )
    sibling_session_ids = [r[0] for r in sibling_sessions_result.all()]

    if not sibling_session_ids:
        return base_difficulty

    # 3. Fetch last 3 questions (across sibling sessions) that have responses
    questions_result = await db.execute(
        select(QuestionInstance)
        .where(
            QuestionInstance.session_id.in_(sibling_session_ids),
            QuestionInstance.deleted_at.is_(None),
        )
        .options(
            selectinload(QuestionInstance.responses)
        )
        .order_by(QuestionInstance.generated_at.desc())
        .limit(10)  # over-fetch, then filter to those with responses
    )
    all_questions = questions_result.scalars().all()

    # Keep only questions that have at least one non-deleted response
    recent_with_responses = [
        q for q in all_questions
        if any(r for r in q.responses if r.deleted_at is None)
    ][:3]

    if not recent_with_responses:
        return base_difficulty

    # Use the most recent question's difficulty as the current baseline
    current_difficulty = recent_with_responses[0].difficulty

    # 4. Collect overall_score from the latest response per question
    scored_values: list[float] = []
    for q in recent_with_responses:
        latest = sorted(
            [r for r in q.responses if r.deleted_at is None],
            key=lambda r: r.created_at,
            reverse=True,
        )
        if latest and latest[0].overall_score is not None:
            scored_values.append(latest[0].overall_score)

    if len(scored_values) < MIN_SCORED_RESPONSES:
        return current_difficulty

    # 5. Apply threshold rules
    avg = sum(scored_values) / len(scored_values)

    if avg > INCREASE_ABOVE:
        return _INCREASE_MAP.get(current_difficulty, current_difficulty)

    if avg < DECREASE_BELOW:
        return _DECREASE_MAP.get(current_difficulty, current_difficulty)

    return current_difficulty
