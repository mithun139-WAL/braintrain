"""
Responses router — HTTP layer for submitting question responses.

Routes:
  POST /questions/{question_id}/responses
  POST /questions/{question_id}/responses/{response_id}/followup
All routes are JWT-protected.
"""
import uuid

from fastapi import APIRouter

from app.deps import CurrentUser, DBSession
from app.modules.responses import service
from app.modules.responses.schemas import (
    FollowupRequest,
    FollowupResponse,
    ResponseInstanceResponse,
    SubmitResponseRequest,
)

router = APIRouter()


@router.post(
    "/questions/{question_id}/responses",
    response_model=ResponseInstanceResponse,
    status_code=201,
    tags=["responses"],
)
async def submit_response(
    question_id: uuid.UUID,
    body: SubmitResponseRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    return await service.submit_response(db, question_id, current_user.id, body)


@router.post(
    "/questions/{question_id}/responses/{response_id}/followup",
    response_model=FollowupResponse,
    status_code=200,
    tags=["responses"],
    summary="Analyse a submitted answer in real time and optionally return a follow-up probe question.",
)
async def check_followup(
    question_id: uuid.UUID,
    response_id: uuid.UUID,
    body: FollowupRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    return await service.check_followup(db, question_id, response_id, current_user.id, body)
