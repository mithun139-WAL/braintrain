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

  Follow-up analysis:
  - Called immediately after answer submission during a live session
  - Stateless: full conversation history is passed in the request
  - Capped at MAX_FOLLOWUP_ROUNDS rounds — afterwards always returns needs_followup=False
  - Falls back gracefully to stub (no follow-up) if LLM fails
"""
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.modules.responses import repository as repo
from app.modules.responses.schemas import (
    FollowupRequest,
    FollowupResponse,
    ResponseInstanceResponse,
    SubmitResponseRequest,
)

logger = logging.getLogger(__name__)

# Maximum follow-up rounds per question — enforced here so AI is never asked
# beyond this limit regardless of LLM output.
MAX_FOLLOWUP_ROUNDS = 2


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

    # 3. Prevent duplicate for the same type (first vs followup)
    existing_responses = await repo.get_existing_responses(db, question_id)
    has_initial = any(not r.is_followup for r in existing_responses)
    has_followup = any(r.is_followup for r in existing_responses)

    if not dto.is_followup and has_initial:
        raise BadRequestException("A response has already been submitted for this question")
    if dto.is_followup and has_followup:
        raise BadRequestException("A follow-up response has already been submitted for this question")

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
        is_followup=dto.is_followup,
    )
    await db.commit()
    await db.refresh(response)

    return ResponseInstanceResponse.model_validate(response)


async def check_followup(
    db: AsyncSession,
    question_id: uuid.UUID,
    response_id: uuid.UUID,
    user_id: uuid.UUID,
    dto: FollowupRequest,
) -> FollowupResponse:
    """
    Analyse the candidate's answer in real time and decide whether a follow-up
    probe is needed. If the max rounds cap is reached, skip the LLM call and
    signal the frontend to move on.

    Business rules:
      - question + response must exist and belong to the user's session
      - Session must still be ACTIVE (guard against stale requests)
      - prior_exchanges.length >= MAX_FOLLOWUP_ROUNDS → skip LLM, no more follow-ups
    """
    # 1. Validate question ownership
    question = await repo.get_question_with_session(db, question_id, user_id)
    if not question:
        raise NotFoundException(
            "Question not found or you do not have permission to access it"
        )

    if question.session.status != "ACTIVE":
        raise BadRequestException("Follow-up checks can only be run for ACTIVE sessions")

    # 2. Load the response — must belong to this question
    response = await repo.get_response_by_id(db, response_id)
    if not response or response.question_id != question_id:
        raise NotFoundException("Response not found for this question")

    exchange_number = len(dto.prior_exchanges)

    # 3. Cap enforcement — no more probes after MAX_FOLLOWUP_ROUNDS
    if exchange_number >= MAX_FOLLOWUP_ROUNDS:
        return FollowupResponse(
            needs_followup=False,
            followup_question=None,
            acknowledgement="Let's move on to the next question.",
            gap_identified=None,
            exchange_number=exchange_number,
        )

    # 4. Resolve the answer text (transcribed audio takes priority when available)
    answer_text = response.transcribed_text or response.answer_text or ""

    # 5. Run LLM analysis
    from app.ai.factory import get_followup_provider
    from app.ai.protocols import FollowupExchange, FollowupInput

    provider = get_followup_provider()
    signal = await provider.analyze(
        FollowupInput(
            question_text=question.content,
            answer_text=answer_text,
            interview_type=question.session.interview_type,
            difficulty=question.difficulty,
            prior_exchanges=[
                FollowupExchange(
                    followup_question=ex.followup_question,
                    followup_answer=ex.followup_answer,
                )
                for ex in dto.prior_exchanges
            ],
        )
    )

    logger.info(
        "Followup check | question=%s | round=%d | needs_followup=%s | gap=%s",
        question_id,
        exchange_number,
        signal.needs_followup,
        signal.gap_identified,
    )

    return FollowupResponse(
        needs_followup=signal.needs_followup,
        followup_question=signal.followup_question,
        acknowledgement=signal.acknowledgement,
        gap_identified=signal.gap_identified,
        exchange_number=exchange_number,
    )
