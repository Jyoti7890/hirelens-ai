import os
from backend.utils.extract_text import extract_text
from backend.utils.experience_extractor import extract_experience
from backend.utils.skill_matcher import calculate_skill_score

# ---------------- CONFIG ----------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_DIR = os.path.join(BASE_DIR, "tests", "samples")

TEST_FILES = [
    "sample.txt",
    "Resume.docx",
    "Jyoti_Gola_Resume.pdf",
]

# Skills HR is looking for (normally comes from input.html)
REQUIRED_SKILLS = [
    "python",
    "sql",
    "excel",
    "power bi",
    "machine learning"
]

# ---------------- TEST ----------------

print("\n=========== RESUME → EXPERIENCE → SKILLS PIPELINE TEST ===========\n")

for file_name in TEST_FILES:
    file_path = os.path.join(SAMPLES_DIR, file_name)
    print(f"FILE: {file_name}")

    if not os.path.exists(file_path):
        print(f"❌ File not found at {file_path}\n")
        continue

    try:
        # 1️⃣ Extract text
        text = extract_text(file_path)
        print(f"Extracted Text Length: {len(text)}")

        if not text.strip():
            print("⚠️ No text extracted\n")
            continue

        # 2️⃣ Extract experience
        experience = extract_experience(text)
        print(f"Extracted Experience: {experience} years")

        # 3️⃣ Extract skills + score
        skill_result = calculate_skill_score(text, REQUIRED_SKILLS)
        print(f"Matched Skills: {skill_result['matched_skills']}")
        print(f"Skill Score: {skill_result['score']}%\n")

    except Exception as e:
        print(f"🔥 ERROR while processing file: {e}\n")
