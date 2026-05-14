"""
Redis-backed short-term chat memory.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisMemoryService:
    """Stores a small rolling window of per-user chat messages in Redis."""

    def __init__(self) -> None:
        self.redis_url = settings.REDIS_URL
        self.ttl_seconds = settings.REDIS_MEMORY_TTL_SECONDS
        self.context_exchanges = settings.REDIS_MEMORY_CONTEXT_EXCHANGES
        self.max_messages = max(settings.REDIS_MEMORY_MAX_MESSAGES, self.context_exchanges * 2, 30)
        self._client: Any = None
        self._disabled = False

    async def _get_client(self) -> Optional[Any]:
        if self._disabled or not self.redis_url:
            return None

        if self._client is not None:
            return self._client

        try:
            import redis.asyncio as redis

            client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                health_check_interval=30,
                socket_connect_timeout=3,
                socket_timeout=3,
            )
            await client.ping()
            self._client = client
            logger.info("Redis short memory connected")
            return self._client
        except ImportError:
            logger.warning("Redis package is not installed; short memory is disabled")
            self._disabled = True
        except Exception as e:
            logger.warning(f"Redis short memory unavailable; continuing without it: {e}")

        return None

    def _scope(self, conversation_id: str | None = None) -> str:
        raw = str(conversation_id or "default").strip() or "default"
        safe = re.sub(r"[^a-zA-Z0-9._:-]", "_", raw)[:120]
        return safe or "default"

    def _key(self, user_id: str, conversation_id: str | None = None) -> str:
        return f"coolie:short-memory:{user_id}:{self._scope(conversation_id)}"

    def _state_key(self, user_id: str, name: str, conversation_id: str | None = None) -> str:
        return f"coolie:tool-state:{user_id}:{self._scope(conversation_id)}:{name}"

    async def get_recent_messages(
        self,
        user_id: str,
        limit: Optional[int] = None,
        conversation_id: str | None = None,
    ) -> list[dict[str, str]]:
        """Return recent messages for a user's specific chat, newest window in chronological order."""
        client = await self._get_client()
        if client is None:
            return []

        count = limit or self.max_messages
        try:
            raw_messages = await client.lrange(self._key(user_id, conversation_id), -count, -1)
            messages: list[dict[str, str]] = []
            for raw in raw_messages:
                try:
                    item = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                role = str(item.get("role", "")).strip()
                content = str(item.get("content", "")).strip()
                if role in {"user", "assistant"} and content:
                    messages.append({"role": role, "content": content})
            return messages
        except Exception as e:
            logger.warning(f"Failed to read Redis short memory: {e}")
            return []

    async def get_recent_exchanges(
        self,
        user_id: str,
        limit: Optional[int] = None,
        conversation_id: str | None = None,
    ) -> list[dict[str, str]]:
        """Return the last N user/assistant exchanges for a specific chat."""
        exchange_limit = limit or self.context_exchanges
        return await self.get_recent_messages(user_id, limit=exchange_limit * 2, conversation_id=conversation_id)

    async def append_exchange(
        self,
        user_id: str,
        user_message: str,
        assistant_message: str,
        conversation_id: str | None = None,
    ) -> None:
        """Append the latest user and assistant messages to a chat-scoped rolling memory."""
        client = await self._get_client()
        if client is None:
            return

        now = datetime.now(timezone.utc).isoformat()
        entries = [
            {"role": "user", "content": user_message, "created_at": now},
            {"role": "assistant", "content": assistant_message, "created_at": now},
        ]

        try:
            key = self._key(user_id, conversation_id)
            await client.rpush(key, *[json.dumps(entry) for entry in entries])
            await client.ltrim(key, -self.max_messages, -1)
            if self.ttl_seconds > 0:
                await client.expire(key, self.ttl_seconds)
        except Exception as e:
            logger.warning(f"Failed to write Redis short memory: {e}")

    async def get_state(
        self,
        user_id: str,
        name: str,
        conversation_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Return short-lived structured tool state for a specific chat."""
        client = await self._get_client()
        if client is None:
            return None

        try:
            raw = await client.get(self._state_key(user_id, name, conversation_id))
            if not raw:
                return None
            data = json.loads(raw)
            return data if isinstance(data, dict) else None
        except Exception as e:
            logger.warning(f"Failed to read Redis tool state {name}: {e}")
            return None

    async def set_state(
        self,
        user_id: str,
        name: str,
        value: dict[str, Any],
        ttl_seconds: int = 900,
        conversation_id: str | None = None,
    ) -> None:
        """Store short-lived structured tool state for a specific chat."""
        client = await self._get_client()
        if client is None:
            return

        try:
            await client.set(self._state_key(user_id, name, conversation_id), json.dumps(value), ex=ttl_seconds)
        except Exception as e:
            logger.warning(f"Failed to write Redis tool state {name}: {e}")

    async def delete_state(self, user_id: str, name: str, conversation_id: str | None = None) -> None:
        """Delete short-lived structured tool state for a specific chat."""
        client = await self._get_client()
        if client is None:
            return

        try:
            await client.delete(self._state_key(user_id, name, conversation_id))
        except Exception as e:
            logger.warning(f"Failed to delete Redis tool state {name}: {e}")

    async def delete_conversation(self, user_id: str, conversation_id: str) -> None:
        """Delete all Redis short memory and pending tool state for one chat."""
        client = await self._get_client()
        if client is None:
            return

        scope = self._scope(conversation_id)
        keys = [self._key(user_id, scope)]
        try:
            async for key in client.scan_iter(match=f"coolie:tool-state:{user_id}:{scope}:*", count=100):
                keys.append(key)
            if keys:
                await client.delete(*keys)
        except Exception as e:
            logger.warning(f"Failed to delete Redis chat scope {scope}: {e}")


redis_memory_service = RedisMemoryService()
