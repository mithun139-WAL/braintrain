"""
Analytics topic metrics helpers.

Shared query + shaping logic for topic-level analytics endpoints so the HTTP
layer and topic detail surfaces stay aligned with the main analytics module.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics import repository as repo
from app.modules.analytics.schemas import TopicAnalyticsResponseSchema, TopicTrendItemSchema


async def get_topic_analytics(
    db: AsyncSession,
    user_id: uuid.UUID,
    topic_id: uuid.UUID,
) -> TopicAnalyticsResponseSchema:
    sessions = await repo.get_topic_sessions_with_evaluations(db, user_id, topic_id)

    total_sessions = len(sessions)
    analyzed = [session for session in sessions if session.evaluation is not None]

    trend = [
        TopicTrendItemSchema(
            session_id=session.id,
            analyzed_at=session.evaluation.created_at.isoformat(),
            overall_score=session.evaluation.overall_score,
            confidence_score=session.evaluation.confidence_score,
            clarity_score=session.evaluation.clarity_score,
            structure_score=session.evaluation.structure_score,
            depth_score=session.evaluation.depth_score,
            interview_type=session.interview_type,
            interview_mode=session.interview_mode,
            difficulty=session.difficulty,
        )
        for session in analyzed
    ]

    recent_scores = [item.overall_score for item in trend[-10:]]
    average_score = round(sum(recent_scores) / len(recent_scores), 1) if recent_scores else 0.0

    score_delta = None
    if len(trend) >= 2:
        score_delta = round(trend[-1].overall_score - trend[-2].overall_score, 1)

    return TopicAnalyticsResponseSchema(
        topic_id=topic_id,
        total_sessions=total_sessions,
        analyzed_sessions=len(analyzed),
        average_score=average_score,
        score_delta=score_delta,
        latest_score=round(trend[-1].overall_score, 1) if trend else None,
        last_session_at=trend[-1].analyzed_at if trend else None,
        trend=trend,
    )
