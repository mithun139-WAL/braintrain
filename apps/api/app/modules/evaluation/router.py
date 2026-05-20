"""
Evaluation router — POST /sessions/:id/evaluation/analyze + GET /sessions/:id/evaluation.

Routes:
  POST /sessions/{session_id}/evaluation/analyze
    Triggers AI evaluation for a COMPLETED session.
    Persists per-response scores, produces an aggregated EvaluationReport,
    and transitions the session to ANALYZED.
    Idempotent guard: throws 409 if already analyzed.

  GET /sessions/{session_id}/evaluation
    Retrieves an existing evaluation report.
    Returns 404 if the session has not been analyzed yet.

Matches NestJS: apps/backend/src/modules/evaluation/evaluation.controller.ts
"""
import uuid

from fastapi import APIRouter

from app.deps import CurrentUser, DBSession
from app.modules.evaluation import service
from app.modules.evaluation.schemas import SessionEvaluationResponseSchema

router = APIRouter()


@router.post(
    "/sessions/{session_id}/evaluation/analyze",
    response_model=SessionEvaluationResponseSchema,
    status_code=200,
    summary="Trigger AI evaluation for a completed session",
)
async def analyze_session(
    session_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> SessionEvaluationResponseSchema:
    return await service.analyze_session(db, session_id, current_user.id)


@router.get(
    "/sessions/{session_id}/evaluation",
    response_model=SessionEvaluationResponseSchema,
    status_code=200,
    summary="Get evaluation report for a session",
)
async def get_evaluation(
    session_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> SessionEvaluationResponseSchema:
    return await service.get_evaluation(db, session_id, current_user.id)
