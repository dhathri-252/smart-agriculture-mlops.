"""Environment-driven configuration for the Smart Agriculture API.

All secrets are read from environment variables only — nothing sensitive is
ever hard-coded. Every value is read lazily (at call time) so tests can
override environment variables without restarting the process.
"""

import os
import secrets
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Ephemeral secret used when AUTH_SECRET_KEY is not set. Generated once per
# process; a warning is logged at startup so operators know sessions will not
# survive a restart until a stable secret is configured.
_EPHEMERAL_SECRET: str = secrets.token_hex(32)
_EPHEMERAL_SECRET_WARNED = False


def get_db_path() -> Path:
    """SQLite database location (override with APP_DB_PATH)."""
    raw = os.environ.get("APP_DB_PATH", "").strip()
    if raw:
        return Path(raw)
    return PROJECT_ROOT / "data" / "app.db"


def get_cors_origins() -> list:
    raw = os.environ.get("CORS_ALLOW_ORIGINS", "")
    extras = [o.strip() for o in raw.split(",") if o.strip()]
    defaults = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # Local dev hostname (http://smart-agriculture:5173).
        # Requires a hosts-file entry mapping smart-agriculture -> 127.0.0.1.
        "http://smart-agriculture:5173",
    ]
    seen, origins = set(), []
    for origin in defaults + extras:
        if origin not in seen:
            seen.add(origin)
            origins.append(origin)
    return origins


def get_auth_secret() -> str:
    raw = os.environ.get("AUTH_SECRET_KEY", "").strip()
    if raw:
        return raw
    global _EPHEMERAL_SECRET_WARNED
    if not _EPHEMERAL_SECRET_WARNED:
        import logging

        logging.getLogger("api").warning(
            "AUTH_SECRET_KEY is not set — using an ephemeral secret. "
            "Sessions will be invalidated on restart. Set AUTH_SECRET_KEY in production."
        )
        _EPHEMERAL_SECRET_WARNED = True
    return _EPHEMERAL_SECRET


def get_token_ttl_seconds() -> int:
    try:
        return max(300, int(os.environ.get("AUTH_TOKEN_TTL_SECONDS", "86400")))
    except ValueError:
        return 86400


def get_admin_token() -> str:
    return os.environ.get("ADMIN_TOKEN", "").strip()


def get_weather_api_key() -> str:
    return os.environ.get("WEATHER_API_KEY", "").strip()


def get_weather_provider() -> str:
    """'openweathermap' when a key is configured, otherwise 'none'."""
    provider = os.environ.get("WEATHER_PROVIDER", "").strip().lower()
    if provider:
        return provider
    return "openweathermap" if get_weather_api_key() else "none"


def get_ai_provider() -> str:
    """'openai' when explicitly requested AND a key exists, otherwise 'knowledge_base'."""
    provider = os.environ.get("AI_PROVIDER", "").strip().lower()
    if provider in ("knowledge_base", "kb", "none"):
        return "knowledge_base"
    if provider in ("openai", "auto", ""):
        if get_openai_api_key():
            return "openai"
        return "knowledge_base"
    return "knowledge_base"


def get_openai_api_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "").strip()


def get_openai_base_url() -> str:
    raw = os.environ.get("OPENAI_BASE_URL", "").strip().rstrip("/")
    return raw or "https://api.openai.com/v1"


def get_openai_model() -> str:
    return os.environ.get("OPENAI_MODEL", "").strip() or "gpt-4o-mini"


def get_openai_timeout_seconds() -> int:
    """Provider request timeout in seconds (OPENAI_TIMEOUT_SECONDS, 5..60)."""
    try:
        return max(5, min(60, int(os.environ.get("OPENAI_TIMEOUT_SECONDS", "20"))))
    except ValueError:
        return 20
