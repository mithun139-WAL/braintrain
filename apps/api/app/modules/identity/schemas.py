"""
Identity module — Pydantic request / response schemas.

Mirrors the NestJS DTOs exactly:
  - RegisterDto, LoginDto, VerifyOtpDto, GoogleLoginDto
  - UpdateProfileDto, AddSkillPreferenceDto

Response shapes match what NestJS IdentityService returned so the frontend
does not need to change.
"""
import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, HttpUrl, field_validator, model_validator


# ── Request schemas ────────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None

    @model_validator(mode="after")
    def email_or_phone_required(self) -> "RegisterRequest":
        if not self.email and not self.phone_number:
            raise ValueError("email or phone_number is required")
        return self

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) < 6:
            raise ValueError("password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None

    @model_validator(mode="after")
    def email_or_phone_required(self) -> "LoginRequest":
        if not self.email and not self.phone_number:
            raise ValueError("email or phone_number is required")
        return self


class RequestOtpRequest(BaseModel):
    identifier: str  # email address OR phone number


class VerifyOtpRequest(BaseModel):
    identifier: str
    code: str


class GoogleLoginRequest(BaseModel):
    token: str


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

    @field_validator("display_name")
    @classmethod
    def display_name_max(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 100:
            raise ValueError("display_name must be 100 characters or fewer")
        return v

    @field_validator("bio")
    @classmethod
    def bio_max(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 500:
            raise ValueError("bio must be 500 characters or fewer")
        return v


class AddSkillPreferenceRequest(BaseModel):
    skill_tag_id: uuid.UUID
    level: Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"]


# ── Response schemas ───────────────────────────────────────────────────────────


class UserBasicResponse(BaseModel):
    id: uuid.UUID
    email: Optional[str] = None
    phone_number: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    user: UserBasicResponse


class SkillTagResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_global: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SkillPreferenceResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    skill_tag_id: uuid.UUID
    level: str
    created_at: datetime
    updated_at: datetime
    skill_tag: SkillTagResponse

    model_config = {"from_attributes": True}


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    email: Optional[str] = None
    phone_number: Optional[str] = None
    google_id: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    plan_type: str
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_subscription_status: Optional[str] = None
    monthly_session_count: int
    monthly_evaluation_credits: int
    usage_period_start: datetime
    created_at: datetime
    updated_at: datetime
    skill_preferences: list[SkillPreferenceResponse] = []

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str
