from backend.utils.skill_matcher import calculate_skill_score

resume_text = """
Experienced Data Analyst with 5 years of experience.
Strong skills in Python, SQL, Excel, Power BI.
Worked on data analytics, dashboards and reporting.
No experience in machine learning.
"""

required_skills = [
    "python",
    "sql",
    "excel",
    "power bi",
    "machine learning"
]

print("\n=========== SKILL MATCHER TEST ===========\n")

result = calculate_skill_score(resume_text, required_skills)

print("Matched Skills:", result["matched_skills"])
print("Skill Score:", result["score"])
