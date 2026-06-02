"""
Training plans repository — DB queries for training plans and tasks.
"""
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.training_plan import TrainingPlan
from app.db.models.training_task import TrainingTask


async def create_plan(
    db: AsyncSession,
    user_id: uuid.UUID,
    focus_dimension: str,
    summary: str,
    source_session_id: Optional[uuid.UUID] = None,
    duration_days: int = 7,
) -> TrainingPlan:
    today = date.today()
    from datetime import timedelta
    plan = TrainingPlan(
        user_id=user_id,
        source_session_id=source_session_id,
        status="ACTIVE",
        focus_dimension=focus_dimension,
        summary=summary,
        duration_days=duration_days,
        start_date=today,
        end_date=today + timedelta(days=duration_days - 1),
    )
    db.add(plan)
    await db.flush()
    return plan


async def create_task(
    db: AsyncSession,
    training_plan_id: uuid.UUID,
    day_number: int,
    sequence_order: int,
    title: str,
    description: str,
    exercise_type: str,
    estimated_minutes: int,
) -> TrainingTask:
    task = TrainingTask(
        training_plan_id=training_plan_id,
        day_number=day_number,
        sequence_order=sequence_order,
        title=title,
        description=description,
        exercise_type=exercise_type,
        estimated_minutes=estimated_minutes,
    )
    db.add(task)
    await db.flush()
    return task


async def get_active_plan(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> Optional[TrainingPlan]:
    result = await db.execute(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id, TrainingPlan.status == "ACTIVE")
        .options(selectinload(TrainingPlan.tasks))
        .order_by(TrainingPlan.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_plan(
    db: AsyncSession,
    plan_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Optional[TrainingPlan]:
    result = await db.execute(
        select(TrainingPlan)
        .where(TrainingPlan.id == plan_id, TrainingPlan.user_id == user_id)
        .options(selectinload(TrainingPlan.tasks))
    )
    return result.scalar_one_or_none()


async def list_plans(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    limit: int = 10,
) -> Tuple[List[TrainingPlan], int]:
    offset = (page - 1) * limit

    count_result = await db.execute(
        select(func.count()).where(TrainingPlan.user_id == user_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .options(selectinload(TrainingPlan.tasks))
        .order_by(TrainingPlan.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all(), total


async def get_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Optional[TrainingTask]:
    """Get a task, verifying ownership via the plan."""
    result = await db.execute(
        select(TrainingTask)
        .join(TrainingPlan, TrainingTask.training_plan_id == TrainingPlan.id)
        .where(TrainingTask.id == task_id, TrainingPlan.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def complete_task(
    db: AsyncSession,
    task: TrainingTask,
) -> TrainingTask:
    task.is_completed = True
    task.completed_at = datetime.now(timezone.utc)
    await db.flush()
    return task


async def supersede_active_plans(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> None:
    """Mark all ACTIVE plans for this user as SUPERSEDED before creating a new one."""
    await db.execute(
        update(TrainingPlan)
        .where(TrainingPlan.user_id == user_id, TrainingPlan.status == "ACTIVE")
        .values(status="SUPERSEDED")
    )
