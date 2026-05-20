"""
Rate limiting setup using SlowAPI.

Mirrors the NestJS ThrottlerModule configuration:
  ThrottlerModule.forRoot([{ ttl: 60_000, limit: 30 }])
  → 30 requests per 60 seconds per IP

Usage in routes:
    from app.core.rate_limit import limiter
    from fastapi import Request

    @router.get("/some-endpoint")
    @limiter.limit("30/minute")
    async def some_endpoint(request: Request, ...):
        ...

The `request: Request` parameter is required by SlowAPI — it must be present
in the route signature even if you don't use it directly.

The global limit is applied in main.py via app.state.limiter and the
RateLimitExceeded exception handler.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Key function: rate limit by client IP address
# For production behind a load balancer, replace with:
#   get_remote_address  →  custom function reading X-Forwarded-For
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["30/minute"],  # global default matches NestJS ThrottlerModule
)
