"""
Configuration settings for the Data Cleaning System.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# ============================================================================
# PATHS
# ============================================================================
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
EXPORTS_DIR = DATA_DIR / "exports"
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "data_cleaning.db"

# Create directories if they don't exist
for directory in [UPLOADS_DIR, EXPORTS_DIR, DATABASE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# GEMINI API CONFIGURATION
# ============================================================================
# Get API key from environment variable
# You can set this in a .env file or as an environment variable:
# Windows: set GEMINI_API_KEY=your_key_here
# Linux/Mac: export GEMINI_API_KEY=your_key_here
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Model to use for rule parsing
GEMINI_MODEL = "gemini-2.0-flash"

# Whether to use AI parsing (set to False to always use pattern-based)
USE_AI_PARSING = True

# ============================================================================
# DATA CLEANING SETTINGS
# ============================================================================
# Maximum file size for CSV upload (in MB)
MAX_FILE_SIZE_MB = 100

# Default encoding for CSV files
DEFAULT_ENCODING = "utf-8"

# Backup encodings to try if default fails
FALLBACK_ENCODINGS = ["latin-1", "cp1252", "iso-8859-1"]
