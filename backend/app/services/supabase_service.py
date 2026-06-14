"""
Supabase database service.
"""

from supabase import create_client, Client
from app.core.config import settings
import logging
import asyncio
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def is_connectivity_error(error: Exception) -> bool:
    """Return True for network/DNS failures talking to Supabase."""
    text = str(error)
    return (
        "getaddrinfo failed" in text
        or "ConnectError" in text
        or "Name or service not known" in text
        or "nodename nor servname provided" in text
    )


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
        if getattr(self, "_constructed", False):
            return
        self._constructed = True
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
            self._client = None
            self._initialized = False
            raise  # Re-raise so caller knows initialization failed

    @property
    def client(self) -> Client:
        """Get Supabase client - initializes on first use."""
        self._ensure_initialized()
        if self._client is None:
            raise RuntimeError("Supabase client not initialized - check credentials")
        return self._client

    def is_configured(self) -> bool:
        """Return whether required Supabase settings are present."""
        return bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)

    def is_ready(self) -> bool:
        """Return whether the lazy client has initialized successfully."""
        return self._client is not None and self._initialized

    # ============ User Operations ============
    async def get_user_by_firebase_id(self, firebase_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Firebase ID."""
        try:
            def _get():
                return self.client.table("users").select("*").eq("firebase_id", firebase_id).single().execute()
            response = await asyncio.to_thread(_get)
            if isinstance(response.data, dict):
                return response.data
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
    async def create_message(
        self,
        user_id: str,
        content: str,
        role: str,
        model: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a chat message."""
        try:
            payload = {
                "user_id": user_id,
                "content": content,
                "role": role,
                "model": model,
            }
            if conversation_id:
                payload["conversation_id"] = conversation_id

            def _create():
                return self.client.table("chat_messages").insert(payload).execute()

            try:
                response = await asyncio.to_thread(_create)
            except Exception as e:
                if conversation_id and "conversation_id" in str(e):
                    raise RuntimeError(
                        "Supabase chat_messages.conversation_id is missing. "
                        "Run backend/sql/chat_messages_conversation_id.sql before using chat-scoped history."
                    ) from e
                raise
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create message: {e}")
            raise

    async def get_messages(
        self,
        user_id: str,
        limit: int = 50,
        conversation_id: Optional[str] = None,
        since_iso: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get recent chat messages."""
        try:
            def _get():
                query = self.client.table("chat_messages").select("*").eq("user_id", user_id)
                if conversation_id:
                    query = query.eq("conversation_id", conversation_id)
                if since_iso:
                    query = query.gte("created_at", since_iso)
                return query.order("created_at", desc=True).limit(limit).execute()
            response = await asyncio.to_thread(_get)
            rows = response.data[::-1]  # Reverse to get chronological order
            for row in rows:
                if "timestamp" not in row and row.get("created_at"):
                    row["timestamp"] = row.get("created_at")
            return rows
        except Exception as e:
            logger.error(f"Failed to get messages for user {user_id}: {e}")
            raise

    async def delete_messages_for_conversation(self, user_id: str, conversation_id: str) -> int:
        """Delete durable chat messages for one user-owned conversation."""
        conversation_id = str(conversation_id or "").strip()
        if not conversation_id:
            return 0

        try:
            def _delete():
                return (
                    self.client.table("chat_messages")
                    .delete()
                    .eq("user_id", user_id)
                    .eq("conversation_id", conversation_id)
                    .execute()
                )

            response = await asyncio.to_thread(_delete)
            return len(response.data or [])
        except Exception as e:
            logger.error(f"Failed to delete chat messages for user {user_id}, conversation {conversation_id}: {e}")
            raise

    # ============ Long-Term Memory Operations ============
    async def create_long_term_memory(
        self,
        user_id: str,
        content: str,
        source: str = "chat",
        importance_score: float = 0.7,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        normalized_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a long-term memory row."""
        try:
            def _create():
                return self.client.table("long_term_memories").insert({
                    "user_id": user_id,
                    "content": content,
                    "normalized_content": normalized_content,
                    "source": source,
                    "importance_score": importance_score,
                    "reason": reason,
                    "metadata": metadata or {},
                }).execute()
            response = await asyncio.to_thread(_create)
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to create long-term memory: {e}")
            raise

    async def find_long_term_memory_by_normalized_content(
        self,
        user_id: str,
        normalized_content: str,
    ) -> Optional[Dict[str, Any]]:
        """Find an existing long-term memory by normalized content."""
        try:
            def _get():
                return (
                    self.client.table("long_term_memories")
                    .select("*")
                    .eq("user_id", user_id)
                    .eq("normalized_content", normalized_content)
                    .limit(1)
                    .execute()
                )
            response = await asyncio.to_thread(_get)
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to find long-term memory duplicate: {e}")
            raise

    async def get_long_term_memories(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get the most important recent long-term memories for a user."""
        try:
            def _get():
                return (
                    self.client.table("long_term_memories")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("importance_score", desc=True)
                    .order("created_at", desc=True)
                    .limit(limit)
                    .execute()
                )
            response = await asyncio.to_thread(_get)
            return response.data
        except Exception as e:
            logger.error(f"Failed to get long-term memories for user {user_id}: {e}")
            raise

    async def count_long_term_memories(self, user_id: str) -> int:
        """Count durable memories for a user."""
        try:
            def _count():
                return (
                    self.client.table("long_term_memories")
                    .select("id", count="exact")
                    .eq("user_id", user_id)
                    .execute()
                )
            response = await asyncio.to_thread(_count)
            return int(response.count or 0)
        except Exception as e:
            logger.error(f"Failed to count long-term memories for user {user_id}: {e}")
            raise

    # ============ Task Operations ============
    async def create_task(
        self,
        user_id: str,
        title: str,
        task_type: str,
        priority: str = "medium",
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
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
                    "status": "pending",
                    "metadata": metadata or {},
                }).execute()
            response = await asyncio.to_thread(_create)
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise

    async def create_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple tasks in one PostgREST insert."""
        if not tasks:
            return []

        try:
            payloads = []
            for task in tasks:
                payloads.append({
                    "user_id": task["user_id"],
                    "title": task["title"],
                    "description": task.get("description"),
                    "type": task["type"],
                    "priority": task.get("priority") or "medium",
                    "due_date": task.get("due_date"),
                    "completed": False,
                    "status": "pending",
                    "metadata": task.get("metadata") or {},
                })

            def _create_many():
                return self.client.table("tasks").insert(payloads).execute()

            response = await asyncio.to_thread(_create_many)
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to create tasks: {e}")
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
            raise

    async def count_active_tasks(self, user_id: str, notify_by_call: bool | None = None) -> int:
        """Count tasks still active for quota enforcement."""
        try:
            def _count():
                query = (
                    self.client.table("tasks")
                    .select("id", count="exact")
                    .eq("user_id", user_id)
                    .in_("status", ["pending", "calling"])
                )
                if notify_by_call is True:
                    query = query.contains("metadata", {"notify_by_call": True})
                return query.execute()
            response = await asyncio.to_thread(_count)
            return int(response.count or 0)
        except Exception as e:
            logger.error(f"Failed to count active tasks for user {user_id}: {e}")
            raise

    async def get_due_pending_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get due pending tasks across users for backend-side automation."""
        try:
            from datetime import datetime, timezone

            now_iso = datetime.now(timezone.utc).isoformat()

            def _get():
                return (
                    self.client.table("tasks")
                    .select("*")
                    .eq("status", "pending")
                    .lte("due_date", now_iso)
                    .order("due_date", desc=False)
                    .limit(limit)
                    .execute()
                )
            response = await asyncio.to_thread(_get)
            return response.data
        except Exception as e:
            logger.error(f"Failed to get due pending tasks: {e}")
            raise

    async def get_stale_claimed_tasks(
        self,
        older_than_iso: str,
        limit: int = 50,
        execution_scopes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get claimed backend/manual tasks whose execution lease appears stale."""
        scopes = execution_scopes or ["backend_scheduler", "manual_execute"]
        try:
            def _get_for_scope(scope: str):
                return (
                    self.client.table("tasks")
                    .select("*")
                    .eq("status", "calling")
                    .lte("last_attempt_at", older_than_iso)
                    .contains("metadata", {"execution_scope": scope})
                    .order("last_attempt_at", desc=False)
                    .limit(limit)
                    .execute()
                )

            rows: List[Dict[str, Any]] = []
            for scope in scopes:
                response = await asyncio.to_thread(_get_for_scope, scope)
                for row in response.data or []:
                    if row not in rows:
                        rows.append(row)
                    if len(rows) >= limit:
                        return rows
            return rows
        except Exception as e:
            logger.error(f"Failed to get stale claimed tasks: {e}")
            raise

    async def get_task(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a single task scoped to a user."""
        try:
            def _get():
                return (
                    self.client.table("tasks")
                    .select("*")
                    .eq("id", task_id)
                    .eq("user_id", user_id)
                    .limit(1)
                    .execute()
                )
            response = await asyncio.to_thread(_get)
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get task {task_id} for user {user_id}: {e}")
            raise

    async def update_task(self, task_id: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """Update a task."""
        try:
            def _update():
                return (
                    self.client.table("tasks")
                    .update(kwargs)
                    .eq("id", task_id)
                    .eq("user_id", user_id)
                    .execute()
                )
            response = await asyncio.to_thread(_update)
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            raise

    async def claim_pending_task(self, task_id: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """Atomically move a pending task into an in-progress state."""
        try:
            def _claim():
                return (
                    self.client.table("tasks")
                    .update(kwargs)
                    .eq("id", task_id)
                    .eq("user_id", user_id)
                    .eq("status", "pending")
                    .execute()
                )
            response = await asyncio.to_thread(_claim)
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to claim pending task {task_id}: {e}")
            raise

    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task."""
        try:
            def _delete():
                return (
                    self.client.table("tasks")
                    .delete()
                    .eq("id", task_id)
                    .eq("user_id", user_id)
                    .execute()
                )
            response = await asyncio.to_thread(_delete)
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            raise

    # ============ Preferences Operations ============
    async def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences."""
        try:
            def _get():
                return self.client.table("user_preferences").select("*").eq("user_id", user_id).limit(1).execute()
            response = await asyncio.to_thread(_get)
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get preferences for user {user_id}: {e}")
            raise

    async def upsert_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update user preferences."""
        try:
            def _upsert():
                return (
                    self.client.table("user_preferences")
                    .upsert({
                        "user_id": user_id,
                        **preferences,
                    }, on_conflict="user_id")
                    .execute()
                )
            response = await asyncio.to_thread(_upsert)
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to upsert preferences for user {user_id}: {e}")
            raise

    # ============ Credentials Operations ============
    def _normalize_credentials_data(self, cred_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize integration credential payloads while preserving original fields."""
        normalized = dict(data or {})
        if cred_type != "gmail":
            return normalized

        key_map = {
            "client_id": "gmail_client_id",
            "clientId": "gmail_client_id",
            "gmailClientId": "gmail_client_id",
            "client_secret": "gmail_client_secret",
            "clientSecret": "gmail_client_secret",
            "gmailClientSecret": "gmail_client_secret",
            "refresh_token": "gmail_refresh_token",
            "refreshToken": "gmail_refresh_token",
            "gmailRefreshToken": "gmail_refresh_token",
            "token": "gmail_access_token",
            "access_token": "gmail_access_token",
            "gmailAccessToken": "gmail_access_token",
            "apiKey": "gmail_api_key",
            "gmailApiKey": "gmail_api_key",
        }
        for source, target in key_map.items():
            value = normalized.get(source)
            if value and not normalized.get(target):
                normalized[target] = value

        return normalized

    async def save_credentials(self, user_id: str, cred_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save user credentials (Gmail, WhatsApp, etc.)."""
        try:
            normalized_data = self._normalize_credentials_data(cred_type, data)
            def _save():
                return (
                    self.client.table("user_credentials")
                    .upsert({
                        "user_id": user_id,
                        "type": cred_type,
                        "data": normalized_data,
                    }, on_conflict="user_id,type")
                    .execute()
                )
            response = await asyncio.to_thread(_save)
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to save credentials for user {user_id}: {e}")
            raise

    async def get_credentials(self, user_id: str, cred_type: str) -> Optional[Dict[str, Any]]:
        """Get user credentials."""
        try:
            def _get():
                return self.client.table("user_credentials").select("*").eq("user_id", user_id).eq("type", cred_type).limit(1).execute()
            response = await asyncio.to_thread(_get)
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get {cred_type} credentials for user {user_id}: {e}")
            raise

    async def find_user_id_by_credential_phone(self, phone_number: str) -> Optional[str]:
        """Find a user whose stored credential data contains this phone number."""
        try:
            def _get(cred_type: str):
                return (
                    self.client.table("user_credentials")
                    .select("user_id,data,type")
                    .eq("type", cred_type)
                    .contains("data", {"phone_number": phone_number})
                    .limit(1)
                    .execute()
                )

            for cred_type in ("whatsapp", "call_reminder"):
                response = await asyncio.to_thread(_get, cred_type)
                if response.data:
                    return response.data[0].get("user_id")
            return None
        except Exception as e:
            logger.error(f"Failed to find user by phone credential: {e}")
            raise

    async def find_credential_by_phone(self, phone_number: str, cred_type: str) -> Optional[Dict[str, Any]]:
        """Find one credential row by provider phone number."""
        try:
            def _get():
                return (
                    self.client.table("user_credentials")
                    .select("user_id,data,type")
                    .eq("type", cred_type)
                    .contains("data", {"phone_number": phone_number})
                    .limit(1)
                    .execute()
                )

            response = await asyncio.to_thread(_get)
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to find {cred_type} credential by phone: {e}")
            raise

    async def delete_credentials(self, user_id: str, cred_type: str) -> bool:
        """Delete user credentials."""
        try:
            def _delete():
                return (
                    self.client.table("user_credentials")
                    .delete()
                    .eq("user_id", user_id)
                    .eq("type", cred_type)
                    .execute()
                )
            response = await asyncio.to_thread(_delete)
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to delete {cred_type} credentials for user {user_id}: {e}")
            raise

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
            raise

    # ============ Plan and Usage Operations ============
    async def get_user_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user's billing/entitlement row."""
        try:
            def _get():
                return (
                    self.client.table("user_plans")
                    .select("*")
                    .eq("user_id", user_id)
                    .limit(1)
                    .execute()
                )
            response = await asyncio.to_thread(_get)
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get user plan for {user_id}: {e}")
            if is_connectivity_error(e):
                raise
            return None

    async def upsert_user_plan(
        self,
        user_id: str,
        plan: str,
        billing_status: str,
        provider: Optional[str] = None,
        provider_customer_id: Optional[str] = None,
        provider_subscription_id: Optional[str] = None,
        current_period_start: Optional[str] = None,
        current_period_end: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create or update a user's plan row."""
        try:
            payload = {
                "user_id": user_id,
                "plan": plan,
                "billing_status": billing_status,
                "provider": provider,
                "provider_customer_id": provider_customer_id,
                "provider_subscription_id": provider_subscription_id,
                "current_period_start": current_period_start,
                "current_period_end": current_period_end,
            }

            def _upsert():
                return (
                    self.client.table("user_plans")
                    .upsert(payload, on_conflict="user_id")
                    .execute()
                )
            response = await asyncio.to_thread(_upsert)
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to upsert user plan for {user_id}: {e}")
            if is_connectivity_error(e):
                raise
            raise

    async def create_usage_event(
        self,
        user_id: str,
        feature: str,
        amount: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record one billable/limited usage event."""
        try:
            def _create():
                return self.client.table("usage_events").insert({
                    "user_id": user_id,
                    "feature": feature,
                    "amount": max(1, int(amount or 1)),
                    "metadata": metadata or {},
                }).execute()
            response = await asyncio.to_thread(_create)
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to create usage event {feature} for {user_id}: {e}")
            raise

    async def consume_usage_quota(
        self,
        user_id: str,
        feature: str,
        amount: int,
        metadata: Optional[Dict[str, Any]],
        day_start: Optional[str] = None,
        day_limit: Optional[int] = None,
        month_start: Optional[str] = None,
        month_limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Atomically check quota and record usage through a Postgres RPC."""
        try:
            payload = {
                "p_user_id": user_id,
                "p_feature": feature,
                "p_amount": max(1, int(amount or 1)),
                "p_metadata": metadata or {},
                "p_day_start": day_start,
                "p_day_limit": day_limit,
                "p_month_start": month_start,
                "p_month_limit": month_limit,
            }

            def _consume():
                return self.client.rpc("consume_usage_quota", payload).execute()

            response = await asyncio.to_thread(_consume)
            data = response.data
            if isinstance(data, list):
                return data[0] if data else {}
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"Failed to atomically consume usage {feature} for {user_id}: {e}")
            if is_connectivity_error(e):
                raise
            raise

    async def count_usage_events(self, user_id: str, feature: str, since: str) -> int:
        """Sum usage amount for a feature since an ISO timestamp."""
        try:
            def _get():
                return (
                    self.client.table("usage_events")
                    .select("amount")
                    .eq("user_id", user_id)
                    .eq("feature", feature)
                    .gte("occurred_at", since)
                    .execute()
                )
            response = await asyncio.to_thread(_get)
            total = 0
            for row in response.data or []:
                total += int(row.get("amount") or 1)
            return total
        except Exception as e:
            logger.error(f"Failed to count usage events {feature} for {user_id}: {e}")
            raise


# Initialize singleton instance
supabase_service = SupabaseService()
