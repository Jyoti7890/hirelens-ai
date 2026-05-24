# backend/utils/file_handler.py

import zipfile
import os
import uuid
from pathlib import Path
import shutil

TEMP_FOLDER = Path("temp_resumes")
TEMP_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXT = (".pdf", ".docx", ".txt")
MAX_FILES = 50
MAX_ZIP_SIZE_MB = 50
MAX_EXTRACT_SIZE_MB = 50


class ZipValidationError(Exception):
    """Custom exception for ZIP validation issues"""
    pass


def safe_extract(zip_ref, extract_path):
    """
    Protect from path traversal attack.
    """
    for member in zip_ref.namelist():
        member_path = extract_path / member
        if not str(member_path.resolve()).startswith(str(extract_path.resolve())):
            raise ZipValidationError("Unsafe ZIP file detected (path traversal)")
        zip_ref.extract(member, extract_path)


def extract_zip(file_bytes) -> list:
    """
    SAFE zip extraction.
    Returns list of valid resume file paths.
    """

    folder_name = None

    try:
        # ---- 1. Validate ZIP size ----
        if not file_bytes:
            raise ZipValidationError("Empty ZIP file uploaded")

        if len(file_bytes) > MAX_ZIP_SIZE_MB * 1024 * 1024:
            raise ZipValidationError("Upload failed: ZIP file size exceeds the allowed limit.")

        # ---- 2. Create temp folder ----
        folder_name = TEMP_FOLDER / str(uuid.uuid4())
        folder_name.mkdir(parents=True, exist_ok=True)

        # ---- 3. Save ZIP ----
        zip_path = folder_name / "uploaded.zip"
        with open(zip_path, "wb") as f:
            f.write(file_bytes)

        # ---- 4. Extract safely ----
        extracted_files = []

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:

                # Prevent ZIP bomb
                total_uncompressed = sum(
                    z.file_size for z in zip_ref.infolist()
                )

                if total_uncompressed > MAX_EXTRACT_SIZE_MB * 1024 * 1024:
                    raise ZipValidationError(
                        "ZIP bomb detected (extracted size too large)"
                    )

                # Prevent too many files
                if len(zip_ref.infolist()) > MAX_FILES:
                    raise ZipValidationError("Upload failed: Too many resumes in the ZIP file. Maximum allowed is 50.")

                # Secure extraction
                safe_extract(zip_ref, folder_name)

        except zipfile.BadZipFile:
            raise ZipValidationError("Invalid or corrupted ZIP file")

        # ---- 5. Collect allowed resume files ----
        for root, _, files in os.walk(folder_name):
            for file in files:
                if file.lower().endswith(ALLOWED_EXT):
                    extracted_files.append(os.path.join(root, file))

        if not extracted_files:
            raise ZipValidationError("No valid resume files found (.pdf, .docx, .txt)")

        return extracted_files

    except Exception as e:
        # Cleanup on failure
        if folder_name and folder_name.exists():
            shutil.rmtree(folder_name, ignore_errors=True)
        raise e
