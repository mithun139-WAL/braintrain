"""
Exception classes and global exception handlers.

Mirrors the NestJS GlobalExceptionFilter behaviour:
- All errors return a consistent { success, code, message, details? } shape
- HTTP status codes are mapped to string codes (e.g. 404 → "NOT_FOUND")
- 5xx errors are logged at ERROR level; 4xx at WARNING level
- Validation errors (422) include the full Pydantic error list in `details`
"""
import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# ─── Status code → string code map ───────────────────────────────────────────
# Matches GlobalExceptionFilter in apps/backend/src/filters/

_STATUS_CODE_MAP: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    410: "GONE",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_SERVER_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
}


def _error_response(
    status_code: int,
    message: str,
    details: list | dict | None = None,
) -> JSONResponse:
    """Build the standard error envelope. Never wrapped by ResponseEnvelopeMiddleware."""
    body: dict = {
        "success": False,
        "code": _STATUS_CODE_MAP.get(status_code, "ERROR"),
        "message": message,
    }
    if details is not None:
        body["details"] = details
    return JSONResponse(status_code=status_code, content=body)


# ─── Exception handlers (registered in main.py) ───────────────────────────────


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code >= 500:
        logger.error("HTTP %s — %s %s", exc.status_code, request.method, request.url)
    else:
        logger.warning("HTTP %s — %s %s — %s", exc.status_code, request.method, request.url, exc.detail)

    return _error_response(exc.status_code, str(exc.detail))


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning("Validation error — %s %s", request.method, request.url)
    return _error_response(
        status_code=422,
        message="Request validation failed",
        details=exc.errors(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception — %s %s", request.method, request.url)
    return _error_response(500, "An unexpected error occurred")


# ─── Domain exception classes ─────────────────────────────────────────────────
# Raise these from services. The http_exception_handler above catches them when
# they are raised as HTTPException. For custom domain errors, raise HTTPException
# directly with the appropriate status code and detail message.
#
# Usage example:
#   from fastapi import HTTPException
#   raise HTTPException(status_code=404, detail="Session not found")
#
# These are convenience wrappers for the most common domain scenarios.

from fastapi import HTTPException


class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Access denied"):
        super().__init__(status_code=403, detail=detail)


class ConflictException(HTTPException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=409, detail=detail)


class BadRequestException(HTTPException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=400, detail=detail)


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=401, detail=detail)
