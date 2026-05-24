from pydantic import BaseModel, conint, Field
from typing import List, Optional

class JobCriteriaCreate(BaseModel):
    hr_id: str
    job_desc: str
    min_exp: conint(ge=0)
    skills: List[str]
    department: str
    min_score: conint(ge=0, le=100)

class ResumeRecord(BaseModel):
    hr_id: str
    resume_file: Optional[str]
    resume_storage_path: Optional[str]
    extracted_text: Optional[str]
    experience: float
    skills_score: float
    jd_similarity_score: float
    final_score: float
    status: str = Field(pattern=r"^(Selected|Rejected)$")
    matched_skills: List[str] = []
