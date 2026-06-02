"""
Topics repository — all DB read/write operations for the topics module.

Rules:
  - No business logic, no HTTP, no imports from other feature modules
  - selectinload() used for parent_topic and subtopics relationships
  - Avg score and last session date computed via scalar subqueries (no N+1)
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.evaluation_report import EvaluationReport
from app.db.models.interview_session import InterviewSession
from app.db.models.topic import Topic


# ── Helpers ────────────────────────────────────────────────────────────────────


def _active_topic_options():
    """Return selectinload options for eager-loading parent + subtopics."""
    return [
        selectinload(Topic.parent_topic),
        selectinload(Topic.subtopics),
    ]


# ── Topic queries ──────────────────────────────────────────────────────────────


async def get_topic_by_id(
    db: AsyncSession, topic_id: uuid.UUID
) -> Optional[Topic]:
    """Load a topic by ID regardless of ownership (no access filter)."""
    result = await db.execute(
        select(Topic)
        .where(Topic.id == topic_id, Topic.deleted_at.is_(None))
        .options(*_active_topic_options())
    )
    return result.scalar_one_or_none()


async def get_topic_accessible(
    db: AsyncSession, topic_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[Topic]:
    """Load a topic that is either global or owned by `user_id`."""
    result = await db.execute(
        select(Topic)
        .where(
            Topic.id == topic_id,
            Topic.deleted_at.is_(None),
            or_(Topic.is_global.is_(True), Topic.created_by_user_id == user_id),
        )
        .options(*_active_topic_options())
    )
    return result.scalar_one_or_none()


async def get_topic_by_name_for_user(
    db: AsyncSession, name: str, user_id: uuid.UUID
) -> Optional[Topic]:
    """Return existing user-owned topic with this name (for duplicate check)."""
    result = await db.execute(
        select(Topic).where(
            Topic.name == name,
            Topic.created_by_user_id == user_id,
            Topic.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_accessible_topics(
    db: AsyncSession, user_id: uuid.UUID
) -> list[Topic]:
    """
    Return all global topics + user-owned topics, ordered global-first then name.
    Subtopics are filtered to non-deleted only (post-load in service).
    """
    result = await db.execute(
        select(Topic)
        .where(
            Topic.deleted_at.is_(None),
            or_(Topic.is_global.is_(True), Topic.created_by_user_id == user_id),
        )
        .options(*_active_topic_options())
        .order_by(Topic.is_global.desc(), Topic.name.asc())
    )
    return list(result.scalars().all())


async def create_topic(
    db: AsyncSession,
    *,
    name: str,
    description: Optional[str] = None,
    user_id: uuid.UUID,
    parent_topic_id: Optional[uuid.UUID] = None,
) -> Topic:
    topic = Topic(
        name=name,
        description=description,
        is_global=False,
        created_by_user_id=user_id,
        parent_topic_id=parent_topic_id,
    )
    db.add(topic)
    await db.flush()
    return topic


async def soft_delete_topic(db: AsyncSession, topic: Topic) -> None:
    topic.deleted_at = datetime.now(timezone.utc)
    await db.flush()


# ── Analytics subqueries ───────────────────────────────────────────────────────


async def get_topic_analytics(
    db: AsyncSession, topic_id: uuid.UUID, user_id: uuid.UUID
) -> dict:
    """
    Compute avg_score, last_session_date, session_count for a single topic.

    Joins InterviewSession → EvaluationReport to compute avg score of ANALYZED
    sessions only. Uses aggregate SQL (no Python-level loops) for efficiency.
    """
    # All sessions for this user + topic
    sessions_q = (
        select(
            InterviewSession.created_at,
            EvaluationReport.overall_score,
        )
        .outerjoin(
            EvaluationReport,
            EvaluationReport.session_id == InterviewSession.id,
        )
        .where(
            InterviewSession.topic_id == topic_id,
            InterviewSession.user_id == user_id,
            InterviewSession.status == "ANALYZED",
            InterviewSession.deleted_at.is_(None),
        )
        .order_by(InterviewSession.created_at.desc())
    )

    rows = (await db.execute(sessions_q)).all()

    scored = [r.overall_score for r in rows if r.overall_score is not None]
    avg_score = round(sum(scored) / len(scored)) if scored else 0
    last_session_date = rows[0].created_at if rows else None

    # Total session count (any status, not just ANALYZED)
    count_result = await db.execute(
        select(func.count(InterviewSession.id)).where(
            InterviewSession.topic_id == topic_id,
            InterviewSession.user_id == user_id,
            InterviewSession.deleted_at.is_(None),
        )
    )
    session_count: int = count_result.scalar_one()

    return {
        "avg_score": avg_score,
        "last_session_date": last_session_date,
        "session_count": session_count,
    }


async def get_bulk_topic_analytics(
    db: AsyncSession, topic_ids: list[uuid.UUID], user_id: uuid.UUID
) -> dict[uuid.UUID, dict]:
    """
    Compute analytics for a list of topic IDs in two queries
    (one for avg + last date, one for total counts) — avoids N+1.
    """
    if not topic_ids:
        return {}

    # ── Avg score + last session date per topic ─────────────────────────────
    scored_q = (
        select(
            InterviewSession.topic_id,
            func.avg(EvaluationReport.overall_score).label("avg_score"),
            func.max(InterviewSession.created_at).label("last_session_date"),
        )
        .join(
            EvaluationReport,
            EvaluationReport.session_id == InterviewSession.id,
        )
        .where(
            InterviewSession.topic_id.in_(topic_ids),
            InterviewSession.user_id == user_id,
            InterviewSession.status == "ANALYZED",
            InterviewSession.deleted_at.is_(None),
        )
        .group_by(InterviewSession.topic_id)
    )
    scored_rows = (await db.execute(scored_q)).all()
    scored_map = {
        r.topic_id: {
            "avg_score": round(r.avg_score) if r.avg_score is not None else 0,
            "last_session_date": r.last_session_date,
        }
        for r in scored_rows
    }

    # ── Total session count per topic ────────────────────────────────────────
    count_q = (
        select(
            InterviewSession.topic_id,
            func.count(InterviewSession.id).label("session_count"),
        )
        .where(
            InterviewSession.topic_id.in_(topic_ids),
            InterviewSession.user_id == user_id,
            InterviewSession.deleted_at.is_(None),
        )
        .group_by(InterviewSession.topic_id)
    )
    count_rows = (await db.execute(count_q)).all()
    count_map = {r.topic_id: r.session_count for r in count_rows}

    # Merge into a single dict keyed by topic_id
    result: dict[uuid.UUID, dict] = {}
    for tid in topic_ids:
        result[tid] = {
            "avg_score": scored_map.get(tid, {}).get("avg_score", 0),
            "last_session_date": scored_map.get(tid, {}).get("last_session_date"),
            "session_count": count_map.get(tid, 0),
        }
    return result
