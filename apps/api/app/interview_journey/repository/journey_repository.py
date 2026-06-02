import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.interview_journey import InterviewJourney


async def create_journey(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    role_title: str,
    job_description: str,
    resume_text: str,
    company_name: str | None = None,
) -> InterviewJourney:
    journey = InterviewJourney(
        user_id=user_id,
        role_title=role_title,
        job_description=job_description,
        resume_text=resume_text,
        company_name=company_name,
        status="CREATED",
    )
    db.add(journey)
    await db.flush()
    return journey


async def get_journey_by_id(
    db: AsyncSession,
    journey_id: uuid.UUID,
    user_id: uuid.UUID,
) -> InterviewJourney | None:
    result = await db.execute(
        select(InterviewJourney)
        .where(
            InterviewJourney.id == journey_id,
            InterviewJourney.user_id == user_id,
        )
        .options(selectinload(InterviewJourney.sessions))
    )
    return result.scalar_one_or_none()


async def get_journeys_by_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[InterviewJourney], int]:
    from sqlalchemy import func

    base_where = [InterviewJourney.user_id == user_id]

    count_result = await db.execute(
        select(func.count(InterviewJourney.id)).where(*base_where)
    )
    total = count_result.scalar_one()

    offset = (page - 1) * limit
    data_result = await db.execute(
        select(InterviewJourney)
        .where(*base_where)
        .options(selectinload(InterviewJourney.sessions))
        .order_by(InterviewJourney.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    journeys = list(data_result.scalars().all())
    return journeys, total


async def update_journey(
    db: AsyncSession,
    journey: InterviewJourney,
    **kwargs,
) -> InterviewJourney:
    for key, value in kwargs.items():
        setattr(journey, key, value)
    await db.flush()
    return journey


async def update_generated_plan(
    db: AsyncSession,
    journey: InterviewJourney,
    generated_plan: dict,
) -> InterviewJourney:
    journey.generated_plan = generated_plan
    await db.flush()
    return journey


async def delete_journey(
    db: AsyncSession,
    journey: InterviewJourney,
) -> None:
    await db.delete(journey)
    await db.flush()

