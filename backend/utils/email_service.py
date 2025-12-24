import os
import smtplib
import logging
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger("hirelens")

def _send_smtp_email_sync(receiver_email: str, otp: int) -> bool:
    """
    Synchronous function to send email using SMTP.
    This is meant to be run in a separate thread to avoid blocking the asyncio event loop.
    """
    smtp_host = "smtp-relay.brevo.com"
    smtp_port = 587
    
    # Get credentials from environment variables
    # User requested to use "Brevo API Key" as Username/Password implies strict dependency on env vars
    # We will look for standard SMTP_USERNAME/SMTP_PASSWORD variables
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    sender_email = os.getenv("SENDER_EMAIL", "noreply@hirelens.ai")
    sender_name = os.getenv("SENDER_NAME", "HireLens AI")

    if not smtp_username or not smtp_password:
        logger.error("SMTP credentials missing: SMTP_USERNAME or SMTP_PASSWORD not set")
        return False

    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = receiver_email
        msg["Subject"] = "Your Verification OTP"

        body = f"Your OTP is: {otp}\n\nThis code will expire in 5 minutes."
        msg.attach(MIMEText(body, "plain"))

        # Connect to SMTP server
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()  # Upgrade connection to secure
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            
        logger.info(f"OTP email sent successfully to {receiver_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send OTP email via Brevo SMTP: {e}")
        return False

async def send_otp_email(receiver_email: str, otp: int) -> bool:
    """
    Asynchronous wrapper for sending OTP email.
    Runs the synchronous SMTP call in a separate thread.
    """
    loop = asyncio.get_running_loop()
    # run_in_executor with None uses the default ThreadPoolExecutor
    return await loop.run_in_executor(None, _send_smtp_email_sync, receiver_email, otp)
