import os

ALLOWED_EXTENSIONS = [
    ".pdf",
    ".docx",
    ".jpg",
    ".png"
]

def allowed_file(filename):
    ext = os.path.splitext(filename)[1]
    return ext.lower() in ALLOWED_EXTENSIONS
