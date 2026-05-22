"""
Email provider — sends transactional emails via the Resend API.

Two email types:
  - OTP codes (6-digit, 2-minute expiry)
  - Email confirmation links (token-based, 24-hour expiry)

Falls back to a log-only stub when RESEND_API_KEY is not configured,
so local development works without a real email service.
"""
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailProvider:
    """Resend-backed email sender for OTP delivery and account confirmation."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def _is_configured(self) -> bool:
        return bool(self._settings.resend_api_key)

    async def send_otp(self, to_email: str, otp_code: str) -> None:
        """Send a 6-digit OTP code to `to_email`."""
        if not self._is_configured():
            logger.warning(
                "[EmailProvider STUB] OTP for %s: %s (RESEND_API_KEY not set)",
                to_email,
                otp_code,
            )
            return

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin:0;padding:0;background:#0d0f1a;font-family:'Inter',Arial,sans-serif;">
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#0d0f1a;padding:40px 16px;">
            <tr><td align="center">
              <table width="520" cellpadding="0" cellspacing="0"
                     style="background:#111827;border-radius:16px;border:1px solid #1e2a45;overflow:hidden;">
                <!-- Header -->
                <tr>
                  <td style="padding:32px 40px 24px;border-bottom:1px solid #1e2a45;">
                    <table cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="background:#3b6ef8;border-radius:10px;padding:8px 12px;display:inline-block;">
                          <span style="color:#fff;font-size:15px;font-weight:700;letter-spacing:-0.3px;">BrainTrain</span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <!-- Body -->
                <tr>
                  <td style="padding:40px 40px 32px;">
                    <p style="margin:0 0 8px;color:#94a3b8;font-size:13px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;">
                      Verification Code
                    </p>
                    <h1 style="margin:0 0 24px;color:#f1f5f9;font-size:26px;font-weight:700;letter-spacing:-0.5px;">
                      Your one-time passcode
                    </h1>
                    <p style="margin:0 0 32px;color:#94a3b8;font-size:15px;line-height:1.6;">
                      Use the code below to sign in to BrainTrain. This code expires in
                      <strong style="color:#e2e8f0;">2 minutes</strong>.
                    </p>
                    <!-- OTP display -->
                    <div style="background:#0d0f1a;border:1px solid #1e2a45;border-radius:12px;
                                padding:24px 32px;text-align:center;margin-bottom:32px;">
                      <span style="font-size:40px;font-weight:800;letter-spacing:12px;color:#4d82fc;
                                   font-family:'Courier New',monospace;">
                        {otp_code}
                      </span>
                    </div>
                    <p style="margin:0;color:#64748b;font-size:13px;line-height:1.6;">
                      If you didn't request this code, you can safely ignore this email.
                      Someone may have entered your email address by mistake.
                    </p>
                  </td>
                </tr>
                <!-- Footer -->
                <tr>
                  <td style="padding:20px 40px;border-top:1px solid #1e2a45;background:#0d0f1a;">
                    <p style="margin:0;color:#475569;font-size:12px;">
                      © 2025 BrainTrain Inc. · This is an automated message, please do not reply.
                    </p>
                  </td>
                </tr>
              </table>
            </td></tr>
          </table>
        </body>
        </html>
        """

        await self._send(
            to=to_email,
            subject="Your BrainTrain verification code",
            html=html,
        )
        logger.info("OTP email sent to %s", to_email)

    async def send_confirmation(self, to_email: str, confirmation_url: str, display_name: str | None = None) -> None:
        """Send an email-confirmation link to a newly registered user."""
        if not self._is_configured():
            logger.warning(
                "[EmailProvider STUB] Confirmation link for %s: %s (RESEND_API_KEY not set)",
                to_email,
                confirmation_url,
            )
            return

        name = display_name or "there"
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin:0;padding:0;background:#0d0f1a;font-family:'Inter',Arial,sans-serif;">
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#0d0f1a;padding:40px 16px;">
            <tr><td align="center">
              <table width="520" cellpadding="0" cellspacing="0"
                     style="background:#111827;border-radius:16px;border:1px solid #1e2a45;overflow:hidden;">
                <!-- Header -->
                <tr>
                  <td style="padding:32px 40px 24px;border-bottom:1px solid #1e2a45;">
                    <table cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="background:#3b6ef8;border-radius:10px;padding:8px 12px;">
                          <span style="color:#fff;font-size:15px;font-weight:700;letter-spacing:-0.3px;">BrainTrain</span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <!-- Body -->
                <tr>
                  <td style="padding:40px 40px 32px;">
                    <p style="margin:0 0 8px;color:#94a3b8;font-size:13px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;">
                      Confirm Your Email
                    </p>
                    <h1 style="margin:0 0 24px;color:#f1f5f9;font-size:26px;font-weight:700;letter-spacing:-0.5px;">
                      Welcome to BrainTrain, {name}
                    </h1>
                    <p style="margin:0 0 32px;color:#94a3b8;font-size:15px;line-height:1.6;">
                      Thanks for signing up! Click the button below to confirm your email address
                      and activate your account. This link expires in
                      <strong style="color:#e2e8f0;">24 hours</strong>.
                    </p>
                    <!-- CTA Button -->
                    <div style="text-align:center;margin-bottom:32px;">
                      <a href="{confirmation_url}"
                         style="display:inline-block;background:#3b6ef8;color:#fff;
                                font-size:15px;font-weight:700;text-decoration:none;
                                padding:14px 40px;border-radius:10px;letter-spacing:-0.2px;">
                        Confirm Email Address
                      </a>
                    </div>
                    <p style="margin:0 0 12px;color:#64748b;font-size:13px;line-height:1.6;">
                      Or copy and paste this URL into your browser:
                    </p>
                    <p style="margin:0;background:#0d0f1a;border:1px solid #1e2a45;border-radius:8px;
                               padding:12px 16px;font-size:12px;color:#4d82fc;word-break:break-all;">
                      {confirmation_url}
                    </p>
                  </td>
                </tr>
                <!-- Footer -->
                <tr>
                  <td style="padding:20px 40px;border-top:1px solid #1e2a45;background:#0d0f1a;">
                    <p style="margin:0;color:#475569;font-size:12px;">
                      © 2025 BrainTrain Inc. · If you didn't create an account, you can safely ignore this email.
                    </p>
                  </td>
                </tr>
              </table>
            </td></tr>
          </table>
        </body>
        </html>
        """

        await self._send(
            to=to_email,
            subject="Confirm your BrainTrain account",
            html=html,
        )
        logger.info("Confirmation email sent to %s", to_email)

    async def _send(self, to: str, subject: str, html: str) -> None:
        """Dispatch an email via the Resend API (runs sync SDK in thread pool)."""
        import asyncio
        import resend

        settings = self._settings
        resend.api_key = settings.resend_api_key

        params: resend.Emails.SendParams = {
            "from": settings.email_from,
            "to": [to],
            "subject": subject,
            "html": html,
        }

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: resend.Emails.send(params))
        except Exception as exc:
            logger.error("Resend delivery failed to %s: %s", to, exc)
            raise
