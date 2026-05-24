
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def jd_resume_similarity_original(job_desc: str, resume_text: str):
    job = _clean_text(job_desc)
    res = _clean_text(resume_text)
    if not job or not res:
        return 0.0, 0.0
    # Original problematic parameters
    vect = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95)
    try:
        tfidf = vect.fit_transform([job, res])
        sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        score_0_100 = round(sim * 100, 2)
        return sim, score_0_100
    except ValueError:
        return 0.0, 0.0

def jd_resume_similarity_fixed(job_desc: str, resume_text: str):
    job = _clean_text(job_desc)
    res = _clean_text(resume_text)
    
    # Defensive check: ensure meaningful text length
    if not job or len(job) < 10 or not res or len(res) < 10:
        return 0.0, 0.0

    # Refactored: removed max_df, added sublinear_tf for stability
    # max_df=0.95 with 2 docs excludes words present in both (100% freq), resulting in 0 similarity
    vect = TfidfVectorizer(
        ngram_range=(1, 2), 
        min_df=1, 
        norm='l2', 
        use_idf=True, 
        smooth_idf=True, 
        sublinear_tf=True  # Log scaling for stability
    )
    
    try:
        tfidf = vect.fit_transform([job, res])
        sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        score_0_100 = round(sim * 100, 2)
        return sim, score_0_100
    except ValueError:
        # Handle empty vocabulary case
        return 0.0, 0.0

jd = "We are looking for a software engineer with python and sql skills"
resume = "I am a software engineer with 5 years of experience in python and sql"

print(f"Original: {jd_resume_similarity_original(jd, resume)}")
print(f"Fixed:    {jd_resume_similarity_fixed(jd, resume)}")
