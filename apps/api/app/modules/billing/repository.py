import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    return result.scalar_one_or_none()


async def get_user_by_stripe_customer_id(db: AsyncSession, stripe_customer_id: str) -> User | None:
    result = await db.execute(
        select(User).where(User.stripe_customer_id == stripe_customer_id, User.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def update_user_billing(
    db: AsyncSession,
    user: User,
    *,
    plan_type: str | None = None,
    stripe_customer_id: str | None = None,
    stripe_subscription_id: str | None = None,
    stripe_subscription_status: str | None = None,
    monthly_evaluation_credits: int | None = None,
    usage_period_start: datetime | None = None,
) -> User:
    if plan_type is not None:
        user.plan_type = plan_type
    if stripe_customer_id is not None:
        user.stripe_customer_id = stripe_customer_id
    if stripe_subscription_id is not None:
        user.stripe_subscription_id = stripe_subscription_id
    if stripe_subscription_status is not None:
        user.stripe_subscription_status = stripe_subscription_status
    if monthly_evaluation_credits is not None:
        user.monthly_evaluation_credits = monthly_evaluation_credits
    if usage_period_start is not None:
        user.usage_period_start = usage_period_start

    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return user
