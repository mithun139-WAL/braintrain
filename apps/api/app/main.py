"""
FastAPI application factory — BrainTrain API.

Responsibilities:
  - Create and configure the FastAPI app instance
  - Register CORS middleware
  - Register response envelope middleware
  - Register global exception handlers
  - Mount the rate limiter
  - Register all feature routers (stubs for now, filled in Phase 2+)
  - Start/stop the background job scheduler (APScheduler)

Phase 1: Only GET / health check is active.
Phase 2+: Feature routers are uncommented as each module is implemented.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.middleware import ResponseEnvelopeMiddleware
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Application lifespan ───────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown logic.
    Replace the stub with real scheduler start/stop in Phase 8.
    """
    logger.info("BrainTrain API starting — env=%s", settings.app_env)
    logger.info(
        "AI providers: %s",
        "OpenAI (GPT-4o-mini + Whisper-1)" if settings.ai_enabled else "Stub (offline mode)",
    )

    # ── Phase 8: evaluation worker scheduler ──────────────────────────────────
    from app.workers.scheduler import start_scheduler
    start_scheduler()

    yield

    # ── Phase 8: stop scheduler cleanly on shutdown ───────────────────────────
    from app.workers.scheduler import stop_scheduler
    stop_scheduler()

    logger.info("BrainTrain API shutting down")


# ── App factory ────────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    app = FastAPI(
        title="BrainTrain API",
        description="Confidence-first interview training platform — FastAPI backend",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,   # disable Swagger in prod
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # ── Rate limiter (SlowAPI — mirrors NestJS ThrottlerModule) ───────────────
    # Default: 30 requests / 60 seconds per IP (configured in core/rate_limit.py)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Response envelope middleware ───────────────────────────────────────────
    # Wraps all 2xx JSON responses in { success: true, data: <payload> }
    # Must be added AFTER CORSMiddleware (middleware stack is LIFO)
    app.add_middleware(ResponseEnvelopeMiddleware)

    # ── Exception handlers ─────────────────────────────────────────────────────
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.add_exception_handler(
        RateLimitExceeded,
        lambda req, exc: __import__("fastapi.responses", fromlist=["JSONResponse"]).JSONResponse(
            status_code=429,
            content={"success": False, "code": "TOO_MANY_REQUESTS", "message": str(exc)},
        ),
    )

    # ── Feature routers ───────────────────────────────────────────────────────
    # Uncomment each router as the corresponding phase is implemented.
    # They are imported here (not at module level) to avoid ImportError
    # before the module is built.

    # Phase 2 — Identity
    from app.modules.identity.router import router as identity_router
    app.include_router(identity_router, prefix="/identity", tags=["identity"])

    # Phase 3 — Topics
    from app.modules.topics.router import router as topics_router
    app.include_router(topics_router, prefix="/topics", tags=["topics"])

    # Phase 4 — Question Bank
    from app.modules.question_bank.router import router as question_bank_router
    app.include_router(question_bank_router, prefix="/question-bank", tags=["question-bank"])

    # Phase 5 — Sessions
    from app.modules.sessions.router import router as sessions_router
    app.include_router(sessions_router, prefix="/sessions", tags=["sessions"])

    # Phase 6 — Questions (nested: /sessions/:id/questions/next)
    from app.modules.questions.router import router as questions_router
    app.include_router(questions_router, tags=["questions"])

    # Phase 7 — Responses (nested: /questions/:id/responses)
    from app.modules.responses.router import router as responses_router
    app.include_router(responses_router, tags=["responses"])

    # Phase 8 — Evaluation (nested: /sessions/:id/evaluation/*)
    from app.modules.evaluation.router import router as evaluation_router
    app.include_router(evaluation_router, tags=["evaluation"])

    # Phase 9 — Analytics
    from app.modules.analytics.router import router as analytics_router
    app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])

    # Phase 10 — AI Coaching
    from app.modules.coaching.router import router as coaching_router
    app.include_router(coaching_router, prefix="/coaching", tags=["coaching"])

    # Phase 11 — Training Plans
    from app.modules.training_plans.router import router as training_plans_router
    app.include_router(training_plans_router, prefix="/training-plans", tags=["training-plans"])

    # Phase 12 — Billing
    from app.modules.billing.router import router as billing_router, webhook_router as billing_webhook_router
    app.include_router(billing_router, prefix="/billing", tags=["billing"])
    app.include_router(billing_webhook_router, prefix="/billing", tags=["billing"])

    # Phase 13 — Interview Journey
    from app.interview_journey.routers.journey_router import router as journey_router
    app.include_router(journey_router, prefix="/journeys", tags=["interview-journey"])

    return app


# ── Health check ───────────────────────────────────────────────────────────────
# Registered directly on the app so it's always available, even before
# any feature routers are mounted.

app = create_app()


@app.get("/", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    Returns app status and AI provider mode.
    Equivalent to NestJS GET / AppController.
    """
    return {
        "status": "ok",
        "env": settings.app_env,
        "ai_mode": "openai" if settings.ai_enabled else "stub",
    }
