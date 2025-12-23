from fastapi import APIRouter, Form, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse
from backend.supabase_client import supabase
from backend.utils.email_service import send_otp_email
import random
from pathlib import Path
from datetime import datetime, timedelta
import re
import logging

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger("hirelens")

# Temporary in-memory password store (email → password)
temp_password_store = {}
temp_otp_store = {}
last_otp_sent = {}

# Frontend path
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


# ------------------------------------
# SIGNUP → SEND OTP
# ------------------------------------
@router.post("/send-otp")
def send_otp(background_tasks: BackgroundTasks, email: str = Form(...), password: str = Form(...)):
    try:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""):
            return HTMLResponse(
                "<script>alert('Invalid email format'); window.location='/signup';</script>"
            )

        # Check if user already exists
        try:
            existing = supabase.table("users").select("id").eq("email", email).execute()
        except Exception:
            existing = type("Obj", (), {"data": []})()

        if existing.data:
            return HTMLResponse(
                "<script>alert('Email already registered. Please login.'); window.location='/login';</script>"
            )

        otp = random.randint(100000, 999999)
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        # Upsert OTP
        try:
            supabase.table("temp_otp").upsert({
                "email": email,
                "otp": str(otp),
                "expires_at": expires_at.isoformat()
            }, on_conflict="email").execute()
        except Exception:
            temp_otp_store[email] = {"otp": str(otp), "expires_at": expires_at}

        # Store password temporarily
        temp_password_store[email] = password

        last_otp_sent[email] = datetime.utcnow()
        background_tasks.add_task(send_otp_email, email, otp)

        return RedirectResponse(url="/otp", status_code=302)

    except Exception as e:
        logger.error(f"OTP send failed: {e}")
        return HTMLResponse("<script>alert('OTP send failed'); window.location='/signup';</script>")


# ------------------------------------
# LOAD OTP PAGE
# ------------------------------------
@router.get("/otp")
def otp_page():
    html = (FRONTEND / "otp.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


# ------------------------------------
# VERIFY OTP
# ------------------------------------
@router.post("/verify-otp")
def verify_otp(otp: str = Form(...)):
    try:
        now = datetime.utcnow()
        now_iso = now.isoformat()
        result = (
            supabase
            .table("temp_otp")
            .select("*")
            .eq("otp", str(otp))
            .gt("expires_at", now_iso)
            .limit(1)
            .execute()
        )

        email = None
        if result.data:
            email = result.data[0]["email"]
        else:
            for k, v in list(temp_otp_store.items()):
                if str(v.get("otp")) == str(otp) and v.get("expires_at") and v["expires_at"] > now:
                    email = k
                    break
            if not email:
                return RedirectResponse(
                    url="/otp?error=Invalid+or+Expired+OTP",
                    status_code=302
                )

        user_check = supabase.table("users").select("id").eq("email", email).execute()
        if not user_check.data:
            supabase.table("users").insert({
                "email": email,
                "password": temp_password_store.get(email, "")
            }).execute()

        supabase.table("temp_otp").delete().eq("email", email).execute()
        temp_password_store.pop(email, None)
        temp_otp_store.pop(email, None)

        response = RedirectResponse(url="/input", status_code=302)
        response.set_cookie("hr_email", email, httponly=True, samesite="Lax")
        response.set_cookie("hr_id", email, httponly=True, samesite="Lax")
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OTP verification failed: {e}")

@router.post("/resend-otp")
def resend_otp(background_tasks: BackgroundTasks, email: str = Form(...)):
    try:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""):
            return HTMLResponse(
                "<script>alert('Invalid email format'); window.location='/otp';</script>"
            )
        last = last_otp_sent.get(email)
        if last and (datetime.utcnow() - last).total_seconds() < 30:
            return HTMLResponse(
                "<script>alert('Please wait before requesting another OTP'); window.location='/otp';</script>"
            )
        otp = random.randint(100000, 999999)
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        try:
            supabase.table("temp_otp").upsert({
                "email": email,
                "otp": str(otp),
                "expires_at": expires_at.isoformat()
            }, on_conflict="email").execute()
        except Exception:
            temp_otp_store[email] = {"otp": str(otp), "expires_at": expires_at}
        last_otp_sent[email] = datetime.utcnow()
        background_tasks.add_task(send_otp_email, email, otp)
        return RedirectResponse(url="/otp?resent=1", status_code=302)
    except Exception as e:
        return HTMLResponse(
            f"<script>alert('Resend OTP failed: {e}'); window.location='/otp';</script>"
        )

# ------------------------------------
# LOGIN
# ------------------------------------
@router.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    try:
        res = supabase.table("users") \
            .select("*") \
            .eq("email", email) \
            .eq("password", password) \
            .execute()

        if not res.data:
            return HTMLResponse(
                "<script>alert('Invalid email or password'); window.location='/login';</script>"
            )

        response = RedirectResponse(url="/input", status_code=302)
        response.set_cookie("hr_email", email, httponly=True, samesite="Lax")
        response.set_cookie("hr_id", email, httponly=True, samesite="Lax")
        return response

    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


# ------------------------------------
# FORGOT PASSWORD
# ------------------------------------
@router.post("/forgot-password")
def forgot_password(email: str = Form(...)):
    try:
        res = supabase.table("users").select("id").eq("email", email).execute()

        if not res.data:
            return HTMLResponse(
                "<script>alert('Email not registered'); window.location='/forgot-password';</script>"
            )

        return RedirectResponse(
            url=f"/reset_password.html?email={email}",
            status_code=302
        )

    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        raise HTTPException(status_code=500, detail="Forgot password error")


# ------------------------------------
# RESET PASSWORD
# ------------------------------------
@router.post("/reset-password")
def reset_password(
    email: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...)
):
    try:
        if new_password != confirm_password:
            return HTMLResponse(
                "<script>alert('Passwords do not match'); history.back();</script>"
            )

        supabase.table("users") \
            .update({"password": new_password}) \
            .eq("email", email) \
            .execute()

        return RedirectResponse(url="/login", status_code=302)

    except Exception as e:
        logger.error(f"Reset password failed: {e}")
        raise HTTPException(status_code=500, detail="Reset password failed")

# ------------------------------------
# LOGOUT
# ------------------------------------
@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("hr_email")
    response.delete_cookie("hr_id")
    return response
