"""
Coaching service — business logic for AI coaching sessions.

Flow:
  1. User creates a coaching session (optionally linked to an interview session)
  2. User sends a message → backend appends user message, calls AI, appends assistant reply
  3. User ends the session

The AI provider is resolved via the factory (LangChain/OpenAI for PRO, Stub for FREE).
"""
import uuid
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_coach_provider
from app.core.exceptions import ForbiddenException, NotFoundException
from app.modules.coaching import repository as repo
from app.modules.coaching.schemas import (
    CoachingMessageResponse,
    CoachingSessionListResponse,
    CoachingSessionResponse,
    CreateCoachingSessionRequest,
    SendMessageResponse,
)

logger = logging.getLogger(__name__)

VALID_FOCUS_AREAS = {"confidence", "clarity", "technical", "general"}

# Map frontend focus area values that differ from the internal ones
_FOCUS_AREA_ALIASES: dict[str, str] = {
    "technical_explanation": "technical",
}


# ── Helpers ────────────────────────────────────────────────────────────────────


def _build_session_response(session) -> CoachingSessionResponse:
    msg_responses = [
        CoachingMessageResponse(
            id=m.id,
            coaching_session_id=m.coaching_session_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
        )
        for m in session.messages
    ]
    return CoachingSessionResponse(
        id=session.id,
        user_id=session.user_id,
        interview_session_id=session.interview_session_id,
        focus_area=session.focus_area,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=msg_responses,
        message_count=len(msg_responses),
    )


def _build_message_response(message) -> CoachingMessageResponse:
    return CoachingMessageResponse(
        id=message.id,
        coaching_session_id=message.coaching_session_id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
    )


# ── Public service methods ─────────────────────────────────────────────────────


async def create_session(
    db: AsyncSession,
    dto: CreateCoachingSessionRequest,
    user_id: uuid.UUID,
) -> CoachingSessionResponse:
    focus_area = _FOCUS_AREA_ALIASES.get(dto.focus_area, dto.focus_area)
    focus_area = focus_area if focus_area in VALID_FOCUS_AREAS else "general"

    # Validate interview_session_id belongs to user if provided
    if dto.interview_session_id:
        from sqlalchemy import select
        from app.db.models.interview_session import InterviewSession
        result = await db.execute(
            select(InterviewSession).where(
                InterviewSession.id == dto.interview_session_id,
                InterviewSession.user_id == user_id,
            )
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Interview session not found")

    session = await repo.create_coaching_session(
        db,
        user_id=user_id,
        focus_area=focus_area,
        interview_session_id=dto.interview_session_id,
    )

    # Generate an opening greeting from the AI
    coach = get_coach_provider()
    try:
        opening = await coach.get_response([], focus_area=focus_area)
    except Exception as exc:
        logger.warning("Coach provider failed during session open (%s); using stub fallback", exc)
        from app.ai.providers.stub_coach import StubCoachProvider
        opening = await StubCoachProvider().get_response([], focus_area=focus_area)
    await repo.create_message(db, session.id, "assistant", opening)

    await db.commit()

    # Reload with messages
    session = await repo.get_coaching_session(db, session.id, user_id)
    logger.info("CoachingSession %s created for user %s", session.id, user_id)
    return _build_session_response(session)


async def get_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
) -> CoachingSessionResponse:
    session = await repo.get_coaching_session(db, session_id, user_id)
    if not session:
        raise NotFoundException("Coaching session not found")
    return _build_session_response(session)


async def list_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
) -> CoachingSessionListResponse:
    limit = min(limit, 50)
    sessions, total = await repo.list_coaching_sessions(db, user_id, page=page, limit=limit)
    return CoachingSessionListResponse(
        data=[_build_session_response(s) for s in sessions],
        total=total,
    )


async def send_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    content: str,
) -> SendMessageResponse:
    session = await repo.get_coaching_session(db, session_id, user_id)
    if not session:
        raise NotFoundException("Coaching session not found")
    if session.status != "ACTIVE":
        from app.core.exceptions import BadRequestException
        raise BadRequestException("Coaching session has ended")

    # Build conversation history for the AI
    history = [{"role": m.role, "content": m.content} for m in session.messages]

    # Append user message
    user_msg = await repo.create_message(db, session_id, "user", content)
    history.append({"role": "user", "content": content})

    # Optionally pull evaluation context
    context_summary: Optional[str] = None
    if session.interview_session_id:
        from sqlalchemy import select
        from app.db.models.evaluation_report import EvaluationReport
        result = await db.execute(
            select(EvaluationReport).where(
                EvaluationReport.session_id == session.interview_session_id
            )
        )
        report = result.scalar_one_or_none()
        if report:
            context_summary = report.feedback_summary

    # Get AI response
    coach = get_coach_provider()
    try:
        ai_content = await coach.get_response(
            history,
            focus_area=session.focus_area,
            context_summary=context_summary,
        )
    except Exception as exc:
        logger.warning("Coach provider failed during send_message (%s); using stub fallback", exc)
        from app.ai.providers.stub_coach import StubCoachProvider
        ai_content = await StubCoachProvider().get_response(
            history,
            focus_area=session.focus_area,
            context_summary=context_summary,
        )

    assistant_msg = await repo.create_message(db, session_id, "assistant", ai_content)

    await db.commit()

    return SendMessageResponse(
        user_message=_build_message_response(user_msg),
        assistant_message=_build_message_response(assistant_msg),
    )


async def end_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
) -> CoachingSessionResponse:
    session = await repo.get_coaching_session(db, session_id, user_id)
    if not session:
        raise NotFoundException("Coaching session not found")

    session = await repo.end_coaching_session(db, session)
    await db.commit()

    session = await repo.get_coaching_session(db, session_id, user_id)
    return _build_session_response(session)
