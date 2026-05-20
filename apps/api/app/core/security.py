"""
Security utilities — JWT lifecycle and password hashing.

Design notes:
- JWT payload uses 'sub' for userId (matches NestJS JwtStrategy convention)
- bcrypt is used for both passwords and OTP codes (matches NestJS bcrypt usage)
- decode_jwt returns None instead of raising so callers decide how to handle it
- Google ID token verification is here, not in the identity service, because it
  is a security primitive, not business logic
"""
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


# ─── Password / OTP hashing ───────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    """Bcrypt-hash a plaintext password or OTP code."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ─── JWT ──────────────────────────────────────────────────────────────────────


def create_access_token(user_id: str, email: str | None, phone_number: str | None) -> str:
    """
    Create a signed JWT.
    Payload mirrors the NestJS JwtStrategy payload: { sub, email, phoneNumber }.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "phoneNumber": phone_number,
        "iat": datetime.now(timezone.utc),
        "exp": expire,
        "jti": str(uuid.uuid4()),  # unique token ID — useful for future revocation
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """
    Decode and verify a JWT. Returns the payload dict or None if invalid/expired.
    Never raises — callers handle None as an authentication failure.
    """
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        return None


# ─── Google OAuth ─────────────────────────────────────────────────────────────


def verify_google_id_token(token: str) -> dict:
    """
    Verify a Google ID token and return the decoded payload.
    Raises ValueError if verification fails — callers convert to HTTPException.

    Returned payload includes: 'sub' (Google ID), 'email', 'name', 'picture'.
    """
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    if not settings.google_client_id:
        raise ValueError("GOOGLE_CLIENT_ID is not configured")

    try:
        request = google_requests.Request()
        payload = id_token.verify_oauth2_token(
            token,
            request,
            settings.google_client_id,
        )
        return payload
    except Exception as exc:
        raise ValueError(f"Invalid Google token: {exc}") from exc
