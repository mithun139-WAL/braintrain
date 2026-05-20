"""
Responses service — submits a response for a question instance.

Business rules:
  - At least one of answer_text or audio_url must be provided (enforced in schema)
  - Question must exist and belong to the user's session
  - Session must be in ACTIVE status
  - Duplicate responses are rejected
  - audio_processing_status is set at submission time:
      PENDING  → audioUrl present (Whisper runs during EvaluationJob)
      SKIPPED  → text-only submission
"""
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.modules.responses import repository as repo
from app.modules.responses.schemas import ResponseInstanceResponse, SubmitResponseRequest

logger = logging.getLogger(__name__)


async def submit_response(
    db: AsyncSession,
    question_id: uuid.UUID,
    user_id: uuid.UUID,
    dto: SubmitResponseRequest,
) -> ResponseInstanceResponse:
    # 1. Load question + session with ownership check
    question = await repo.get_question_with_session(db, question_id, user_id)
    if not question:
        raise NotFoundException(
            "Question not found or you do not have permission to access it"
        )

    # 2. Session must be ACTIVE
    if question.session.status != "ACTIVE":
        raise BadRequestException("Responses can only be submitted for ACTIVE sessions")

    # 3. Prevent duplicate
    existing = await repo.get_existing_response(db, question_id)
    if existing:
        raise BadRequestException("A response has already been submitted for this question")

    # 4. Compute lightweight metrics
    answer_length = len(dto.answer_text) if dto.answer_text else 0

    # 5. Set audio processing status
    audio_processing_status = "PENDING" if dto.audio_url else "SKIPPED"

    # 6. Persist
    response = await repo.create_response(
        db,
        question_id=question_id,
        session_id=question.session.id,
        answer_text=dto.answer_text or None,
        audio_url=dto.audio_url or None,
        response_time_ms=dto.response_time_ms,
        thinking_time_ms=dto.thinking_time_ms,
        answer_length=answer_length,
        audio_processing_status=audio_processing_status,
    )
    await db.commit()
    await db.refresh(response)

    return ResponseInstanceResponse.model_validate(response)
