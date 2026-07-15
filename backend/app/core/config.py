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
    ALLOW_DEV_OAUTH_UID_FALLBACK: bool = False

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
    WHATSAPP_VERIFICATION_TTL_MINUTES: int = 15
    WHATSAPP_VERIFICATION_RESEND_SECONDS: int = 60
    WEBHOOK_IDEMPOTENCY_TTL_SECONDS: int = 86400

    # n8n tool webhooks
    N8N_BASE_URL: Optional[str] = None
    N8N_GMAIL_ACTION_PATH: str = "/webhook/gmail-action"
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
    # Raw bytes per attachment. JSON base64 expands this on the wire, so the
    # request-body limit is calculated separately by the ASGI middleware setup.
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024
    MAX_CHAT_MESSAGE_CHARS: int = 12000
    MAX_ATTACHMENT_CONTEXT_CHARS: int = 60000
    MAX_IMAGE_PIXELS: int = 40_000_000
    AI_REQUEST_TIMEOUT_SECONDS: int = 60

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:8000"]

    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=[str(Path(__file__).resolve().parent.parent.parent.parent / ".env"), ".env"],
        case_sensitive=True,
        extra="allow"
    )

    def is_local_runtime(self) -> bool:
        """Return true only for explicitly local/test environments."""
        return self.ENV.strip().lower() in {"development", "dev", "local", "test", "testing"}

    def is_production(self) -> bool:
        """Return true for every deployment that is not explicitly local/test."""
        return not self.is_local_runtime()

    def api_docs_enabled(self) -> bool:
        """Keep interactive docs on for development, off by default in production."""
        return self.is_local_runtime() and bool(self.DEBUG)

    def validate_runtime_safety(self) -> None:
        """Fail fast on unsafe production configuration."""
        if self.is_local_runtime():
            return

        errors: list[str] = []
        if self.DEBUG:
            errors.append("DEBUG must be false in production.")
        if not self.SESSION_SECRET_KEY or self.SESSION_SECRET_KEY == "your-secret-key-change-in-production":
            errors.append("SESSION_SECRET_KEY must be set to a strong production secret.")
        elif len(self.SESSION_SECRET_KEY) < 32:
            errors.append("SESSION_SECRET_KEY must be at least 32 characters in production.")
        if "*" in [origin.strip() for origin in self.CORS_ORIGINS]:
            errors.append("CORS_ORIGINS must not contain '*' when credentials are allowed.")
        if not self.TWILIO_VALIDATE_WEBHOOK_SIGNATURE:
            errors.append("TWILIO_VALIDATE_WEBHOOK_SIGNATURE must be true in production.")
        if self.DEMO_BILLING_ENABLED:
            errors.append("DEMO_BILLING_ENABLED must be false in production.")
        if self.REDIS_URL and not self.REDIS_URL.lower().startswith("rediss://"):
            errors.append("REDIS_URL must use rediss:// outside local development.")
        for origin in self.CORS_ORIGINS:
            normalized = origin.strip().lower()
            if not normalized.startswith("https://"):
                errors.append("CORS_ORIGINS must use https:// outside local development.")
                break

        if errors:
            raise ValueError("Unsafe production configuration: " + " ".join(errors))


# Load settings
settings = Settings()


def get_settings() -> Settings:
    """Get current settings."""
    return settings
