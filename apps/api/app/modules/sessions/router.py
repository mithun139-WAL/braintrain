"""
Sessions router — HTTP layer for session lifecycle.

All routes are JWT-protected.
Route prefix /sessions is applied when mounted in main.py.

Routes:
 POST /sessions              — create a session (enforces usage limits)
 GET  /sessions              — list sessions (paginated, filterable by status/topic)
 GET  /sessions/{id}         — get full session detail
 PUT  /sessions/{id}/start   — transition CREATED → ACTIVE
 PUT  /sessions/{id}/complete — transition ACTIVE → COMPLETED (enqueues eval job)
  GET  /sessions/{id}/status  — poll evaluation job status + overall score
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Query

from app.deps import CurrentUser, DBSession
from app.modules.sessions import service
from app.modules.sessions.schemas import (
    CreateSessionRequest,
    SessionListResponse,
    SessionResponse,
    SessionStatusResponse,
)

router = APIRouter()


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    body: CreateSessionRequest, current_user: CurrentUser, db: DBSession
):
    return await service.create_session(db, body, current_user.id)


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    current_user: CurrentUser,
    db: DBSession,
    status: Optional[str] = Query(None),
    topic_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    return await service.list_sessions(
        db,
        current_user.id,
        status=status,
        topic_id=topic_id,
        page=page,
        limit=limit,
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID, current_user: CurrentUser, db: DBSession
):
    return await service.get_session_by_id(db, session_id, current_user.id)


@router.put("/{session_id}/start", response_model=SessionResponse)
async def start_session(
    session_id: uuid.UUID, current_user: CurrentUser, db: DBSession
):
    return await service.start_session(db, session_id, current_user.id)


@router.put("/{session_id}/complete", response_model=SessionResponse)
async def complete_session(
    session_id: uuid.UUID, current_user: CurrentUser, db: DBSession
):
    return await service.complete_session(db, session_id, current_user.id)


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: uuid.UUID, current_user: CurrentUser, db: DBSession
):
    return await service.get_session_status(db, session_id, current_user.id)


@router.get("/{session_id}/webrtc-token")
async def get_webrtc_token(
    session_id: uuid.UUID, current_user: CurrentUser, db: DBSession
):
    # Verify session exists and is owned by the user
    await service.get_session_by_id(db, session_id, current_user.id)
    
    # Generate LiveKit WebRTC Access Token using python-jose
    import time
    from jose import jwt
    from app.core.config import get_settings
    
    settings = get_settings()
    current_time = int(time.time())
    expire_time = current_time + 3600 * 2  # 2 hours validity
    
    # Identity is the user name or email or ID
    identity = current_user.display_name or current_user.email or str(current_user.id)
    
    payload = {
        "iss": settings.livekit_api_key,
        "sub": identity,
        "nbf": current_time - 60,  # avoid clock drift issues
        "exp": expire_time,
        "video": {
            "roomJoin": True,
            "room": str(session_id),
            "canPublish": True,
            "canSubscribe": True,
            "canPublishData": True
        }
    }
    
    token = jwt.encode(
        payload,
        settings.livekit_api_secret,
        algorithm="HS256"
    )
    
    # Launch voice agent in the background for this session
    from app.ai.voice_agent import launch_voice_agent
    launch_voice_agent(str(session_id))
    
    return {"token": token}


# ══════════════════════════════════════════════════════════════════════════════
# Orchestrator Monitoring Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/{session_id}/orchestrators/stats")
async def get_orchestrator_stats(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession
):
    """
    Get orchestrator performance statistics for a session.
    
    Returns detailed metrics from all orchestrators:
    - Evaluation latency and disagreement rates
    - Model provider health and latencies
    - Realtime pipeline performance
    - Speculative cache hit rates
    - Active session count
    """
    # Verify session ownership
    await service.get_session_by_id(db, session_id, current_user.id)
    
    # Get active agent
    from app.ai.voice_agent import active_agents
    
    agent = active_agents.get(str(session_id))
    if not agent:
        return {
            "error": "Session not active or agent not found",
            "session_id": str(session_id)
        }
    
    if not hasattr(agent, 'orchestrator_hub'):
        return {
            "error": "Orchestrators not enabled for this session",
            "session_id": str(session_id)
        }
    
    # Get stats from orchestrator hub
    stats = agent.orchestrator_hub.get_performance_stats()
    
    return {
        "session_id": str(session_id),
        "evaluation": {
            "total_evaluations": stats["evaluation"].get("total_evaluations", 0),
            "avg_latency_ms": round(stats["evaluation"].get("avg_latency_ms", 0), 2),
            "max_latency_ms": round(stats["evaluation"].get("max_latency_ms", 0), 2),
            "min_latency_ms": round(stats["evaluation"].get("min_latency_ms", 0), 2),
            "disagreement_rate": round(stats["evaluation"].get("disagreement_rate", 0), 4),
            "cache_enabled": stats["evaluation"].get("cache_enabled", False),
        },
        "model_providers": {
            provider: {
                "health": round(provider_stats["health"], 3),
                "avg_latency_ms": round(provider_stats["avg_latency_ms"], 2),
                "p95_latency_ms": round(provider_stats["p95_latency_ms"], 2),
                "success_rate": round(provider_stats["success_rate"], 4),
                "total_requests": provider_stats["total_requests"],
                "failures": provider_stats["failures"],
            }
            for provider, provider_stats in stats["model"].items()
        },
        "realtime": {
            "total_turns": stats["realtime"].get("total_turns", 0),
            "avg_latency_ms": round(stats["realtime"].get("avg_latency_ms", 0), 2),
            "p95_latency_ms": round(stats["realtime"].get("p95_latency_ms", 0), 2),
            "target_ms": stats["realtime"].get("target_ms", 700),
            "budget_violations": stats["realtime"].get("budget_violations", 0),
            "violation_rate": round(stats["realtime"].get("violation_rate", 0), 4),
            "speculative_cache_hit_rate": round(
                stats["realtime"].get("speculative_cache_hit_rate", 0), 4
            ),
            "speculative_hits": stats["realtime"].get("speculative_hits", 0),
            "speculative_misses": stats["realtime"].get("speculative_misses", 0),
            "stage_latencies": {
                stage: {
                    "avg_ms": round(stage_stats["avg_ms"], 2),
                    "p95_ms": round(stage_stats["p95_ms"], 2),
                }
                for stage, stage_stats in stats["realtime"].get("stage_latencies", {}).items()
            },
        },
        "active_sessions": stats["active_sessions"],
    }


@router.get("/{session_id}/orchestrators/health")
async def get_orchestrator_health(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession
):
    """
    Get orchestrator health status for a session.
    
    Returns:
    - Overall health status (healthy/degraded/unhealthy)
    - Unhealthy model providers
    - Latency compliance
    - Recommendations for improvement
    """
    # Verify session ownership
    await service.get_session_by_id(db, session_id, current_user.id)
    
    # Get active agent
    from app.ai.voice_agent import active_agents
    
    agent = active_agents.get(str(session_id))
    if not agent:
        return {
            "status": "unknown",
            "error": "Session not active",
            "session_id": str(session_id)
        }
    
    if not hasattr(agent, 'orchestrator_hub'):
        return {
            "status": "disabled",
            "message": "Orchestrators not enabled",
            "session_id": str(session_id)
        }
    
    hub = agent.orchestrator_hub
    
    # Check model provider health
    model_stats = hub.model_orchestrator.get_provider_stats()
    unhealthy_providers = [
        provider
        for provider, stats in model_stats.items()
        if stats["health"] < 0.8
    ]
    
    # Check latency compliance
    realtime_stats = hub.realtime_orchestrator.get_performance_stats()
    avg_latency = realtime_stats.get("avg_latency_ms", 0)
    target_latency = realtime_stats.get("target_ms", 700)
    latency_ok = avg_latency < target_latency if avg_latency > 0 else True
    
    # Check evaluation performance
    eval_stats = hub.evaluation_orchestrator.get_performance_stats()
    eval_disagreement = eval_stats.get("disagreement_rate", 0)
    eval_ok = eval_disagreement < 0.15  # < 15% disagreement
    
    # Determine overall status
    if unhealthy_providers or not latency_ok or not eval_ok:
        status = "degraded"
    else:
        status = "healthy"
    
    if len(unhealthy_providers) >= 2:
        status = "unhealthy"
    
    # Generate recommendations
    recommendations = []
    
    if unhealthy_providers:
        recommendations.append(
            f"Model providers experiencing issues: {', '.join(unhealthy_providers)}"
        )
    
    if not latency_ok:
        recommendations.append(
            f"Average latency ({avg_latency:.0f}ms) exceeds target ({target_latency}ms)"
        )
    
    if not eval_ok:
        recommendations.append(
            f"High evaluation disagreement rate ({eval_disagreement:.1%})"
        )
    
    if not recommendations:
        recommendations.append("All systems operating normally")
    
    return {
        "session_id": str(session_id),
        "status": status,
        "checks": {
            "model_providers": {
                "healthy": len(unhealthy_providers) == 0,
                "unhealthy_providers": unhealthy_providers,
            },
            "latency": {
                "healthy": latency_ok,
                "avg_latency_ms": round(avg_latency, 2),
                "target_latency_ms": target_latency,
            },
            "evaluation": {
                "healthy": eval_ok,
                "disagreement_rate": round(eval_disagreement, 4),
                "target_disagreement_rate": 0.15,
            },
        },
        "recommendations": recommendations,
    }


@router.get("/{session_id}/orchestrators/state")
async def get_orchestrator_state(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession
):
    """
    Get current orchestrator state for a session.
    
    Returns:
    - Interview phase and progress
    - Candidate performance metrics
    - Current question state
    - Interviewer mood and strategy
    """
    # Verify session ownership
    await service.get_session_by_id(db, session_id, current_user.id)
    
    # Get active agent
    from app.ai.voice_agent import active_agents
    
    agent = active_agents.get(str(session_id))
    if not agent:
        return {
            "error": "Session not active",
            "session_id": str(session_id)
        }
    
    if not hasattr(agent, 'orchestrator_hub'):
        return {
            "error": "Orchestrators not enabled",
            "session_id": str(session_id)
        }
    
    hub = agent.orchestrator_hub
    
    # Get session state
    interview_state = hub.session_states.get(str(session_id))
    candidate_state = hub.candidate_states.get(str(session_id))
    current_question = hub.current_questions.get(str(session_id))
    
    if not interview_state or not candidate_state:
        return {
            "error": "Session state not initialized",
            "session_id": str(session_id)
        }
    
    return {
        "session_id": str(session_id),
        "interview": {
            "phase": interview_state.current_phase.value,
            "domain": interview_state.domain.value,
            "progress_percent": round(interview_state.interview_progress_percent, 2),
            "questions_asked": interview_state.questions_asked,
            "followups_asked": interview_state.followups_asked,
            "consecutive_followups": interview_state.consecutive_followups,
            "interviewer_mood": interview_state.interviewer_mood.value,
            "challenge_level": interview_state.current_challenge_level.value,
            "elapsed_minutes": round(
                (interview_state.updated_at - interview_state.started_at).total_seconds() / 60,
                2
            ),
        },
        "candidate": {
            "candidate_id": candidate_state.candidate_id,
            "current_performance_score": round(candidate_state.current_performance_score, 2),
            "current_confidence_score": round(candidate_state.current_confidence_score, 2),
            "performance_trend": candidate_state.performance_trend,
            "frustration_level": round(candidate_state.frustration_level, 3),
            "recent_answer_qualities": [
                q.value for q in candidate_state.answer_quality_history[-5:]
            ],
            "recent_scores": [round(s, 1) for s in candidate_state.recent_scores[-5:]],
        },
        "current_question": {
            "question_id": current_question.question_id if current_question else None,
            "question_text": current_question.question_text if current_question else None,
            "phase": current_question.phase.value if current_question else None,
            "asked_at": current_question.asked_at.isoformat() if current_question else None,
        } if current_question else None,
    }


