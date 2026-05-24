import os

from backend.utils.file_handler import extract_zip
from backend.utils.extract_text import extract_text
from backend.utils.experience_extractor import extract_experience
from backend.utils.skill_matcher import calculate_skill_score

# ----------------------------
# REQUIRED SKILLS (HR INPUT)
# ----------------------------
REQUIRED_SKILLS = [
    "Python",
    "SQL",
    "Excel",
    "Power BI",
    "Machine Learning"
]

# ----------------------------
# LOAD ZIP FILE
# ----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_PATH = os.path.join(BASE_DIR, "tests", "samples", "resumes.zip")

print("\n=========== FULL RESUME SCREENING PIPELINE TEST ===========\n")

if not os.path.exists(ZIP_PATH):
    print("❌ ZIP file not found")
    exit()

# ----------------------------
# READ ZIP BYTES
# ----------------------------
with open(ZIP_PATH, "rb") as f:
    zip_bytes = f.read()

# ----------------------------
# STEP 1: Extract resumes from ZIP
# ----------------------------
try:
    resume_files = extract_zip(zip_bytes)
    print(f"📂 Extracted {len(resume_files)} resumes\n")
except Exception as e:
    print(f"🔥 ZIP Extraction Failed: {e}")
    exit()

# ----------------------------
# STEP 2: Process each resume
# ----------------------------
for idx, resume_path in enumerate(resume_files, start=1):
    print(f"================ RESUME {idx} =================")
    print(f"FILE: {os.path.basename(resume_path)}")

    try:
        # Text Extraction
        text = extract_text(resume_path)
        print(f"📝 Text Length: {len(text)}")

        if not text.strip():
            print("⚠️ Empty text — skipping\n")
            continue

        # Experience
        experience = extract_experience(text)
        print(f"⏳ Experience: {experience} years")

        # Skill Matching
        skill_result = calculate_skill_score(text, REQUIRED_SKILLS)
        print(f"🧠 Matched Skills: {skill_result['matched_skills']}")
        print(f"📊 Skill Score: {skill_result['score']}%")

        print("✅ Resume processed successfully\n")

    except Exception as e:
        print(f"🔥 Error processing resume: {e}\n")
