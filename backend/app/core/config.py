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
    APP_TIMEZONE: str = "Asia/Kolkata"

    # Firebase
    FIREBASE_ADMIN_CREDENTIALS_PATH: Optional[str] = None
    FIREBASE_SERVICE_ACCOUNT_JSON: Optional[str] = None
    FIREBASE_PROJECT_ID: Optional[str] = None

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # AI Providers
    EMBEDDING_PROVIDER: str = "google"  # google, openai
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_AI_API_KEY: Optional[str] = None
    GOOGLE_AI_API_FALLBACK_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    
    # AI Models (configurable)
    GEMINI_MODEL: str = "gemini-1.5-flash"  # gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash
    GEMINI_VISION_MODEL: str = "gemini-1.5-flash"  # Vision model for image analysis
    OPENAI_MODEL: str = "gpt-4o-mini"  # gpt-4o, gpt-4o-mini, gpt-4-turbo

    # Observability
    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "agentcoolie-production"

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_OAUTH_REDIRECT_URI: Optional[str] = None
    FRONTEND_URL: Optional[str] = None

    # YouTube
    YOUTUBE_API_KEY: Optional[str] = None

    # Web search
    SERPAPI_API_KEY: Optional[str] = None

    # Call reminders
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None
    TWILIO_WHATSAPP_FROM: Optional[str] = None
    TWILIO_VALIDATE_WEBHOOK_SIGNATURE: bool = True
    CALL_REMINDER_POLL_INTERVAL_SECONDS: int = 30
    TASK_EXECUTION_LEASE_SECONDS: int = 300

    # Webhooks
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    WHATSAPP_WEBHOOK_SECRET: Optional[str] = None

    # n8n tool webhooks
    N8N_BASE_URL: Optional[str] = None
    N8N_GMAIL_ACTION_PATH: str = "/webhook/gmail-action"
    N8N_GMAIL_CREDENTIALS_PATH: str = "/webhook/save-gmail-credentials"
    N8N_TOOL_SECRET: Optional[str] = None

    # Short-term chat memory
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    REDIS_MEMORY_TTL_SECONDS: int = 86400
    REDIS_MEMORY_CONTEXT_EXCHANGES: int = 5
    REDIS_MEMORY_MAX_MESSAGES: int = 30

    # Long-term memory
    LONG_TERM_MEMORY_ENABLED: bool = True
    LONG_TERM_MEMORY_CONTEXT_LIMIT: int = 20
    LONG_TERM_MEMORY_MIN_IMPORTANCE: float = 0.65

    # Session
    SESSION_SECRET_KEY: str = "your-secret-key-change-in-production"
    OAUTH_STATE_MAX_AGE_SECONDS: int = 600

    # Billing
    DEMO_BILLING_ENABLED: bool = False

    # Upload limits
    MAX_ATTACHMENT_COUNT: int = 4
    MAX_UPLOAD_BYTES: int = 25 * 1024 * 1024

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
