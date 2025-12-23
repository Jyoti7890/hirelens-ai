import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("hirelens")

def send_otp_email(receiver_email: str, otp: int) -> bool:
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM_EMAIL")
    from_name = os.getenv("RESEND_FROM_NAME", "HireLens AI")
    base_url = os.getenv("RESEND_BASE_URL", "https://api.resend.com")
    timeout = int(os.getenv("EMAIL_TIMEOUT", "10"))

    if not api_key or not from_email:
        logger.error("Resend configuration missing: RESEND_API_KEY or RESEND_FROM_EMAIL not set")
        return False

    payload = {
        "from": f"{from_name} <{from_email}>",
        "to": receiver_email,
        "subject": "Your Verification OTP",
        "text": f"Your OTP is: {otp}\n\nThis code will expire in 5 minutes."
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(f"{base_url}/emails", json=payload, headers=headers, timeout=timeout)
        if 200 <= resp.status_code < 300:
            return True
        logger.error(f"Resend API error: {resp.status_code} {resp.text}")
        return False
    except Exception as e:
        logger.error(f"Resend API request failed: {e}")
        return False
