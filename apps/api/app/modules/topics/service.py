"""
Topics service — business logic for topic CRUD and analytics enrichment.

Rules:
  - No HTTP objects, no imports from other feature modules
  - Access control: users can only delete their own (non-global) topics
  - Analytics (avgScore, sessionCount, lastSessionDate) are computed in the
    repository layer via aggregate SQL — no N+1 loops here
"""
import uuid
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.modules.topics import repository as repo
from app.modules.topics.schemas import (
    CreateTopicRequest,
    MessageResponse,
    TopicRefResponse,
    TopicResponse,
)

logger = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _build_topic_response(topic, analytics: dict) -> TopicResponse:
    """Assemble a TopicResponse from an ORM Topic + analytics dict."""
    return TopicResponse(
        id=topic.id,
        name=topic.name,
        description=topic.description,
        is_global=topic.is_global,
        created_by_user_id=topic.created_by_user_id,
        parent_topic_id=topic.parent_topic_id,
        created_at=topic.created_at,
        updated_at=topic.updated_at,
        parent_topic=(
            TopicRefResponse(id=topic.parent_topic.id, name=topic.parent_topic.name)
            if topic.parent_topic
            else None
        ),
        # Filter subtopics to non-deleted only (ORM loads all; we filter here)
        subtopics=[
            TopicRefResponse(id=s.id, name=s.name)
            for s in topic.subtopics
            if s.deleted_at is None
        ],
        avg_score=analytics.get("avg_score", 0),
        last_session_date=analytics.get("last_session_date"),
        session_count=analytics.get("session_count", 0),
    )


# ── Public service methods ─────────────────────────────────────────────────────


async def list_topics(db: AsyncSession, user_id: uuid.UUID) -> list[TopicResponse]:
    topics = await repo.list_accessible_topics(db, user_id)

    if not topics:
        return []

    topic_ids = [t.id for t in topics]
    analytics_map = await repo.get_bulk_topic_analytics(db, topic_ids, user_id)

    return [_build_topic_response(t, analytics_map.get(t.id, {})) for t in topics]


async def get_topic(
    db: AsyncSession, topic_id: uuid.UUID, user_id: uuid.UUID
) -> TopicResponse:
    topic = await repo.get_topic_accessible(db, topic_id, user_id)
    if not topic:
        raise NotFoundException("Topic not found")

    analytics = await repo.get_topic_analytics(db, topic_id, user_id)
    return _build_topic_response(topic, analytics)


async def create_topic(
    db: AsyncSession, dto: CreateTopicRequest, user_id: uuid.UUID
) -> TopicResponse:
    # Validate parent topic if provided
    if dto.parent_topic_id:
        parent = await repo.get_topic_by_id(db, dto.parent_topic_id)
        if not parent:
            raise NotFoundException("Parent topic not found")

    # Duplicate name check per user
    existing = await repo.get_topic_by_name_for_user(db, dto.name, user_id)
    if existing:
        raise BadRequestException(f'You already have a topic named "{dto.name}"')

    topic = await repo.create_topic(
        db,
        name=dto.name,
        description=dto.description,
        user_id=user_id,
        parent_topic_id=dto.parent_topic_id,
    )
    await db.commit()

    # Reload with relationships
    topic = await repo.get_topic_by_id(db, topic.id)
    return _build_topic_response(topic, {"avg_score": 0, "last_session_date": None, "session_count": 0})


async def delete_topic(
    db: AsyncSession, topic_id: uuid.UUID, user_id: uuid.UUID
) -> MessageResponse:
    topic = await repo.get_topic_by_id(db, topic_id)
    if not topic:
        raise NotFoundException("Topic not found")

    if topic.is_global or topic.created_by_user_id != user_id:
        raise ForbiddenException("You do not have permission to delete this topic")

    await repo.soft_delete_topic(db, topic)
    await db.commit()
    return MessageResponse(message="Topic deleted successfully")
