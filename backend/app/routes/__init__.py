"""Routes package."""

from .auth import router as auth_router
from .chat import router as chat_router
from .tasks import router as tasks_router
from .whatsapp import router as whatsapp_router
from .website import router as website_router
from .youtube import router as youtube_router
from .notifications import router as notifications_router
from .reminders import router as reminders_router
from .search import router as search_router
from .preferences import router as preferences_router
from .integrations import router as integrations_router
from .oauth import router as oauth_router
from .billing import router as billing_router

__all__ = [
    "auth_router",
    "chat_router",
    "tasks_router",
    "whatsapp_router",
    "website_router",
    "youtube_router",
    "notifications_router",
    "reminders_router",
    "search_router",
    "preferences_router",
    "integrations_router",
    "oauth_router",
    "billing_router",
]
