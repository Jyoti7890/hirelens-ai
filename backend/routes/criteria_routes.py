from fastapi import APIRouter, Form, HTTPException
from datetime import datetime
from backend.supabase_client import supabase
import logging

router = APIRouter(prefix="/criteria", tags=["Job Criteria"])
logger = logging.getLogger("hirelens")

@router.post("/save")
def save_criteria(
    hr_id: str = Form(...),
    job_desc: str = Form(...),
    min_exp: int = Form(...),
    skills: str = Form(...),
    department: str = Form(...),
    min_score: int = Form(...),
):
    data = {
        "hr_id": hr_id,
        "job_desc": job_desc,
        "min_exp": min_exp,
        "skills": skills,
        "department": department,
        "min_score": min_score,
        "locked": True,
        "created_at": datetime.utcnow().isoformat(),
    }

    try:
        supabase.table("job_criteria").insert(data).execute()
        return {"status": "success", "message": "Criteria saved and locked", "data": data}
    except Exception as e:
        logger.error(f"Criteria save DB error: {e}")
        raise HTTPException(status_code=500, detail="DB Error")
