from supabase import create_client
from backend.config import SUPABASE_URL, SUPABASE_KEY
import logging
import os

logger = logging.getLogger("hirelens")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase configuration missing. Set SUPABASE_URL and SUPABASE_KEY via environment variables.")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client initialized")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    raise RuntimeError("Supabase client initialization failed")
