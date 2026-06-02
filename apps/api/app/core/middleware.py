"""
Response envelope middleware.

Mirrors the NestJS ResponseInterceptor behaviour:
- All successful (2xx) JSON responses are wrapped in { success: true, data: <payload> }
- Error responses (4xx, 5xx) are NOT wrapped — the exception handlers own that shape
- Non-JSON responses (files, streams, health SSE) pass through untouched

Design note:
  We read the full response body, re-wrap it, and return a new JSONResponse.
  This is fine for standard API responses.
  When streaming AI responses are added (Phase 6), those routes must set
  response.headers["X-No-Envelope"] = "1" to bypass wrapping.
"""
import json
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

_BYPASS_HEADER = "x-no-envelope"


class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # ── Skip non-2xx (errors have their own shape from exception handlers)
        if response.status_code < 200 or response.status_code >= 300:
            return response

        # ── Skip non-JSON content types (file downloads, HTML, SSE streams)
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # ── Allow individual routes to opt out (used by streaming endpoints)
        if response.headers.get(_BYPASS_HEADER):
            return response

        # ── Read, wrap, and return
        try:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            data = json.loads(body)
            wrapped = json.dumps({"success": True, "data": data}, default=str)

            # Rebuild headers without content-length (it changed after wrapping)
            headers = dict(response.headers)
            headers.pop("content-length", None)

            return Response(
                content=wrapped,
                status_code=response.status_code,
                headers=headers,
                media_type="application/json",
            )
        except Exception:
            # If anything goes wrong, pass the original response through unchanged
            logger.exception("ResponseEnvelopeMiddleware failed to wrap response")
            return response
