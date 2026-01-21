"""
Centralized configuration and constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
DATA_DIR = Path("data")
UPLOADS_DIR = DATA_DIR / "uploads"
LOGS_DIR = Path("logs")
DATABASE_PATH = DATA_DIR / "shared_database.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database
DB_TIMEOUT = 30  # seconds

# File uploads
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = {'jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'}

# Notifications
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "app.log"

# App settings
APP_NAME = "Personal Knowledge & Task Management"
VERSION = "1.0.0"

# Streamlit config
STREAMLIT_CONFIG = {
    "page_title": APP_NAME,
    "page_icon": "📚",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}
