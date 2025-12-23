from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from backend.supabase_client import supabase
from backend.utils.supabase_storage import get_signed_url, download_bytes
from zipfile import ZipFile
import tempfile
import requests
import os
from io import BytesIO
import logging

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
logger = logging.getLogger("hirelens")

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
