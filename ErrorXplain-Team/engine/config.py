"""
Centralized application configuration.

Every tunable value (URLs, model names, timeouts, limits, paths, CORS
origins, the Groq API key) lives here and is read from environment
variables, so nothing sensitive or environment-specific is hardcoded
anywhere else in the application.

Values are loaded from a `.env` file (via python-dotenv) if one is
present, falling back to real environment variables, then to the
defaults below. See `.env.example` for every variable this app reads.
"""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Load variables from a .env file in the current working directory (or
# nearest parent) if one exists. Safe to call even with no .env file -
# real environment variables always take priority over the file.
load_dotenv()

# Root of the engine/ package - used to resolve default relative paths.
BASE_DIR = Path(__file__).resolve().parent


def _get_bool(name: str, default: bool) -> bool:
    """Read a boolean-ish environment variable ('true'/'1'/'yes'/'on')."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _get_float(name: str, default: float) -> float:
    """Read a float environment variable, falling back to default on any issue."""
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _get_int(name: str, default: int) -> int:
    """Read an int environment variable, falling back to default on any issue."""
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_list(name: str, default: List[str]) -> List[str]:
    """Read a comma-separated environment variable into a list of strings."""
    raw = os.getenv(name)
    if not raw or not raw.strip():
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings:
    """
    Application settings, populated once from the environment at import
    time. Treat this as read-only after startup.
    """

    # --- App / server ---
    APP_NAME: str = os.getenv("APP_NAME", "ErrorXplain Engine")
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = _get_int("PORT", 8000)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # --- CORS ---
    CORS_ORIGINS: List[str] = _get_list(
        "CORS_ORIGINS",
        ["http://localhost", "http://127.0.0.1", "http://localhost:3000"],
    )

    # --- Rules ---
    # Defaults to <project_root>/rules (one level above engine/), matching
    # the existing repo layout: engine/ and rules/ are siblings.
    RULES_DIR: Path = Path(
        os.getenv("RULES_DIR", str(BASE_DIR.parent / "rules"))
    ).resolve()

    # --- Request limits (used for validation + AI sanitization) ---
    MAX_ERROR_MESSAGE_LENGTH: int = _get_int("MAX_ERROR_MESSAGE_LENGTH", 4000)
    MAX_SOURCE_CODE_LENGTH: int = _get_int("MAX_SOURCE_CODE_LENGTH", 2000)

    # --- Groq AI ---
    # Master switch: even with a key present, AI is off unless this is true.
    AI_ENABLED: bool = _get_bool("AI_ENABLED", True)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_API_URL: str = os.getenv(
        "GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions"
    )
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    AI_TIMEOUT_SECONDS: float = _get_float("AI_TIMEOUT_SECONDS", 10.0)
    AI_MAX_TOKENS: int = _get_int("AI_MAX_TOKENS", 300)
    AI_TEMPERATURE: float = _get_float("AI_TEMPERATURE", 0.3)
    # How long an identical (language, error_message) AI result is reused.
    AI_CACHE_TTL_SECONDS: int = _get_int("AI_CACHE_TTL_SECONDS", 300)  # 5 minutes


settings = Settings()
