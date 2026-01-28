"""
API Configuration - reuses core config but adds API-specific settings.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATA_DIR = Path(__file__).parent.parent / "data"
DATABASE_PATH = DATA_DIR / "shared_database.db"

# API Settings
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))

# CORS - Read from env or use dev defaults
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "")
if CORS_ORIGINS_STR:
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]
else:
    # Development defaults
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

# File uploads
UPLOADS_DIR = DATA_DIR / "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = {
    # Images
    'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp',
    # Documents
    'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt',
    # Spreadsheets
    'xls', 'xlsx', 'csv', 'ods',
    # Presentations
    'ppt', 'pptx', 'odp',
    # Archives
    'zip', 'rar', '7z', 'tar', 'gz',
    # Code
    'py', 'js', 'html', 'css', 'json', 'xml', 'md'
}

# Default user (single-user mode for now)
DEFAULT_USER_ID = 1
