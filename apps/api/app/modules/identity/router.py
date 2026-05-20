"""
Identity router — HTTP layer for auth, profile, and skill preferences.

Route prefix /identity is applied when this router is mounted in main.py.

Public routes (no JWT):
  POST /identity/register
  POST /identity/login
  POST /identity/request-otp
  POST /identity/verify-otp
  POST /identity/google

Protected routes (JWT required via CurrentUser):
  GET  /identity/me
  PUT  /identity/me
  GET  /identity/skill-tags
  POST /identity/me/skills
  DELETE /identity/me/skills/{skill_tag_id}
"""
import uuid

from fastapi import APIRouter

from app.deps import CurrentUser, DBSession
from app.modules.identity import service
from app.modules.identity.schemas import (
    AddSkillPreferenceRequest,
    AuthResponse,
    GoogleLoginRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    RequestOtpRequest,
    SkillPreferenceResponse,
    SkillTagResponse,
    UpdateProfileRequest,
    UserProfileResponse,
    VerifyOtpRequest,
)

router = APIRouter()


# ── Auth (public) ──────────────────────────────────────────────────────────────


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(body: RegisterRequest, db: DBSession):
    return await service.register(db, body)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: DBSession):
    return await service.login(db, body)


@router.post("/request-otp", response_model=MessageResponse)
async def request_otp(body: RequestOtpRequest, db: DBSession):
    return await service.request_otp(db, body.identifier)


@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp(body: VerifyOtpRequest, db: DBSession):
    return await service.verify_otp(db, body)


@router.post("/google", response_model=AuthResponse)
async def google_login(body: GoogleLoginRequest, db: DBSession):
    return await service.google_login(db, body.token)


# ── Profile (protected) ────────────────────────────────────────────────────────


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(current_user: CurrentUser, db: DBSession):
    return await service.get_profile(db, current_user.id)


@router.put("/me", response_model=UserProfileResponse)
async def update_profile(
    body: UpdateProfileRequest, current_user: CurrentUser, db: DBSession
):
    return await service.update_profile(db, current_user.id, body)


# ── Skill Tags (protected) ─────────────────────────────────────────────────────


@router.get("/skill-tags", response_model=list[SkillTagResponse])
async def get_skill_tags(current_user: CurrentUser, db: DBSession):
    return await service.get_skill_tags(db)


# ── Skill Preferences (protected) ─────────────────────────────────────────────


@router.post("/me/skills", response_model=SkillPreferenceResponse, status_code=201)
async def add_skill_preference(
    body: AddSkillPreferenceRequest, current_user: CurrentUser, db: DBSession
):
    return await service.add_skill_preference(db, current_user.id, body)


@router.delete("/me/skills/{skill_tag_id}", response_model=MessageResponse)
async def remove_skill_preference(
    skill_tag_id: uuid.UUID, current_user: CurrentUser, db: DBSession
):
    return await service.remove_skill_preference(db, current_user.id, skill_tag_id)
