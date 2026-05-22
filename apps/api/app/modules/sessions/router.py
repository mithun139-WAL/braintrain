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


