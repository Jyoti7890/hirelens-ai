from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from backend.supabase_client import supabase
from backend.utils.supabase_storage import get_signed_url, download_bytes
from zipfile import ZipFile
from collections import Counter
import tempfile
import requests
import os
from io import BytesIO
import logging

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
logger = logging.getLogger("hirelens")

@router.get("/analytics")
def dashboard_analytics(hr_id: str = Query(...)):
    """
    Fetch comprehensive analytics for a specific HR.
    """
    try:
        # Fetch all resumes for this HR
        res = (
            supabase
            .table("resumes")
            .select("status,final_score,jd_similarity_score,matched_skills")
            .eq("hr_id", hr_id)
            .execute()
        )
        
        data = res.data or []
        total = len(data)
        
        if total == 0:
            return {
                "summary": {
                    "total": 0,
                    "selected": 0,
                    "rejected": 0,
                    "avg_score": 0
                },
                "charts": {
                    "status_distribution": {"selected": 0, "rejected": 0, "pending": 0},
                    "avg_jd_match": 0,
                    "top_skills": []
                }
            }

        # Calculate Status Counts
        statuses = [str(r.get("status", "")).lower() for r in data]
        selected_count = statuses.count("selected")
        rejected_count = statuses.count("rejected")
        pending_count = total - selected_count - rejected_count

        # Calculate Averages
        total_score = sum([float(r.get("final_score", 0) or 0) for r in data])
        avg_score = round(total_score / total, 1) if total > 0 else 0

        total_jd_match = sum([float(r.get("jd_similarity_score", 0) or 0) for r in data])
        avg_jd_match = round(total_jd_match / total, 1) if total > 0 else 0

        # Skill Distribution
        all_skills = []
        for r in data:
            skills = r.get("matched_skills", [])
            if isinstance(skills, list):
                all_skills.extend(skills)
            elif isinstance(skills, str):
                all_skills.extend([s.strip() for s in skills.split(",") if s.strip()])
        
        skill_counts = Counter(all_skills).most_common(5)
        top_skills = [{"skill": s, "count": c} for s, c in skill_counts]

        return {
            "summary": {
                "total": total,
                "selected": selected_count,
                "rejected": rejected_count,
                "avg_score": avg_score
            },
            "charts": {
                "status_distribution": {
                    "selected": selected_count,
                    "rejected": rejected_count,
                    "pending": pending_count
                },
                "avg_jd_match": avg_jd_match,
                "top_skills": top_skills
            }
        }

    except Exception as e:
        logger.error(f"Analytics Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")

@router.get("/summary")
def dashboard_summary(hr_id: str = Query(...)):
    res = (
        supabase
        .table("resumes")
        .select("status")
        .eq("hr_id", hr_id)
        .execute()
    )
    if not res.data:
        return {"total_resumes": 0, "selected_resumes": 0, "rejected_resumes": 0, "pending_resumes": 0}
    total = len(res.data)
    selected = len([r for r in res.data if str(r.get("status", "")).lower() == "selected"])
    rejected = len([r for r in res.data if str(r.get("status", "")).lower() == "rejected"])
    pending = len([r for r in res.data if str(r.get("status", "")).lower() == "pending"])
    return {
        "total_resumes": total,
        "selected_resumes": selected,
        "rejected_resumes": rejected,
        "pending_resumes": pending
    }

@router.get("/top-resumes")
def top_resumes(hr_id: str = Query(...)):
    res = (
        supabase
        .table("resumes")
        .select("resume_file,experience,skills_score,jd_similarity_score,final_score,matched_skills,missing_skills,status")
        .eq("hr_id", hr_id)
        .in_("status", ["Selected", "SELECTED"])
        .order("final_score", desc=True)
        .execute()
    )
    return res.data or []

@router.get("/download-pending")
def download_pending_resumes(hr_id: str = Query(...)):
    res = (
        supabase
        .table("resumes")
        .select("resume_storage_path")
        .eq("hr_id", hr_id)
        .eq("status", "PENDING")
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="No pending resumes")

    mem_zip = BytesIO()
    with ZipFile(mem_zip, "w") as zipf:
        for idx, item in enumerate(res.data):
            path = item.get("resume_storage_path")
            if not path:
                continue
            file_data = download_bytes(path)
            if not file_data:
                logger.warning(f"Download failed for path: {path}")
                continue
            zipf.writestr(f"pending_{idx+1}{os.path.splitext(path)[1]}", file_data)
    mem_zip.seek(0)
    return StreamingResponse(mem_zip, media_type="application/zip", headers={
        "Content-Disposition": "attachment; filename=pending_resumes.zip"
    })

@router.get("/download-selected")
def download_selected_resumes(hr_id: str = Query(...)):
    res = (
        supabase
        .table("resumes")
        .select("resume_storage_path")
        .eq("hr_id", hr_id)
        .eq("status", "Selected")
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="No selected resumes")

    mem_zip = BytesIO()
    with ZipFile(mem_zip, "w") as zipf:
        for idx, item in enumerate(res.data):
            path = item.get("resume_storage_path")
            if not path:
                continue
            file_data = download_bytes(path)
            if not file_data:
                logger.warning(f"Download failed for path: {path}")
                continue
            zipf.writestr(f"resume_{idx+1}{os.path.splitext(path)[1]}", file_data)
    mem_zip.seek(0)
    return StreamingResponse(mem_zip, media_type="application/zip", headers={
        "Content-Disposition": "attachment; filename=selected_resumes.zip"
    })

@router.get("/download-rejected")
def download_rejected_resumes(hr_id: str = Query(...)):
    res = (
        supabase
        .table("resumes")
        .select("resume_storage_path")
        .eq("hr_id", hr_id)
        .eq("status", "Rejected")
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="No rejected resumes available for download.")

    mem_zip = BytesIO()
    with ZipFile(mem_zip, "w") as zipf:
        for idx, item in enumerate(res.data):
            path = item.get("resume_storage_path")
            if not path:
                continue
            file_data = download_bytes(path)
            if not file_data:
                logger.warning(f"Download failed for path: {path}")
                continue
            ext = os.path.splitext(path)[1]
            zipf.writestr(f"rejected_{idx+1}{ext}", file_data)
    mem_zip.seek(0)
    return StreamingResponse(mem_zip, media_type="application/zip", headers={
        "Content-Disposition": "attachment; filename=rejected_resumes.zip"
    })
