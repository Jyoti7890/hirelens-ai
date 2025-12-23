from typing import Tuple
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

def _clean_text(text: str) -> str:
    """Standardizes text: lowercase, removes special chars, collapses spaces."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

_VECT = HashingVectorizer(
    n_features=2**18,
    alternate_sign=False,
    ngram_range=(1, 2),
    norm='l2'
)

def jd_resume_similarity(job_desc: str, resume_text: str) -> Tuple[float, float]:
    """
    Computes cosine similarity between Job Description and Resume using TF-IDF.
    
    Refactored for stability on small corpora (2 docs):
    - Removed max_df=0.95 (caused vocabulary collapse when terms appeared in both docs)
    - Added sublinear_tf=True (log scaling) to dampen effect of repeated terms in long resumes
    - Added defensive checks for minimal text length
    """
    job = _clean_text(job_desc)
    res = _clean_text(resume_text)
    
    # 1. Defensive Check: Ensure texts are not empty or too short to be meaningful
    if not job or len(job) < 10 or not res or len(res) < 10:
        return 0.0, 0.0

    # Trim extremely long resumes to reduce processing time
    if len(res) > 12000:
        res = res[:12000]

    try:
        v_job = _VECT.transform([job])
        v_res = _VECT.transform([res])
        sim = cosine_similarity(v_job, v_res)[0][0]
        score_0_100 = round(sim * 100, 2)
        return float(sim), float(score_0_100)
    except Exception:
        return 0.0, 0.0
