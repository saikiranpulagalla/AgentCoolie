"""
Supabase database service.
"""

from supabase import create_client, Client
from app.core.config import settings
import logging
import asyncio
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class SupabaseService:
    """Supabase database operations."""

    _instance = None
    _client: Optional[Client] = None

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize Supabase client lazily on first use."""
        self._initialized = False
        self._client = None

    def _ensure_initialized(self):
        """Lazy initialization of Supabase client on first use."""
        if self._initialized:
            return
        
        try:
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )
            logger.info("Supabase client initialized successfully")
            self._initialized = True
        except Exception as e:
            logger.error(f"Supabase initialization failed: {e}")
            self._initialized = True  # Mark as attempted to prevent retry storm
            raise  # Re-raise so caller knows initialization failed

    @property
    def client(self) -> Client:
        """Get Supabase client - initializes on first use."""
        self._ensure_initialized()
        if self._client is None:
            raise RuntimeError("Supabase client not initialized - check credentials")
        return self._client

    # ============ User Operations ============
    async def get_user_by_firebase_id(self, firebase_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Firebase ID."""
        try:
            def _get():
                return self.client.table("users").select("*").eq("firebase_id", firebase_id).single().execute()
            response = await asyncio.to_thread(_get)
            return response.data[0] if response.data else None
        except Exception as e:
            logger.warning(f"User not found: {firebase_id}")
            return None

    async def create_user(self, firebase_id: str, email: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user."""
        try:
            def _create():
                return self.client.table("users").insert({
                    "firebase_id": firebase_id,
                    "email": email,
                    "display_name": display_name,
                }).execute()
            response = await asyncio.to_thread(_create)
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise

    async def update_user(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Update user."""
        try:
            def _update():
                return self.client.table("users").update(kwargs).eq("id", user_id).execute()
            response = await asyncio.to_thread(_update)
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise

    # ============ Chat Message Operations ============
    async def create_message(self, user_id: str, content: str, role: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Create a chat message."""
        try:
            def _create():
                return self.client.table("chat_messages").insert({
                    "user_id": user_id,
                    "content": content,
                    "role": role,
                    "model": model,
                }).execute()
            response = await asyncio.to_thread(_create)
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create message: {e}")
            raise

    async def get_messages(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent chat messages."""
        try:
            def _get():
                return self.client.table("chat_messages").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
            response = await asyncio.to_thread(_get)
            return response.data[::-1]  # Reverse to get chronological order
        except Exception as e:
            logger.error(f"Failed to get messages for user {user_id}: {e}")
            return []

    # ============ Task Operations ============
    async def create_task(self, user_id: str, title: str, task_type: str, priority: str = "medium", description: Optional[str] = None, due_date: Optional[str] = None) -> Dict[str, Any]:
        """Create a task."""
        try:
            def _create():
                return self.client.table("tasks").insert({
                    "user_id": user_id,
                    "title": title,
                    "description": description,
                    "type": task_type,
                    "priority": priority,
                    "due_date": due_date,
                    "completed": False,
                }).execute()
            response = await asyncio.to_thread(_create)
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise

    async def get_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user tasks."""
        try:
            def _get():
                return self.client.table("tasks").select("*").eq("user_id", user_id).execute()
            response = await asyncio.to_thread(_get)
            return response.data
        except Exception as e:
            logger.error(f"Failed to get tasks for user {user_id}: {e}")
            return []

    async def update_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """Update a task."""
        try:
            def _update():
                return self.client.table("tasks").update(kwargs).eq("id", task_id).execute()
            response = await asyncio.to_thread(_update)
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            raise

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        try:
            def _delete():
                return self.client.table("tasks").delete().eq("id", task_id).execute()
            await asyncio.to_thread(_delete)
            return True
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False

    # ============ Preferences Operations ============
    async def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences."""
        try:
            def _get():
                return self.client.table("user_preferences").select("*").eq("user_id", user_id).single().execute()
            response = await asyncio.to_thread(_get)
            return response.data[0] if response.data else None
        except Exception:
            return None

    async def upsert_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update user preferences."""
        try:
            def _upsert():
                return self.client.table("user_preferences").upsert({
                    "user_id": user_id,
                    **preferences,
                }).execute()
            response = await asyncio.to_thread(_upsert)
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to upsert preferences for user {user_id}: {e}")
            raise

    # ============ Credentials Operations ============
    async def save_credentials(self, user_id: str, cred_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save user credentials (Gmail, WhatsApp, etc.)."""
        try:
            def _save():
                return self.client.table("user_credentials").upsert({
                    "user_id": user_id,
                    "type": cred_type,
                    "data": data,
                }).execute()
            response = await asyncio.to_thread(_save)
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to save credentials for user {user_id}: {e}")
            raise

    async def get_credentials(self, user_id: str, cred_type: str) -> Optional[Dict[str, Any]]:
        """Get user credentials."""
        try:
            def _get():
                return self.client.table("user_credentials").select("*").eq("user_id", user_id).eq("type", cred_type).single().execute()
            response = await asyncio.to_thread(_get)
            return response.data[0] if response.data else None
        except Exception:
            return None

    # ============ Notifications Operations ============
    async def create_notification(self, user_id: str, title: str, message: str, notification_type: str = "info") -> Dict[str, Any]:
        """Create a notification."""
        try:
            def _create():
                return self.client.table("notifications").insert({
                    "user_id": user_id,
                    "title": title,
                    "message": message,
                    "type": notification_type,
                    "read": False,
                }).execute()
            response = await asyncio.to_thread(_create)
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            raise

    async def get_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get user notifications."""
        try:
            def _get():
                query = self.client.table("notifications").select("*").eq("user_id", user_id)
                if unread_only:
                    query = query.eq("read", False)
                return query.order("created_at", desc=True).execute()
            response = await asyncio.to_thread(_get)
            return response.data
        except Exception as e:
            logger.error(f"Failed to get notifications for user {user_id}: {e}")
            return []


# Initialize singleton instance
supabase_service = SupabaseService()
