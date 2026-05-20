"""
Shared FastAPI dependencies.

This is the ONLY place where:
  - DB sessions are yielded into request handlers
  - JWT tokens are decoded and validated
  - The current authenticated user is resolved from the DB

Design: Use type aliases (CurrentUser, DBSession) in route signatures to
keep them clean. Import from here, never re-implement auth logic elsewhere.

Example route usage:
    from app.deps import CurrentUser, DBSession

    @router.get("/me")
    async def get_profile(current_user: CurrentUser, db: DBSession):
        ...
"""
import uuid
from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.models.user import User
from app.db.session import SessionLocal

# ── Database dependency ────────────────────────────────────────────────────────

bearer_scheme = HTTPBearer(
    scheme_name="JWT",
    description="JWT Bearer token from POST /identity/login or /identity/register",
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async DB session for the duration of a single request.
    Session is automatically closed after the request completes.
    Transactions must be committed explicitly in services/repositories.
    """
    async with SessionLocal() as session:
        yield session


# ── Auth dependency ────────────────────────────────────────────────────────────


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Decode the JWT from the Authorization: Bearer header,
    verify it is valid and not expired, and return the User from DB.

    Returns 401 if:
      - No token provided
      - Token is malformed or expired
      - User does not exist or has been soft-deleted

    Mirrors NestJS JwtAuthGuard + JwtStrategy behaviour.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise unauthorized

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise unauthorized

    try:
        parsed_id = uuid.UUID(user_id)
    except ValueError:
        raise unauthorized

    result = await db.execute(
        select(User).where(
            User.id == parsed_id,
            User.deleted_at.is_(None),  # exclude soft-deleted users
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise unauthorized

    return user


# ── Convenience type aliases ──────────────────────────────────────────────────
# Use these directly in route signatures — they read as self-documenting.

DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
