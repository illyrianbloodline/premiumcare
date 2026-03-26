import os
from dotenv import load_dotenv

# Load variables from a .env file if it exists
load_dotenv()

# -------------------------------------------------------
#  MedPlatform Configuration
# -------------------------------------------------------

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "medplatform"),
    "user":     os.getenv("DB_USER", "medplatform_user"),
    "password": os.getenv("DB_PASSWORD", "admin123"),  # Change in .env!
}

# Security Keys
SECRET_KEY = os.getenv("SECRET_KEY", "7f3a9c2d1e4b5a6c8f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2")
import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDc9zNtRjty09M2z5I6KgSYFoWQvRy722w")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# File Handling
UPLOAD_FOLDER  = "uploads"
MAX_UPLOAD_MB  = 20
PRACTICE_NAME  = "Medical Practice"

# Geofencing: restrict PHI access to these IP prefixes (empty = allow all)
# Example: ["192.168.1.", "10.0.0."]
ALLOWED_IPS    = []

# Email / SMTP (for sending patient reports)
SMTP_HOST     = 'smtp.gmail.com'
SMTP_PORT     = 587
SMTP_USER     = ''   # your Gmail or SMTP username
SMTP_PASSWORD = ''   # your app password
SMTP_FROM     = ''   # sender address shown to patient
 