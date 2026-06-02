import logging
import uuid
from datetime import datetime, timezone

import stripe
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.modules.billing import repository as repo
from app.modules.billing.schemas import (
    BillingPortalResponse,
    BillingSessionResponse,
    BillingStatusResponse,
)
from app.usage.service import get_evaluation_credit_limit

logger = logging.getLogger(__name__)
settings = get_settings()

if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key

ACTIVE_STRIPE_STATUSES = {"active", "trialing"}


def _ensure_stripe_configured() -> None:
    if not settings.stripe_secret_key or not settings.stripe_pro_price_id:
        raise BadRequestException("Billing is not configured yet")


def _is_active_subscription(status: str | None) -> bool:
    return (status or "").lower() in ACTIVE_STRIPE_STATUSES


def _stripe_value(obj, key: str):
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


async def get_billing_status(db: AsyncSession, user_id: uuid.UUID) -> BillingStatusResponse:
    user = await repo.get_user_by_id(db, user_id)
    if not user:
        raise NotFoundException("User not found")

    user = await _reconcile_user_billing(db, user)

    return BillingStatusResponse(
        configured=bool(settings.stripe_secret_key and settings.stripe_pro_price_id),
        has_active_subscription=_is_active_subscription(user.stripe_subscription_status),
        plan_type=user.plan_type,
        subscription_status=user.stripe_subscription_status,
    )


async def create_checkout_session(db: AsyncSession, user_id: uuid.UUID) -> BillingSessionResponse:
    _ensure_stripe_configured()

    user = await repo.get_user_by_id(db, user_id)
    if not user:
        raise NotFoundException("User not found")

    user = await _reconcile_user_billing(db, user)

    if user.plan_type == "PRO" and _is_active_subscription(user.stripe_subscription_status):
        raise BadRequestException("PRO subscription is already active")

    customer_id = user.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(
            email=user.email or None,
            metadata={"user_id": str(user.id)},
        )
        customer_id = customer.id
        await repo.update_user_billing(db, user, stripe_customer_id=customer_id)
        await db.commit()

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": settings.stripe_pro_price_id, "quantity": 1}],
        success_url=settings.stripe_success_url,
        cancel_url=settings.stripe_cancel_url,
        metadata={"user_id": str(user.id)},
        subscription_data={"metadata": {"user_id": str(user.id)}},
        allow_promotion_codes=True,
    )

    if not session.url:
        raise BadRequestException("Unable to create checkout session")

    return BillingSessionResponse(url=session.url)


async def create_billing_portal_session(db: AsyncSession, user_id: uuid.UUID) -> BillingPortalResponse:
    _ensure_stripe_configured()

    user = await repo.get_user_by_id(db, user_id)
    if not user:
        raise NotFoundException("User not found")

    user = await _reconcile_user_billing(db, user)

    if not user.stripe_customer_id:
        raise BadRequestException("No billing account found for this user")

    portal_session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=settings.stripe_portal_return_url,
    )
    return BillingPortalResponse(url=portal_session.url)


async def handle_webhook(db: AsyncSession, request: Request) -> dict:
    _ensure_stripe_configured()

    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature or not settings.stripe_webhook_secret:
        raise ForbiddenException("Missing Stripe webhook signature")

    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)
    except Exception as exc:
        logger.warning("Invalid Stripe webhook payload: %s", exc)
        raise BadRequestException("Invalid Stripe webhook payload")

    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _sync_checkout_completion(db, data_object)
    elif event_type in {"customer.subscription.created", "customer.subscription.updated"}:
        await _sync_subscription(db, data_object)
    elif event_type in {"customer.subscription.deleted", "customer.subscription.paused"}:
        await _sync_subscription(db, data_object, cancelled=True)

    return {"received": True}


async def _sync_checkout_completion(db: AsyncSession, checkout_session) -> None:
    customer_id = _stripe_value(checkout_session, "customer")
    subscription_id = _stripe_value(checkout_session, "subscription")
    metadata = _stripe_value(checkout_session, "metadata") or {}
    user_id = metadata.get("user_id") if isinstance(metadata, dict) else getattr(metadata, "user_id", None)

    user = None
    if customer_id:
        user = await repo.get_user_by_stripe_customer_id(db, customer_id)
    if not user and user_id:
        user = await repo.get_user_by_id(db, uuid.UUID(user_id))

    if not user:
        logger.warning("Stripe checkout completed for unknown user | customer=%s", customer_id)
        return

    await repo.update_user_billing(
        db,
        user,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
    )
    await db.commit()

    if subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
        except Exception as exc:
            logger.warning("Unable to hydrate subscription %s after checkout: %s", subscription_id, exc)
        else:
            await _sync_subscription(db, subscription)


async def _sync_subscription(db: AsyncSession, subscription, cancelled: bool = False) -> None:
    customer_id = _stripe_value(subscription, "customer")
    subscription_id = _stripe_value(subscription, "id")
    status = _stripe_value(subscription, "status")

    if not customer_id:
        return

    user = await repo.get_user_by_stripe_customer_id(db, customer_id)
    if not user:
        logger.warning("Stripe subscription event for unknown customer %s", customer_id)
        return

    is_active = _is_active_subscription(status) and not cancelled
    plan_type = "PRO" if is_active else "FREE"
    was_active = user.plan_type == "PRO" and _is_active_subscription(user.stripe_subscription_status)

    monthly_evaluation_credits = user.monthly_evaluation_credits
    usage_period_start = user.usage_period_start

    if is_active and not was_active:
        monthly_evaluation_credits = get_evaluation_credit_limit(plan_type)
        usage_period_start = datetime.now(timezone.utc)
    elif not is_active:
        monthly_evaluation_credits = 0

    await repo.update_user_billing(
        db,
        user,
        plan_type=plan_type,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        stripe_subscription_status=status,
        monthly_evaluation_credits=monthly_evaluation_credits,
        usage_period_start=usage_period_start,
    )
    await db.commit()


async def _reconcile_user_billing(db: AsyncSession, user):
    if not settings.stripe_secret_key or not user.stripe_customer_id:
        return user

    subscription = None

    if user.stripe_subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
        except Exception as exc:
            logger.warning(
                "Unable to retrieve stored subscription %s for user %s: %s",
                user.stripe_subscription_id,
                user.id,
                exc,
            )

    if not subscription:
        try:
            subscriptions = stripe.Subscription.list(
                customer=user.stripe_customer_id,
                status="all",
                limit=10,
            )
        except Exception as exc:
            logger.warning(
                "Unable to list subscriptions for customer %s: %s",
                user.stripe_customer_id,
                exc,
            )
            return user

        items = list(getattr(subscriptions, "data", []) or [])
        active_subscription = next(
            (item for item in items if _is_active_subscription(_stripe_value(item, "status"))),
            None,
        )
        subscription = active_subscription or (items[0] if items else None)

    if subscription:
        await _sync_subscription(db, subscription)
        refreshed_user = await repo.get_user_by_id(db, user.id)
        return refreshed_user or user

    if user.plan_type != "FREE" or user.stripe_subscription_status:
        await repo.update_user_billing(
            db,
            user,
            plan_type="FREE",
            stripe_subscription_status=None,
            monthly_evaluation_credits=0,
        )
        await db.commit()

    refreshed_user = await repo.get_user_by_id(db, user.id)
    return refreshed_user or user
