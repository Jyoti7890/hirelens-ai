from backend.supabase_client import supabase
import uuid
import os
import re
import unicodedata
from typing import Optional
import logging

BUCKET_NAME = "resumes"
logger = logging.getLogger("hirelens")

# ---------------------------
# Upload Resume to Bucket
# ---------------------------
def _sanitize_filename(file_name: str) -> str:
    name = file_name or "file"
    name = name.replace("’", "'").replace("“", '"').replace("”", '"')
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    base, ext = os.path.splitext(name)
    base = base.lower()
    ext = ext.lower()
    base = re.sub(r"\s+", "_", base)
    base = re.sub(r"[^a-z0-9._-]", "", base)
    if not base:
        base = "file"
    if not ext:
        ext = ""
    return f"{base}{ext}"

def upload_resume(file_bytes: bytes, file_name: str) -> Optional[str]:
    """
    Uploads resume to Supabase Storage bucket safely.

    Returns:
        file_path (str) if successful
        None if failed
    """

    if not file_bytes:
        raise ValueError("Empty file cannot be uploaded")

    if not file_name:
        raise ValueError("File name is required")

    try:
        safe_name = _sanitize_filename(file_name)
        unique_name = f"{uuid.uuid4()}_{safe_name}"

        response = supabase.storage.from_(BUCKET_NAME).upload(
            path=unique_name,
            file=file_bytes,
            file_options={"content-type": "application/octet-stream"}
        )

        if response is None:
            raise Exception("Supabase upload returned None")

        return unique_name

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return None


# ---------------------------
# Generate Signed URL
# ---------------------------
def get_signed_url(file_path: str, expires_in: int = 3600) -> Optional[str]:
    """
    Generates temporary signed URL for private file access.
    """

    if not file_path:
        raise ValueError("File path required")

    try:
        response = supabase.storage.from_(BUCKET_NAME).create_signed_url(
            file_path, expires_in
        )

        if not response or "signedURL" not in response:
            raise Exception("Signed URL generation failed")

        return response["signedURL"]

    except Exception as e:
        logger.error(f"Signed URL error: {e}")
        return None

def download_bytes(file_path: str) -> Optional[bytes]:
    if not file_path:
        return None
    try:
        return supabase.storage.from_(BUCKET_NAME).download(file_path)
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return None


# ---------------------------
# Delete Resume
# ---------------------------
def delete_resume(file_path: str) -> bool:
    """
    Deletes file from Supabase bucket safely.
    """

    if not file_path:
        return False

    try:
        supabase.storage.from_(BUCKET_NAME).remove([file_path])
        return True

    except Exception as e:
        logger.error(f"Delete failed: {e}")
        return False
