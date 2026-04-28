"""
Configuration management using Pydantic v2 settings.
Supports environment variables and .env file loading.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENV: str = "development"
    DEBUG: bool = True

    # Firebase
    FIREBASE_ADMIN_CREDENTIALS_PATH: Optional[str] = None
    FIREBASE_SERVICE_ACCOUNT_JSON: Optional[str] = None
    FIREBASE_PROJECT_ID: Optional[str] = None

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # AI Providers
    EMBEDDING_PROVIDER: str = "google"  # cohere, google, openai
    COHERE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_AI_API_KEY: Optional[str] = None
    
    # AI Models (configurable)
    GEMINI_MODEL: str = "gemini-1.5-flash"  # gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash
    GEMINI_VISION_MODEL: str = "gemini-1.5-flash"  # Vision model for image analysis
    OPENAI_MODEL: str = "gpt-4o-mini"  # gpt-4o, gpt-4o-mini, gpt-4-turbo
    COHERE_MODEL: str = "command-r-plus"  # command-r-plus, command-r

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_OAUTH_REDIRECT_URI: Optional[str] = None

    # YouTube
    YOUTUBE_API_KEY: Optional[str] = None

    # Session
    SESSION_SECRET_KEY: str = "your-secret-key-change-in-production"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:8000"]

    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=[str(Path(__file__).resolve().parent.parent.parent.parent / ".env"), ".env"],
        case_sensitive=True,
        extra="allow"
    )


# Load settings
settings = Settings()


def get_settings() -> Settings:
    """Get current settings."""
    return settings
