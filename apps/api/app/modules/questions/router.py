"""
Questions router — HTTP layer for question generation.

Route: POST /sessions/{session_id}/questions/next
All routes are JWT-protected.
"""
import uuid

from fastapi import APIRouter

from app.deps import CurrentUser, DBSession
from app.modules.questions import service
from app.modules.questions.schemas import QuestionResponse

router = APIRouter()


@router.post(
    "/sessions/{session_id}/questions/next",
    response_model=QuestionResponse,
    status_code=201,
    tags=["questions"],
)
async def generate_next_question(
    session_id: uuid.UUID, current_user: CurrentUser, db: DBSession
):
    return await service.generate_next_question(db, session_id, current_user.id)
