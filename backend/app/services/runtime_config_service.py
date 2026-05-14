"""Runtime configuration loaded from Supabase with env fallback."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Iterable

from app.core.config import settings
from app.services.supabase_service import is_connectivity_error, supabase_service

logger = logging.getLogger(__name__)


class RuntimeConfigService:
    """Read provider secrets without requiring a redeploy for every rotation."""

    def __init__(self, cache_ttl_seconds: int = 60) -> None:
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, tuple[float, str | None]] = {}

    def clear_cache(self) -> None:
        self._cache.clear()

    def _env_value(self, key: str, default: str | None = None) -> str | None:
        value = getattr(settings, key, None)
        return str(value) if value not in (None, "") else default

    async def get_secret(self, key: str, default: str | None = None) -> str | None:
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached and cached[0] > now:
            return cached[1] if cached[1] not in (None, "") else self._env_value(key, default)

        try:
            def _get():
                return (
                    supabase_service.client.table("app_secrets")
                    .select("value,is_enabled")
                    .eq("key", key)
                    .eq("is_enabled", True)
                    .limit(1)
                    .execute()
                )

            response = await asyncio.to_thread(_get)
            value = response.data[0].get("value") if response.data else None
            if value:
                value = str(value)
            self._cache[key] = (now + self.cache_ttl_seconds, value)
            return value if value not in (None, "") else self._env_value(key, default)
        except Exception as e:
            if is_connectivity_error(e):
                logger.warning(f"Runtime secret lookup skipped because Supabase is unreachable: {key}")
            else:
                logger.warning(f"Runtime secret lookup failed for {key}: {e}")
            return self._env_value(key, default)

    async def get_secrets(self, keys: Iterable[str]) -> dict[str, str | None]:
        values: dict[str, str | None] = {}
        for key in keys:
            values[key] = await self.get_secret(key)
        return values


runtime_config_service = RuntimeConfigService()
