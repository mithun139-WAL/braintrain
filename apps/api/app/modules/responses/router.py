"""
Responses router — HTTP layer for submitting question responses.

Route: POST /questions/{question_id}/responses
All routes are JWT-protected.
"""
import uuid

from fastapi import APIRouter

from app.deps import CurrentUser, DBSession
from app.modules.responses import service
from app.modules.responses.schemas import ResponseInstanceResponse, SubmitResponseRequest

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
