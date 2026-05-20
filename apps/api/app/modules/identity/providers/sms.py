"""
SMS provider — sends OTP codes via Twilio.

Mirrors NestJS SmsService with identical:
  - Message body template
  - Twilio credentials from config (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER)

Falls back to log-only stub when Twilio credentials are not configured.
"""
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SmsProvider:
    """Twilio SMS sender for OTP delivery."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def send_otp(self, to_number: str, otp_code: str) -> None:
        """Send a 6-digit OTP to `to_number`. Raises on delivery failure."""
        settings = self._settings

        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            # Stub mode: log and return — no credentials configured
            logger.warning(
                "[SmsProvider STUB] OTP for %s: %s (Twilio not configured)",
                to_number,
                otp_code,
            )
            return

        try:
            # twilio-python is sync; run in a thread pool to avoid blocking the
            # event loop.
            import asyncio
            from functools import partial
            from twilio.rest import Client

            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            body = (
                f"Your BrainTrain verification code is: {otp_code}. "
                "Valid for 1 minute."
            )

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                partial(
                    client.messages.create,
                    body=body,
                    from_=settings.twilio_phone_number,
                    to=to_number,
                ),
            )
            logger.info("SMS OTP sent to %s", to_number)

        except Exception as exc:
            logger.error("Failed to send SMS OTP to %s: %s", to_number, exc)
            raise
