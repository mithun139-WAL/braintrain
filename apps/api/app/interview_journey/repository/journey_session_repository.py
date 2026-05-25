import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.interview_journey_session import InterviewJourneySession


async def create_journey_session(
    db: AsyncSession,
    *,
    journey_id: uuid.UUID,
    round_name: str,
    round_type: str,
    interviewer_persona: dict | None = None,
    round_focus: dict | None = None,
    difficulty: str = "MEDIUM",
    order_index: int = 0,
) -> InterviewJourneySession:
    session = InterviewJourneySession(
        journey_id=journey_id,
        round_name=round_name,
        round_type=round_type,
        interviewer_persona=interviewer_persona,
        round_focus=round_focus,
        difficulty=difficulty,
        order_index=order_index,
        completed=False,
    )
    db.add(session)
    await db.flush()
    return session


async def get_journey_session_by_id(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> InterviewJourneySession | None:
    result = await db.execute(
        select(InterviewJourneySession)
        .where(InterviewJourneySession.id == session_id)
        .options(selectinload(InterviewJourneySession.journey))
    )
    return result.scalar_one_or_none()


async def get_journey_sessions(
    db: AsyncSession,
    journey_id: uuid.UUID,
) -> list[InterviewJourneySession]:
    result = await db.execute(
        select(InterviewJourneySession)
        .where(InterviewJourneySession.journey_id == journey_id)
        .order_by(InterviewJourneySession.order_index.asc())
    )
    return list(result.scalars().all())


async def update_journey_session(
    db: AsyncSession,
    session: InterviewJourneySession,
    **kwargs,
) -> InterviewJourneySession:
    for key, value in kwargs.items():
        setattr(session, key, value)
    await db.flush()
    return session


async def attach_session_id(
    db: AsyncSession,
    journey_session: InterviewJourneySession,
    session_id: uuid.UUID,
) -> InterviewJourneySession:
    journey_session.session_id = session_id
    await db.flush()
    return journey_session


async def mark_completed(
    db: AsyncSession,
    journey_session: InterviewJourneySession,
) -> InterviewJourneySession:
    journey_session.completed = True
    await db.flush()
    return journey_session


async def delete_journey_sessions(
    db: AsyncSession,
    journey_id: uuid.UUID,
) -> None:
    from sqlalchemy import delete
    await db.execute(
        delete(InterviewJourneySession).where(
            InterviewJourneySession.journey_id == journey_id
        )
    )
    await db.flush()

