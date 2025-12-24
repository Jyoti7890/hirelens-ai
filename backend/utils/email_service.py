import os
import smtplib
import logging
import asyncio
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Logger (Render compatible)
logger = logging.getLogger("hirelens")


def _send_smtp_email_sync(receiver_email: str, otp: int) -> bool:
    """
    Synchronous SMTP email sender (Brevo).
    Runs inside thread executor to avoid blocking asyncio loop.
    """

    SMTP_HOST = "smtp-relay.brevo.com"
    SMTP_PORT = 587

    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    SENDER_NAME = os.getenv("SENDER_NAME", "HireLens AI")

    # ---- Mandatory safety checks ----
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.error("SMTP credentials missing")
        return False

    if not SENDER_EMAIL:
        logger.error("SENDER_EMAIL not set or not verified in Brevo")
        return False

    try:
        # ---- Build Email ----
        msg = MIMEMultipart()
        msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg["To"] = receiver_email
        msg["Subject"] = "Your OTP Verification Code"

        body = (
            f"Your One-Time Password (OTP) is:\n\n"
            f"{otp}\n\n"
            f"This code is valid for 5 minutes.\n"
            f"If you did not request this, please ignore this email."
        )

        msg.attach(MIMEText(body, "plain"))

        # ---- Secure SMTP connection ----
        context = ssl.create_default_context()

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls(context=context)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"OTP email sent successfully to {receiver_email}")
        return True

    except Exception as e:
        logger.exception("Failed to send OTP email via Brevo SMTP")
        return False


async def send_otp_email(receiver_email: str, otp: int) -> bool:
    """
    Async wrapper for SMTP email sending.
    Uses thread executor to keep FastAPI event loop non-blocking.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, _send_smtp_email_sync, receiver_email, otp
    )
