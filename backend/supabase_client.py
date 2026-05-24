from supabase import create_client
from backend.config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_ROLE_KEY
import logging

logger = logging.getLogger("hirelens")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase configuration missing.")

try:
    # Standard client for interacting as anon/authenticated user
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Admin client for user management (reset password without old password)
    # Using Key as Service Key fallback if not explicitly set, but requires actual service role key for admin tasks
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY)
    
    logger.info("Supabase clients initialized")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    raise RuntimeError("Supabase client initialization failed")
