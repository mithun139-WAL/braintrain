"""
Analytics service — business logic for user performance analytics.

Two public methods:
  get_analytics(db, user_id)   — full session history, trend, improvement delta, per-topic breakdown
  get_progression(db, user_id) — last-two-sessions delta for dopamine-loop banner

All logic is a direct port of NestJS AnalyticsService with Python idioms.

Matches NestJS: apps/backend/src/modules/analytics/analytics.service.ts
"""
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics import repository as repo
from app.modules.analytics.schemas import (
    AnalyticsResponseSchema,
    ImprovementSchema,
    ProgressionResponseSchema,
    SessionRefSchema,
    TopicBreakdownSchema,
    TrendItemSchema,
)


async def get_analytics(
    db: AsyncSession, user_id: uuid.UUID
) -> AnalyticsResponseSchema:
    """
    GET /analytics/me — full user performance overview.

    Returns:
      totalSessions     — all sessions (including unanalyzed)
      analyzedSessions  — sessions with an EvaluationReport
      trend             — chronological score array from analyzed sessions
      improvement       — delta from first → latest analyzed session
      byTopic           — average overall score per topic
    """
    sessions = await repo.get_sessions_with_evaluations(db, user_id)

    total_sessions = len(sessions)
    analyzed = [s for s in sessions if s.evaluation is not None]

    # ── Build trend ────────────────────────────────────────────────────────────
    trend: list[TrendItemSchema] = [
        TrendItemSchema(
            session_id=s.id,
            topic_name=s.topic.name if s.topic else "",
            interview_type=s.interview_type,
            analyzed_at=s.evaluation.created_at.isoformat(),
            overall_score=s.evaluation.overall_score,
            confidence_score=s.evaluation.confidence_score,
            clarity_score=s.evaluation.clarity_score,
            structure_score=s.evaluation.structure_score,
            depth_score=s.evaluation.depth_score,
        )
        for s in analyzed
    ]

    # ── Improvement delta ──────────────────────────────────────────────────────
    improvement = _build_improvement(analyzed)

    # ── Per-topic breakdown ────────────────────────────────────────────────────
    # Group analyzed sessions by topic_id, compute avg overall score
    topic_map: dict[uuid.UUID, dict] = {}
    for s in analyzed:
        tid = s.topic_id
        if tid not in topic_map:
            topic_map[tid] = {
                "name": s.topic.name if s.topic else "",
                "scores": [],
            }
        topic_map[tid]["scores"].append(s.evaluation.overall_score)

    by_topic: list[TopicBreakdownSchema] = [
        TopicBreakdownSchema(
            topic_id=topic_id,
            topic_name=info["name"],
            session_count=len(info["scores"]),
            avg_overall_score=round(
                sum(info["scores"]) / len(info["scores"]), 1
            ),
        )
        for topic_id, info in topic_map.items()
    ]

    return AnalyticsResponseSchema(
        total_sessions=total_sessions,
        analyzed_sessions=len(analyzed),
        trend=trend,
        improvement=improvement,
        by_topic=by_topic,
    )


async def get_progression(
    db: AsyncSession, user_id: uuid.UUID
) -> ProgressionResponseSchema:
    """
    GET /analytics/progression — dopamine-loop delta banner.

    Returns the last session, the one before it, and the score delta.
    Designed to power "You improved by +X.X points!" notifications.
    """
    last_two = await repo.get_last_two_analyzed_sessions(db, user_id)

    if not last_two:
        return ProgressionResponseSchema(
            last_session=None,
            previous_session=None,
            delta=None,
        )

    last = last_two[0]
    prev = last_two[1] if len(last_two) > 1 else None

    last_score: Optional[float] = last.evaluation.overall_score if last.evaluation else None
    prev_score: Optional[float] = prev.evaluation.overall_score if (prev and prev.evaluation) else None

    delta: Optional[float] = None
    if last_score is not None and prev_score is not None:
        delta = round(last_score - prev_score, 1)

    return ProgressionResponseSchema(
        last_session=SessionRefSchema(
            session_id=last.id,
            overall_score=last_score,
            analyzed_at=(
                last.evaluation.created_at.isoformat()
                if last.evaluation
                else None
            ),
        ),
        previous_session=(
            SessionRefSchema(
                session_id=prev.id,
                overall_score=prev_score,
                analyzed_at=(
                    prev.evaluation.created_at.isoformat()
                    if prev and prev.evaluation
                    else None
                ),
            )
            if prev
            else None
        ),
        delta=delta,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────


def _build_improvement(analyzed_sessions) -> ImprovementSchema:
    """
    Compute deltas between the first and latest analyzed sessions.
    Returns zeroed improvement if fewer than 2 analyzed sessions exist.
    """
    if len(analyzed_sessions) < 2:
        return ImprovementSchema(
            overall_delta=0.0,
            confidence_delta=0.0,
            clarity_delta=0.0,
            top_improved_dimension=None,
            top_weak_dimension=None,
        )

    first_eval = analyzed_sessions[0].evaluation
    latest_eval = analyzed_sessions[-1].evaluation

    deltas: dict[str, float] = {
        "overall":    latest_eval.overall_score    - first_eval.overall_score,
        "confidence": latest_eval.confidence_score - first_eval.confidence_score,
        "clarity":    latest_eval.clarity_score    - first_eval.clarity_score,
        "structure":  latest_eval.structure_score  - first_eval.structure_score,
        "depth":      latest_eval.depth_score      - first_eval.depth_score,
    }

    sorted_deltas = sorted(deltas.items(), key=lambda x: x[1], reverse=True)

    top_improved = sorted_deltas[0][0] if sorted_deltas else None

    negative = [(k, v) for k, v in deltas.items() if v < 0]
    top_weak = min(negative, key=lambda x: x[1])[0] if negative else None

    return ImprovementSchema(
        overall_delta=round(deltas["overall"], 1),
        confidence_delta=round(deltas["confidence"], 1),
        clarity_delta=round(deltas["clarity"], 1),
        top_improved_dimension=top_improved,
        top_weak_dimension=top_weak,
    )
