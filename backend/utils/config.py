"""Configuration management for NeuroDebug."""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Groq API Configuration
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")

    # Application Configuration
    APP_NAME: str = "NeuroDebug API"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # API Configuration
    MAX_CODE_LENGTH: int = 10000
    REQUEST_TIMEOUT: int = 30

    @classmethod
    def get_groq_api_key(cls, user_key: Optional[str] = None) -> Optional[str]:
        """Resolve Groq API key from user key or environment."""
        return user_key or cls.GROQ_API_KEY

    @classmethod
    def validate_api_key(cls, api_key: Optional[str]) -> bool:
        """Validate Groq API key format."""
        return api_key is not None and api_key.startswith("gsk_")
