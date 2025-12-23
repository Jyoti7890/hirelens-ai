import os
from backend.utils.supabase_storage import (
    upload_resume,
    get_signed_url,
    delete_resume
)

print("\n=========== SUPABASE STORAGE TEST ===========\n")

# ---------------------------
# SAMPLE FILE
# ---------------------------
sample_text = b"This is a test resume for Supabase upload."
file_name = "test_resume.txt"

# ---------------------------
# 1️⃣ UPLOAD TEST
# ---------------------------
print("🔼 Uploading file...")

file_path = upload_resume(sample_text, file_name)

if not file_path:
    print("❌ Upload failed")
    exit()

print(f"✅ Uploaded successfully")
print(f"📁 File Path: {file_path}\n")

# ---------------------------
# 2️⃣ SIGNED URL TEST
# ---------------------------
print("🔗 Generating signed URL...")

signed_url = get_signed_url(file_path)

if not signed_url:
    print("❌ Signed URL generation failed")
    exit()

print("✅ Signed URL generated")
print(f"🌐 URL: {signed_url}\n")

# ---------------------------
# 3️⃣ DELETE TEST
# ---------------------------
print("🗑 Deleting file...")

deleted = delete_resume(file_path)

if deleted:
    print("✅ File deleted successfully")
else:
    print("❌ File deletion failed")

print("\n=========== TEST COMPLETED ===========\n")
