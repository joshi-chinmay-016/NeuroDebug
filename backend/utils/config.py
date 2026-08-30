"""Configuration management for NeuroDebug."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Search and load .env from backend directory, parent workspace, and CWD
_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env")
load_dotenv(_backend_dir.parent / ".env")
load_dotenv()


class Config:
    """Application configuration."""

    # Groq API Configuration
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")

    # Application Configuration
    APP_NAME: str = "NeuroDebug API"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # API Configuration
    MAX_CODE_LENGTH: int = 10000
    REQUEST_TIMEOUT: int = 30

    # Database Configuration
    @staticmethod
    def _get_database_url() -> str:
        # Check all standard cloud database environment variables
        raw = (
            os.getenv("DATABASE_URL")
            or os.getenv("DATABASE_PRIVATE_URL")
            or os.getenv("DATABASE_PUBLIC_URL")
            or os.getenv("POSTGRES_URL")
            or os.getenv("POSTGRESQL_URL")
            or os.getenv("SUPABASE_DATABASE_URL")
            or ""
        )
        if not raw:
            return "postgresql+asyncpg://neurodebug:neurodebug@localhost:5432/neurodebug"

        # Normalize driver prefix for asyncpg
        if raw.startswith("postgres://"):
            raw = raw.replace("postgres://", "postgresql+asyncpg://", 1)
        elif raw.startswith("postgresql://") and not raw.startswith("postgresql+asyncpg://"):
            raw = raw.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Normalize sslmode query parameters for asyncpg compatibility
        if "sslmode=require" in raw:
            raw = raw.replace("sslmode=require", "ssl=require")
        elif "sslmode=prefer" in raw:
            raw = raw.replace("sslmode=prefer", "ssl=prefer")
        elif "sslmode=disable" in raw:
            raw = raw.replace("sslmode=disable", "ssl=disable")

        return raw

    DATABASE_URL: str = _get_database_url.__func__()
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "5"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))

    # Session Configuration
    SESSION_COOKIE_NAME: str = "neurodebug_session"
    SESSION_EXPIRY_HOURS: int = int(os.getenv("SESSION_EXPIRY_HOURS", "24"))

    # Usage Limits (configurable via database, these are defaults)
    DEFAULT_GUEST_LIMIT: int = int(os.getenv("DEFAULT_GUEST_LIMIT", "1"))
    DEFAULT_FREE_LIMIT: int = int(os.getenv("DEFAULT_FREE_LIMIT", "5"))
    DEFAULT_PRO_LIMIT: int = int(os.getenv("DEFAULT_PRO_LIMIT", "20"))

    # In-Memory Cache Configuration
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"

    # JWT Configuration
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET", "neurodebug-secret-key-change-in-production"
    )
    JWT_ALGORITHM: str = "HS256"

    # Docker Sandbox Configuration
    SANDBOX_IMAGE: str = os.getenv("SANDBOX_IMAGE", "neurodebug-sandbox:latest")
    SANDBOX_TIMEOUT_SECONDS: float = float(os.getenv("SANDBOX_TIMEOUT_SECONDS", "10.0"))
    SANDBOX_MAX_TIMEOUT_SECONDS: float = float(os.getenv("SANDBOX_MAX_TIMEOUT_SECONDS", "30.0"))
    SANDBOX_MEMORY_LIMIT: str = os.getenv("SANDBOX_MEMORY_LIMIT", "256m")
    SANDBOX_CPU_LIMIT: str = os.getenv("SANDBOX_CPU_LIMIT", "1.0")
    SANDBOX_PIDS_LIMIT: int = int(os.getenv("SANDBOX_PIDS_LIMIT", "64"))
    SANDBOX_MAX_OUTPUT_BYTES: int = int(os.getenv("SANDBOX_MAX_OUTPUT_BYTES", "50000"))
    SANDBOX_TMPFS_SIZE: str = os.getenv("SANDBOX_TMPFS_SIZE", "64m")
    SANDBOX_USER: str = os.getenv("SANDBOX_USER", "10001:10001")
    SANDBOX_FORCE_FALLBACK: bool = os.getenv("SANDBOX_FORCE_FALLBACK", "false").lower() == "true"

    @classmethod
    def get_groq_api_key(cls, user_key: str | None = None) -> str | None:
        """Resolve Groq API key from user key or environment."""
        return user_key or cls.GROQ_API_KEY

    @classmethod
    def validate_api_key(cls, api_key: str | None) -> bool:
        """Validate Groq API key format."""
        return api_key is not None and api_key.startswith("gsk_")
