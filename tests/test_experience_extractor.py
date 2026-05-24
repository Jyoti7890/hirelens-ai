# tests/test_experience_extractor.py

from backend.utils.experience_extractor import extract_experience

test_cases = [
    "I have 3 years of experience",
    "Worked for 2 years 6 months in data analytics",
    "Experience: 1.5 years in Python",
    "Total experience is 3-5 years",
    "I have six years experience in software development",
    "Worked for 8 months as intern",
    "No experience mentioned here"
]

print("\n======= EXPERIENCE EXTRACTION TEST =======\n")

for text in test_cases:
    exp = extract_experience(text)
    print(f"TEXT: {text}")
    print(f"EXTRACTED EXPERIENCE: {exp} years\n")
