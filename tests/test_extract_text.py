import os
from backend.utils.extract_text import extract_text
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BASE_DIR = os.path.dirname(__file__)

files = [
    "sample.txt",
    "Resume.docx",
    "Jyoti_Gola_Resume.pdf",
]

for file in files:
    path = os.path.join(BASE_DIR, file)
    print("\n============================")
    print("Testing:", file)

    text = extract_text(path)

    print("Text length:", len(text))
    print("Extracted Text:")
    print(text[:3000])   # first 500 chars only
