import re
from collections import Counter
try:
    from rapidfuzz import fuzz as rfuzz
    def partial_ratio(a, b): return rfuzz.partial_ratio(a, b)
except Exception:
    from fuzzywuzzy import fuzz
    def partial_ratio(a, b): return fuzz.partial_ratio(a, b)

# ---------------- Skill Synonyms ----------------

SKILL_SYNONYMS = {
    "machine learning": ["ml", "machine-learning", "ml algorithms"],
    "natural language processing": ["nlp", "text mining", "language models"],
    "deep learning": ["dl", "neural networks"],
    "javascript": ["js", "java script"],
    "power bi": ["powerbi", "power-bi"],
    "data analysis": ["data analytics", "analysis of data"],
    "excel": ["msexcel", "advanced excel"],
    "sql": ["mysql", "postgres", "structured query language"],
}

# ---------------- Skill Weights ----------------
# HR critical skills → higher weight

SKILL_WEIGHTS = {
    "machine learning": 1.5,
    "deep learning": 1.4,
    "natural language processing": 1.4,
    "sql": 1.2,
    "power bi": 1.2,
}

DEFAULT_WEIGHT = 1.0

# ---------------- Text Normalizer ----------------

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ---------------- Negative Meaning ----------------

NEGATIVE_PATTERNS = [
    r"no experience in\s+{}",
    r"not familiar with\s+{}",
    r"never worked on\s+{}",
    r"avoid\s+{}",
]

def has_negative_context(text: str, skill: str) -> bool:
    for pattern in NEGATIVE_PATTERNS:
        if re.search(pattern.format(re.escape(skill)), text):
            return True
    return False

# ---------------- Main Skill Scorer ----------------

def calculate_skill_score(text: str, required_skills: list) -> dict:
    """
    ADVANCED Skill Matching Engine
    ✔ weighted scoring
    ✔ frequency impact
    ✔ synonym & fuzzy match
    ✔ negative context handling
    ✔ explainable output
    """

    if not text or not required_skills:
        return {
            "matched_skills": [],
            "missing_skills": required_skills,
            "score": 0.0,
            "details": {}
        }

    text_clean = normalize_text(text)
    text_clean = text_clean[:8000]
    word_freq = Counter(text_clean.split())

    total_weight = 0
    achieved_weight = 0
    details = {}
    matched = set()

    for skill in required_skills:
        skill = skill.lower().strip()
        variants = [skill] + SKILL_SYNONYMS.get(skill, [])
        weight = SKILL_WEIGHTS.get(skill, DEFAULT_WEIGHT)
        total_weight += weight

        # ❌ Negative context → zero
        if has_negative_context(text_clean, skill):
            details[skill] = {
                "matched": False,
                "reason": "negative_context",
                "contribution": 0
            }
            continue

        confidence = 0

        # ✅ Exact / Synonym match via compiled regex
        escaped = [re.escape(v) for v in variants]
        pattern = re.compile(r"\b(?:%s)\b" % "|".join(escaped))
        if pattern.search(text_clean):
            confidence = max(confidence, 0.7)

        # ✅ Fuzzy phrase match (only if exact not found)
        if confidence == 0 and partial_ratio(skill, text_clean) >= 85:
            confidence = max(confidence, 0.85)

        # ✅ Frequency bonus
        freq = sum(word_freq.get(w, 0) for w in skill.split())
        if freq >= 3:
            confidence = min(confidence + 0.15, 1.0)

        contribution = round(confidence * weight, 2)

        if confidence > 0:
            matched.add(skill)
            achieved_weight += contribution

        details[skill] = {
            "matched": confidence > 0,
            "confidence": round(confidence, 2),
            "weight": weight,
            "contribution": contribution
        }

    final_score = (achieved_weight / total_weight) * 100 if total_weight else 0

    return {
        "matched_skills": sorted(list(matched)),
        "missing_skills": sorted(set(required_skills) - matched),
        "score": round(final_score, 2),
        "details": details
    }
