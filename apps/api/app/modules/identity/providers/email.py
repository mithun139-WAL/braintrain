"""
Email provider — sends OTP codes via SMTP using aiosmtplib.

Mirrors NestJS EmailService (nodemailer) with identical:
  - HTML template
  - Subject line
  - From address from SMTP_FROM config

Falls back to a log-only stub when SMTP credentials are not configured,
so local development works without a mail server.
"""
import logging
import ssl

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailProvider:
    """Async SMTP email sender for OTP delivery."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def send_otp(self, to_email: str, otp_code: str) -> None:
        """Send a 6-digit OTP to `to_email`. Raises on delivery failure."""
        settings = self._settings

        if not settings.smtp_user or not settings.smtp_pass:
            # Stub mode: log and return — no credentials configured
            logger.warning(
                "[EmailProvider STUB] OTP for %s: %s (SMTP not configured)",
                to_email,
                otp_code,
            )
            return

        try:
            import aiosmtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Your BrainTrain Verification Code"
            msg["From"] = f'"BrainTrain Support" <{settings.smtp_from}>'
            msg["To"] = to_email

            plain = (
                f"Your BrainTrain verification code is: {otp_code}\n\n"
                "This code will expire in 2 minutes."
            )
            html = f"""
                <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                    <h2>BrainTrain Verification</h2>
                    <p>Your verification code is:</p>
                    <h1 style="font-size: 32px; letter-spacing: 4px; color: #007bff;">{otp_code}</h1>
                    <p>This code will expire in 2 minutes.
                       Please do not share this code with anyone.</p>
                </div>
            """

            msg.attach(MIMEText(plain, "plain"))
            msg.attach(MIMEText(html, "html"))

            use_tls = settings.smtp_port == 465
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_pass,
                use_tls=use_tls,
                start_tls=not use_tls,
            )
            logger.info("Email OTP sent to %s", to_email)

        except Exception as exc:
            logger.error("Failed to send email OTP to %s: %s", to_email, exc)
            raise
