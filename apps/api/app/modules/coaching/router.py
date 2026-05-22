"""
Coaching router — AI coaching session endpoints.

Routes:
  POST   /coaching                     create coaching session + AI greeting
  GET    /coaching                     list user's coaching sessions
  GET    /coaching/:id                 get a specific coaching session with messages
  POST   /coaching/:id/messages        send a message + get AI reply
  PUT    /coaching/:id/end             end a coaching session
"""
import uuid

from fastapi import APIRouter

from app.deps import CurrentProUser, DBSession
from app.modules.coaching import service
from app.modules.coaching.schemas import (
    CoachingSessionListResponse,
    CoachingSessionResponse,
    CreateCoachingSessionRequest,
    SendMessageRequest,
    SendMessageResponse,
)

router = APIRouter()


@router.post(
    "",
    response_model=CoachingSessionResponse,
    status_code=201,
    summary="Create a new AI coaching session",
)
async def create_coaching_session(
    body: CreateCoachingSessionRequest,
    db: DBSession,
    current_user: CurrentProUser,
) -> CoachingSessionResponse:
    return await service.create_session(db, body, current_user.id)


@router.get(
    "",
    response_model=CoachingSessionListResponse,
    status_code=200,
    summary="List the authenticated user's coaching sessions",
)
async def list_coaching_sessions(
    db: DBSession,
    current_user: CurrentProUser,
    page: int = 1,
    limit: int = 20,
) -> CoachingSessionListResponse:
    return await service.list_sessions(db, current_user.id, page=page, limit=limit)


@router.get(
    "/{session_id}",
    response_model=CoachingSessionResponse,
    status_code=200,
    summary="Get a specific coaching session with all messages",
)
async def get_coaching_session(
    session_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentProUser,
) -> CoachingSessionResponse:
    return await service.get_session(db, session_id, current_user.id)


@router.post(
    "/{session_id}/messages",
    response_model=SendMessageResponse,
    status_code=201,
    summary="Send a message to the AI coach and receive a reply",
)
async def send_message(
    session_id: uuid.UUID,
    body: SendMessageRequest,
    db: DBSession,
    current_user: CurrentProUser,
) -> SendMessageResponse:
    return await service.send_message(db, session_id, current_user.id, body.content)


@router.put(
    "/{session_id}/end",
    response_model=CoachingSessionResponse,
    status_code=200,
    summary="End a coaching session",
)
async def end_coaching_session(
    session_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentProUser,
) -> CoachingSessionResponse:
    return await service.end_session(db, session_id, current_user.id)
