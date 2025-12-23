from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
from datetime import datetime
import os
import tempfile
import logging

from backend.supabase_client import supabase
from backend.utils.extract_text import extract_text
from backend.utils.experience_extractor import extract_experience
from backend.utils.skill_matcher import calculate_skill_score
from backend.utils.file_handler import extract_zip, ZipValidationError
from backend.utils.supabase_storage import upload_resume, get_signed_url
from backend.utils.nlp_similarity import jd_resume_similarity

router = APIRouter(prefix="/upload", tags=["Resume Upload"])
logger = logging.getLogger("hirelens")

ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt", ".zip"]

def is_valid_file(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

def _parse_skills(skills_str: str) -> List[str]:
    if not skills_str:
        return []
    return [s.strip() for s in skills_str.split(",") if s.strip()]

@router.post("/resumes")
async def upload_resumes(
    hr_id: str = Form(...),
    zip_file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),
):
    if not hr_id or not hr_id.strip():
        raise HTTPException(status_code=400, detail="Missing hr_id")
    if not hr_id or not hr_id.strip():
        raise HTTPException(status_code=400, detail="Missing hr_id")
    criteria_q = (
        supabase
        .table("job_criteria")
        .select("*")
        .eq("hr_id", hr_id)
        .eq("locked", True)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not criteria_q.data or len(criteria_q.data) == 0:
        raise HTTPException(status_code=404, detail="Locked job criteria not found")

    criteria = criteria_q.data[0]
    min_exp = int(criteria.get("min_exp", 0))
    required_skills = _parse_skills(criteria.get("skills", ""))
    min_match_score = int(criteria.get("min_score", 0))
    job_description = criteria.get("job_desc", "")

    processed = []
    total_files = 0
    success_count = 0
    pending_count = 0

    file_inputs: List[UploadFile] = []
    if zip_file:
        file_inputs.append(zip_file)
    if files:
        file_inputs.extend(files)
    if not file_inputs:
        raise HTTPException(status_code=400, detail="No files uploaded")

    for file in file_inputs:
        if not is_valid_file(file.filename):
            raise HTTPException(status_code=400, detail="Upload failed: Only PDF, DOCX, and TXT files are allowed.")
        input_bytes = await file.read()

        resume_paths = []
        if file.filename.lower().endswith(".zip"):
            try:
                resume_paths = extract_zip(input_bytes)
            except ZipValidationError as ve:
                raise HTTPException(status_code=400, detail=str(ve))
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid ZIP file")
        else:
            with tempfile.TemporaryDirectory() as temp_dir:
                fp = os.path.join(temp_dir, file.filename)
                with open(fp, "wb") as f:
                    f.write(input_bytes)
                resume_paths = [fp]

        if len(resume_paths) > 50:
            raise HTTPException(status_code=400, detail="Upload failed: Too many resumes in the ZIP file. Maximum allowed is 50.")

        for resume_path in resume_paths:
            total_files += 1
            original_name = os.path.basename(resume_path)
            storage_path = None
            resume_url = None
            try:
                with open(resume_path, "rb") as rf:
                    file_bytes = rf.read()
                storage_path = upload_resume(file_bytes, original_name)
                if storage_path:
                    try:
                        resume_url = get_signed_url(storage_path, expires_in=24 * 3600)
                    except Exception:
                        resume_url = None
            except Exception as e:
                storage_path = None
                resume_url = None
                logger.error(f"Upload error for {original_name}: {e}")

            try:
                text = extract_text(resume_path)
                experience = extract_experience(text)

                skill_result = calculate_skill_score(text, required_skills)
                skills_score = float(skill_result["score"])
                matched_skills = skill_result["matched_skills"]
                missing_skills = skill_result.get("missing_skills", [])

                _, jd_similarity_score = jd_resume_similarity(job_description, text)

                if min_exp > 0:
                    experience_score = min((experience / min_exp) * 100.0, 100.0)
                else:
                    experience_score = 0.0

                final_score = round(
                    (skills_score * 0.4) +
                    (jd_similarity_score * 0.4) +
                    (experience_score * 0.2),
                    2
                )

                selected = (
                    (experience >= min_exp) and
                    (final_score >= min_match_score) and
                    (skills_score > 30) and
                    (jd_similarity_score >= 5)
                )
                status = "Selected" if selected else "Rejected"

                try:
                    supabase.table("resumes").insert({
                        "hr_id": hr_id,
                        "resume_file": resume_url,
                        "resume_storage_path": storage_path,
                        "extracted_text": text,
                        "experience": experience,
                        "skills_score": skills_score,
                        "jd_similarity_score": jd_similarity_score,
                        "final_score": final_score,
                        "status": status,
                        "matched_skills": matched_skills,
                        "missing_skills": missing_skills,
                        "created_at": datetime.utcnow().isoformat()
                    }).execute()
                    success_count += 1
                except Exception as db_err:
                    logger.error(f"DB insert error for {original_name}: {db_err}")
                    status = "PENDING"
                    pending_count += 1

                processed.append({
                    "file": original_name,
                    "status": status,
                    "experience": experience,
                    "skills_score": skills_score,
                    "jd_similarity_score": jd_similarity_score,
                    "experience_score": round(experience_score, 2),
                    "final_score": final_score,
                    "matched_skills": matched_skills,
                    "missing_skills": missing_skills,
                    "resume_url": resume_url
                })
            except Exception as e:
                logger.error(f"Processing error for {original_name}: {e}")
                try:
                    supabase.table("resumes").insert({
                        "hr_id": hr_id,
                        "resume_file": None,
                        "resume_storage_path": storage_path,
                        "extracted_text": None,
                        "experience": None,
                        "skills_score": None,
                        "jd_similarity_score": None,
                        "final_score": None,
                        "status": "PENDING",
                        "matched_skills": [],
                        "missing_skills": [],
                        "created_at": datetime.utcnow().isoformat()
                    }).execute()
                except Exception as db_err2:
                    logger.error(f"DB insert PENDING error for {original_name}: {db_err2}")
                pending_count += 1
                processed.append({
                    "file": original_name,
                    "status": "PENDING",
                    "resume_url": resume_url
                })

    return {
        "message": "Resumes processed",
        "total_files": total_files,
        "success_count": success_count,
        "pending_count": pending_count,
        "results": processed
    }
