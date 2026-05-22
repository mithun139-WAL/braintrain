"""
Central configuration — single source of truth for all env vars.

All settings are read from the environment (or .env.development in dev).
No module should ever read os.environ directly — always import `get_settings()`.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ─── App ─────────────────────────────────────────────────────────────────
    app_env: str = "development"
    port: int = 8000

    # ─── Database ─────────────────────────────────────────────────────────────
    # Must use asyncpg driver: postgresql+asyncpg://user:pass@host:port/db
    database_url: str

    # ─── Auth ─────────────────────────────────────────────────────────────────
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days

    # ─── Google OAuth ─────────────────────────────────────────────────────────
    google_client_id: str = ""

    # ─── OpenAI ───────────────────────────────────────────────────────────────
    # Leaving this empty enables all stub AI providers (safe for local dev)
    openai_api_key: str = ""

    # ─── NVIDIA NIM ───────────────────────────────────────────────────────────
    # Set NVIDIA_API_KEY (nvapi-...) to use NVIDIA NIM models.
    # NIM takes precedence over OpenAI when both keys are present.
    # NIM uses the OpenAI-compatible API, so no extra SDK is needed.
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    # Default NIM model — meta/llama-3.1-8b-instruct is available on the free tier.
    # Upgrade to nvidia/llama-3.1-nemotron-70b-instruct if your account has access.
    nvidia_model: str = "meta/llama-3.1-8b-instruct"

    # ─── Groq (audio transcription) ───────────────────────────────────────────
    # Groq runs Whisper on LPU hardware — faster than OpenAI and currently free.
    # Used ONLY for audio transcription. LLM tasks (evaluation, question gen,
    # coaching) are handled by NIM. Groq key format: gsk_...
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_whisper_model: str = "whisper-large-v3"

    # ─── SMTP (Email OTP) ─────────────────────────────────────────────────────
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = "noreply@braintrain.ai"

    # ─── Twilio (SMS OTP) ─────────────────────────────────────────────────────
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # ─── CORS ─────────────────────────────────────────────────────────────────
    frontend_url: str = "http://localhost:3000"

    # ─── LiveKit WebRTC ───────────────────────────────────────────────────────
    livekit_api_key: str = "devkey"
    livekit_api_secret: str = "secret"
    livekit_url: str = "ws://localhost:7880"


    # ─── Stripe Billing ───────────────────────────────────────────────────────
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_pro_price_id: str = ""
    stripe_success_url: str = "http://localhost:3000/dashboard/settings?billing=success"
    stripe_cancel_url: str = "http://localhost:3000/dashboard/settings?billing=cancelled"
    stripe_portal_return_url: str = "http://localhost:3000/dashboard/settings"
    pro_monthly_evaluation_credit_limit: int = 100

    # ─── SaaS Plan Limits ─────────────────────────────────────────────────────
    # Matches the UsageService constants from the NestJS backend
    free_monthly_session_limit: int = 3
    pro_monthly_session_limit: int = 20

    # ─── Rate Limiting ────────────────────────────────────────────────────────
    # Matches NestJS ThrottlerModule: 30 requests per 60 seconds per IP
    rate_limit_requests: int = 30
    rate_limit_window_seconds: int = 60

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def nim_enabled(self) -> bool:
        """True when a NVIDIA NIM API key is configured (nvapi-...)."""
        return bool(self.nvidia_api_key and self.nvidia_api_key.startswith("nvapi-"))

    @property
    def openai_enabled(self) -> bool:
        """True when a real OpenAI key is configured (sk-...)."""
        return bool(self.openai_api_key and self.openai_api_key.startswith("sk-"))

    @property
    def groq_enabled(self) -> bool:
        """True when a Groq API key is configured (gsk_...)."""
        return bool(self.groq_api_key and self.groq_api_key.startswith("gsk_"))

    @property
    def ai_enabled(self) -> bool:
        """True when any real AI provider is configured (NIM takes precedence)."""
        return self.nim_enabled or self.openai_enabled

    model_config = SettingsConfigDict(
        env_file=".env.development",
        env_file_encoding="utf-8",
        extra="ignore",  # silently discard unknown env vars
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    Use Depends(get_settings) in FastAPI routes when you need settings injected.
    Import and call directly in non-route code (services, workers, etc.).
    """
    return Settings()
