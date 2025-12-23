from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import logging

# -------------------------------
# App Initialization
# -------------------------------
app = FastAPI(title="HireLens Resume Screener")

# -------------------------------
# CORS (Required for frontend ↔ backend)
# -------------------------------
frontend_url = os.getenv("FRONTEND_URL")
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = []
if frontend_url:
    allowed_origins.append(frontend_url)
if allowed_origins_env:
    allowed_origins.extend([o.strip() for o in allowed_origins_env.split(",") if o.strip()])
if not allowed_origins:
    allowed_origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# -------------------------------
# Base & Frontend Directory
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# -------------------------------
# Static Files
# -------------------------------
# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hirelens")

# Static mounts: support case-sensitive deployments and absolute paths
static_path = FRONTEND_DIR / "static"
static_path_alt = FRONTEND_DIR / "Static"
styles_path = FRONTEND_DIR / "styles"
scripts_path = FRONTEND_DIR / "scripts"

if static_path.exists():
    app.mount("/static", StaticFiles(directory=static_path), name="static")
elif static_path_alt.exists():
    app.mount("/static", StaticFiles(directory=static_path_alt), name="static")
else:
    logger.warning(f"Static folder not found at: {static_path} or {static_path_alt}")

if styles_path.exists():
    app.mount("/styles", StaticFiles(directory=styles_path), name="styles")
elif static_path.exists():
    app.mount("/styles", StaticFiles(directory=static_path), name="styles")
elif static_path_alt.exists():
    app.mount("/styles", StaticFiles(directory=static_path_alt), name="styles")
else:
    logger.info("No styles directory found to mount")

if scripts_path.exists():
    app.mount("/scripts", StaticFiles(directory=scripts_path), name="scripts")

# -------------------------------
# HTML Loader Helper
# -------------------------------
def load_html(filename: str):
    path = FRONTEND_DIR / filename
    if path.exists():
        return HTMLResponse(path.read_text(encoding="utf-8"))
    return HTMLResponse("<h2>Page not found</h2>", status_code=404)

# -------------------------------
# HTML Routes
# -------------------------------
@app.get("/")
def home():
    return load_html("index.html")

@app.get("/login")
def login():
    return load_html("login.html")

@app.get("/signup")
def signup():
    return load_html("signup.html")

@app.get("/otp")
def otp():
    return load_html("otp.html")

@app.get("/input")
def input_page():
    return load_html("input.html")

@app.get("/upload")
def upload_page():
    return load_html("upload.html")

@app.get("/dashboard")
def dashboard():
    return load_html("dashboard.html")

@app.get("/dashboard.html")
def dashboard_html():
    return load_html("dashboard.html")

@app.get("/forgot-password")
def forgot_password():
    return load_html("forgot_password.html")

@app.get("/reset_password.html")
def reset_password(email: str = ""):
    path = FRONTEND_DIR / "reset_password.html"
    if path.exists():
        html = path.read_text(encoding="utf-8")
        return HTMLResponse(html.replace("{{email}}", email))
    return HTMLResponse("<h2>Page not found</h2>", status_code=404)

# Optional routes for direct file access
@app.get("/index.html")
def index_html():
    return load_html("index.html")

@app.get("/upload.html")
def upload_html():
    return load_html("upload.html")

@app.get("/input.html")
def input_html():
    return load_html("input.html")

# -------------------------------
# API Health & Root
# -------------------------------
@app.get("/api")
def api_root():
    return {"message": "HireLens API is running 🚀"}

@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------------
# Routers (Backend APIs)
# -------------------------------
from backend.routes.auth_routes import router as auth_router
from backend.routes.criteria_routes import router as criteria_router
from backend.routes.upload_routes import router as upload_router
from backend.routes.dashboard_routes import router as dashboard_router

app.include_router(auth_router)
app.include_router(criteria_router)
app.include_router(upload_router)
app.include_router(dashboard_router)

# -------------------------------
# Global Exception Handler
# -------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc)
        }
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
