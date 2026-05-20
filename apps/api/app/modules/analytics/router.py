"""
Analytics router — GET /analytics/me + GET /analytics/progression + topic analytics.

Both routes are JWT-protected and scoped to the authenticated user.

Matches NestJS: apps/backend/src/modules/analytics/analytics.controller.ts
"""
import uuid

from fastapi import APIRouter

from app.deps import CurrentUser, DBSession
from app.modules.analytics import service
from app.modules.analytics.schemas import (
    AnalyticsResponseSchema,
    ProgressionResponseSchema,
    TopicAnalyticsResponseSchema,
)
from app.modules.analytics.topic_metrics import get_topic_analytics as get_topic_analytics_service
from app.modules.topics import repository as topics_repo
from app.core.exceptions import NotFoundException

router = APIRouter()


@router.get(
    "/me",
    response_model=AnalyticsResponseSchema,
    status_code=200,
    summary="Get full performance analytics for the authenticated user",
)
async def get_analytics(
    db: DBSession,
    current_user: CurrentUser,
) -> AnalyticsResponseSchema:
    return await service.get_analytics(db, current_user.id)


@router.get(
    "/progression",
    response_model=ProgressionResponseSchema,
    status_code=200,
    summary="Get last-vs-previous session score delta (dopamine-loop banner)",
)
async def get_progression(
    db: DBSession,
    current_user: CurrentUser,
) -> ProgressionResponseSchema:
    return await service.get_progression(db, current_user.id)


@router.get(
    "/topics/{topic_id}",
    response_model=TopicAnalyticsResponseSchema,
    status_code=200,
    summary="Get topic-level analytics for the authenticated user",
)
async def get_topic_analytics(
    topic_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> TopicAnalyticsResponseSchema:
    topic = await topics_repo.get_topic_accessible(db, topic_id, current_user.id)
    if not topic:
        raise NotFoundException("Topic not found")

    return await get_topic_analytics_service(db, current_user.id, topic_id)
