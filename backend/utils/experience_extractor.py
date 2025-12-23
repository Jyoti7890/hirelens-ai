# backend/utils/experience_extractor.py

import re

# Convert number words to digits
WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15
}

def word_to_number(word: str) -> int:
    return WORD_TO_NUM.get(word.lower(), None)


def extract_experience(text: str) -> float:
    """
    Advanced experience extractor:
    ✔ Detects years + months
    ✔ Converts month → year fraction
    ✔ Detects decimals (1.5 years)
    ✔ Handles ranges (3-5 yrs → returns max)
    ✔ Handles multiple experiences → returns maximum
    ✔ Detects words (five years)
    """

    text = text.lower()
    experience_values = []

    # 1️⃣ Detect "X years Y months"
    combined_pattern = r"(\d+(?:\.\d+)?)\s*years?\s*(\d+)\s*months?"
    match = re.search(combined_pattern, text)
    if match:
        years = float(match.group(1))
        months = int(match.group(2))
        experience_values.append(years + (months / 12))

    # 2️⃣ Detect ranges "3–5 years" → pick max
    range_pattern = r"(\d+)\s*[-to]+\s*(\d+)\s*years?"
    match = re.search(range_pattern, text)
    if match:
        experience_values.append(float(match.group(2)))

    # 3️⃣ Detect decimal years "1.5 years"
    decimal_pattern = r"(\d+\.\d+)\s*years?"
    for match in re.findall(decimal_pattern, text):
        experience_values.append(float(match))

    # 4️⃣ Detect simple integer years "3 years"
    simple_year_pattern = r"(\d+)\s*years?"
    for match in re.findall(simple_year_pattern, text):
        experience_values.append(float(match))

    # 5️⃣ Detect months only "6 months"
    month_pattern = r"(\d+)\s*months?"
    for match in re.findall(month_pattern, text):
        months = int(match)
        experience_values.append(months / 12)

    # 6️⃣ Detect written number years "five years"
    word_pattern = r"(" + "|".join(WORD_TO_NUM.keys()) + r")\s+years?"
    for match in re.findall(word_pattern, text):
        num = word_to_number(match)
        if num:
            experience_values.append(float(num))

    if not experience_values:
        return 0

    return round(max(experience_values), 2)  # return highest experience found
