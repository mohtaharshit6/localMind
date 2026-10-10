"""
LocalMind Configuration
Loads from environment variables / .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).parent
load_dotenv(_project_root / ".env", override=True)

# ── LLM ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ── Indexing ────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
MAX_CONTEXT_CHUNKS: int = int(os.getenv("MAX_CONTEXT_CHUNKS", "5"))

# ── Paths ───────────────────────────────────────────────────────────────────
DATA_DIR: Path = _project_root / "localmind_data"
DB_PATH: Path = DATA_DIR / "localmind.db"
ACTION_LOG_PATH: Path = DATA_DIR / "action_log.db"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Supported extensions ────────────────────────────────────────────────────
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv"}
