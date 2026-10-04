"""Central configuration. Everything reads from environment variables / .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
load_dotenv(BASE_DIR / ".env")

PLACEHOLDER_KEYS = {"", "your_groq_api_key_here"}


def _int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _db_path():
    path = Path(os.getenv("DATABASE_PATH", "database/companion.db"))
    if not path.is_absolute():
        path = BASE_DIR / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change_this_secret_key")
    DATABASE_PATH = _db_path()

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
    GROQ_REASONING_EFFORT = os.getenv("GROQ_REASONING_EFFORT", "low").strip().lower()
    GROQ_TIMEOUT = _int("GROQ_TIMEOUT", 60)
    GROQ_MAX_TOKENS = _int("GROQ_MAX_TOKENS", 4096)

    CORS_ORIGINS = [o.strip() for o in os.getenv(
        "CORS_ORIGINS", "http://localhost:5000,http://127.0.0.1:5000").split(",") if o.strip()]
    COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"
    PORT = _int("PORT", 5000)
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    MAX_CONTENT_LENGTH = 256 * 1024          # request size limit
    MAX_MESSAGE_CHARS = 8000
    CONTEXT_MESSAGES = 24                    # recent messages sent to the model
    CONTEXT_CHAR_BUDGET = 14000              # hard cap on history size
    RELEVANT_MEMORIES = 8                    # memories injected per reply
    MAX_MEMORIES_PER_USER = 200

    MODES = ("friend", "mentor", "study", "coding", "idea", "fun", "think")
    TONES = ("auto", "casual", "professional", "educational", "motivational", "technical", "fun")

    @classmethod
    def ai_configured(cls):
        return cls.GROQ_API_KEY not in PLACEHOLDER_KEYS
