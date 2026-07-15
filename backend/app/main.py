"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.core.body_limit import BodySizeLimitMiddleware
from app.core.config import settings
from app.services.call_task_scheduler import call_task_scheduler
from app.services.firebase_service import firebase_service
from app.services.supabase_service import supabase_service
from app.routes import (
    auth_router,
    chat_router,
    tasks_router,
    whatsapp_router,
    website_router,
    youtube_router,
    notifications_router,
    reminders_router,
    search_router,
    preferences_router,
    integrations_router,
    oauth_router,
    billing_router,
)
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="AgentCoolie",
    description="Memory-aware AI workspace with multi-channel integration",
    version="2.0.0",
    docs_url="/docs" if settings.api_docs_enabled() else None,
    redoc_url="/redoc" if settings.api_docs_enabled() else None,
    openapi_url="/openapi.json" if settings.api_docs_enabled() else None,
)

# Reject oversized request bodies before JSON/multipart parsers buffer them.
max_upload_count = max(1, int(settings.MAX_ATTACHMENT_COUNT or 1))
# Chat attachments are JSON base64 strings, which are about 4/3 the original
# file size. Leave a small allowance for JSON/form metadata.
max_raw_upload_bytes = max(0, int(settings.MAX_UPLOAD_BYTES or 0))
max_encoded_attachment_bytes = ((max_raw_upload_bytes + 2) // 3) * 4
max_request_body_bytes = (max_encoded_attachment_bytes * max_upload_count) + (1024 * 1024)
app.add_middleware(BodySizeLimitMiddleware, max_body_size=max_request_body_bytes)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZIP compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    checks = {
        "firebase": firebase_service.is_ready(),
        "supabase_configured": supabase_service.is_configured(),
        "supabase_initialized": supabase_service.is_ready(),
    }
    production_ready = checks["firebase"] and checks["supabase_configured"]
    return {
        "status": "healthy" if settings.is_local_runtime() or production_ready else "degraded",
        "version": "2.0.0",
        **({"checks": checks} if settings.is_local_runtime() else {}),
    }


# Register routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(tasks_router)
app.include_router(whatsapp_router)
app.include_router(website_router)
app.include_router(youtube_router)
app.include_router(notifications_router)
app.include_router(reminders_router)
app.include_router(search_router)
app.include_router(preferences_router)
app.include_router(integrations_router)
app.include_router(oauth_router)
app.include_router(billing_router)


# Root endpoint
@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    payload = {
        "message": "AgentCoolie API v2.0",
        "health": "/health",
    }
    if settings.api_docs_enabled():
        payload["docs"] = "/docs"
    return payload


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    settings.validate_runtime_safety()
    logger.info("Starting AgentCoolie API...")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    call_task_scheduler.start()


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down AgentCoolie API...")
    await call_task_scheduler.stop()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
