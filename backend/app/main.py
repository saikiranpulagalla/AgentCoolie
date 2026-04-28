"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.core.config import settings
from app.routes import (
    auth_router,
    chat_router,
    tasks_router,
    whatsapp_router,
    gmail_router,
    website_router,
    youtube_router,
    notifications_router,
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
    title="CoolieAssistant",
    description="AI-powered assistant with multi-channel integration",
    version="2.0.0",
)

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
    return {
        "status": "healthy",
        "environment": settings.ENV,
        "version": "2.0.0",
    }


# Register routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(tasks_router)
app.include_router(whatsapp_router)
app.include_router(gmail_router)
app.include_router(website_router)
app.include_router(youtube_router)
app.include_router(notifications_router)


# Root endpoint
@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "CoolieAssistant API v2.0",
        "docs": "/docs",
        "health": "/health",
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting CoolieAssistant API...")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down CoolieAssistant API...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
