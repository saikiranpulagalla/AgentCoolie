"""Routes package."""

from .auth import router as auth_router
from .chat import router as chat_router
from .tasks import router as tasks_router
from .whatsapp import router as whatsapp_router
from .gmail import router as gmail_router
from .website import router as website_router
from .youtube import router as youtube_router
from .notifications import router as notifications_router

__all__ = [
    "auth_router",
    "chat_router",
    "tasks_router",
    "whatsapp_router",
    "gmail_router",
    "website_router",
    "youtube_router",
    "notifications_router",
]
