"""
Sessions service — business logic for session lifecycle management.

Key invariants:
  1. Session creation checks monthly usage limit before proceeding
  2. completeSession atomically creates EvaluationJob(PENDING) in the same
     transaction (ensures no session is ever completed without a queued job)
  3. State machine enforced here: CREATED → ACTIVE → COMPLETED
  4. Usage counter increment is fire-and-forget (failure doesn't block creation)
"""
import asyncio
import logging
import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.modules.sessions import repository as repo
from app.modules.sessions.schemas import (
    CreateSessionRequest,
    PaginationMeta,
    QuestionSummaryResponse,
    ResponseSummaryResponse,
    SessionListItemResponse,
    SessionListResponse,
    SessionResponse,
    SessionStatusResponse,
    TopicRefResponse,
    EvaluationScoreRefResponse,
)
from app.usage import service as usage_svc

logger = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _build_session_response(session) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        topic_id=session.topic_id,
        topic_name=session.topic.name if session.topic else None,
        interview_mode=session.interview_mode,
        interview_type=session.interview_type,
        difficulty=session.difficulty,
        adaptive=session.adaptive,
        duration_minutes=session.duration_minutes,
        is_voice=session.is_voice,
        personality_config=session.personality_config,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        created_at=session.created_at,
        updated_at=session.updated_at,
        topic=(
            TopicRefResponse(id=session.topic.id, name=session.topic.name)
            if session.topic
            else None
        ),
        questions=[
            QuestionSummaryResponse(
                id=q.id,
                content=q.content,
                difficulty=q.difficulty,
                sequence_order=q.sequence_order,
                generated_at=q.generated_at,
                responses=[
                    ResponseSummaryResponse(
                        id=r.id,
                        question_id=r.question_id,
                        answer_text=r.answer_text,
                        audio_url=r.audio_url,
                        response_time_ms=r.response_time_ms,
                        thinking_time_ms=r.thinking_time_ms,
                        overall_score=r.overall_score,
                        created_at=r.created_at,
                    )
                    for r in q.responses
                ],
            )
            for q in sorted(session.questions, key=lambda q: q.sequence_order)
            if q.deleted_at is None
        ],
    )


# ── Public service methods ─────────────────────────────────────────────────────


async def create_session(
    db: AsyncSession, dto: CreateSessionRequest, user_id: uuid.UUID
) -> SessionResponse:
    # Check plan type to enforce constraints
    from sqlalchemy import select
    from app.db.models.user import User
    user_res = await db.execute(select(User.plan_type).where(User.id == user_id))
    user_plan = user_res.scalar_one_or_none() or "FREE"

    if user_plan.upper() == "FREE":
        if dto.interview_mode != "ONE_ON_ONE_AI":
            raise BadRequestException("Only 1:1 AI Interview format is available on the Free Plan.")
        if dto.duration_minutes > 15:
            raise BadRequestException("Maximum session duration is 15 minutes on the Free Plan.")

    # 0. Check usage limit
    await usage_svc.check_session_limit(db, user_id, is_voice=dto.is_voice)

    # 1. Validate topic
    from app.db.models.topic import Topic

    result = await db.execute(
        select(Topic).where(Topic.id == dto.topic_id, Topic.deleted_at.is_(None))
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise NotFoundException("Topic not found")

    if not topic.is_global and topic.created_by_user_id != user_id:
        raise ForbiddenException("You do not have access to this topic")

    # 2. Create session
    session = await repo.create_session(
        db,
        user_id=user_id,
        topic_id=dto.topic_id,
        interview_mode=dto.interview_mode,
        interview_type=dto.interview_type,
        difficulty=dto.difficulty,
        adaptive=dto.adaptive,
        duration_minutes=dto.duration_minutes,
        is_voice=dto.is_voice,
        personality_config=dto.personality_config,
    )
    await db.commit()
    logger.info("Session %s CREATED for user %s", session.id, user_id)

    # 3. Fire-and-forget usage increment (failure does not affect the response)
    async def _increment():
        from app.db.session import SessionLocal

        async with SessionLocal() as inc_db:
            await usage_svc.increment_session_count(inc_db, user_id)

    asyncio.create_task(_increment())

    # Reload with relationships for response
    session = await repo.get_session_by_id(db, session.id, user_id)
    return _build_session_response(session)


async def get_session_by_id(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> SessionResponse:
    session = await repo.get_session_by_id(db, session_id, user_id)
    if not session:
        raise NotFoundException("Session not found")
    return _build_session_response(session)


async def start_session(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> SessionResponse:
    session = await repo.get_session_by_id(db, session_id, user_id)
    if not session:
        raise NotFoundException("Session not found")

    if session.status != "CREATED":
        raise BadRequestException("Session is not in CREATED state. Cannot start.")

    from datetime import datetime, timezone
    session = await repo.update_session_status(
        db, session, "ACTIVE", started_at=datetime.now(timezone.utc)
    )
    await db.commit()

    # Reload with relationships
    session = await repo.get_session_by_id(db, session_id, user_id)
    return _build_session_response(session)


async def complete_session(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> SessionResponse:
    session = await repo.get_session_by_id(db, session_id, user_id)
    if not session:
        raise NotFoundException("Session not found")

    if session.status != "ACTIVE":
        raise BadRequestException("Only ACTIVE sessions can be completed.")

    # Atomically: COMPLETED + create EvaluationJob(PENDING) in one transaction
    from datetime import datetime, timezone
    await repo.update_session_status(
        db, session, "COMPLETED", ended_at=datetime.now(timezone.utc)
    )
    await repo.create_evaluation_job(db, session_id)
    await db.commit()
    logger.info("Session %s COMPLETED — EvaluationJob enqueued.", session_id)

    # Reload
    session = await repo.get_session_by_id(db, session_id, user_id)
    return _build_session_response(session)


async def get_session_status(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> SessionStatusResponse:
    session = await repo.get_session_with_status(db, session_id, user_id)
    if not session:
        raise NotFoundException("Session not found.")

    eval_job = session.evaluation_job
    evaluation = session.evaluation

    return SessionStatusResponse(
        session_id=session.id,
        session_status=session.status,
        evaluation_job_status=eval_job.status if eval_job else None,
        evaluation_attempts=eval_job.attempts if eval_job else 0,
        last_error=eval_job.last_error if eval_job else None,
        overall_score=evaluation.overall_score if evaluation else None,
    )


async def list_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
    status: str | None = None,
    topic_id: uuid.UUID | None = None,
    page: int = 1,
    limit: int = 20,
) -> SessionListResponse:
    limit = min(limit, 100)  # cap at 100
    sessions, total = await repo.list_sessions(
        db,
        user_id,
        status=status,
        topic_id=topic_id,
        page=page,
        limit=limit,
    )

    items = []
    for s in sessions:
        question_count = await repo.count_questions(db, s.id)
        items.append(
            SessionListItemResponse(
                id=s.id,
                user_id=s.user_id,
                topic_id=s.topic_id,
                interview_mode=s.interview_mode,
                interview_type=s.interview_type,
                difficulty=s.difficulty,
                adaptive=s.adaptive,
                duration_minutes=s.duration_minutes,
                is_voice=s.is_voice,
                status=s.status,
                started_at=s.started_at,
                ended_at=s.ended_at,
                created_at=s.created_at,
                updated_at=s.updated_at,
                topic=(
                    TopicRefResponse(id=s.topic.id, name=s.topic.name) if s.topic else None
                ),
                evaluation=(
                    EvaluationScoreRefResponse(overall_score=s.evaluation.overall_score)
                    if s.evaluation
                    else None
                ),
                question_count=question_count,
            )
        )

    total_pages = math.ceil(total / limit) if limit else 1

    return SessionListResponse(
        data=items,
        meta=PaginationMeta(total=total, page=page, limit=limit, total_pages=total_pages),
    )
