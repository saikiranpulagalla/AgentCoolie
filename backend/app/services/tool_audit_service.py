"""Best-effort audit events for side-effecting tools.

Audit writes must never block the user's action. They use the existing
usage_events table with feature="tool_audit" so deployments do not need a
separate migration before the app can benefit from better observability.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)

SENSITIVE_KEY_PARTS = (
    "access_token",
    "api_key",
    "authorization",
    "client_secret",
    "credential",
    "password",
    "refresh_token",
    "secret",
    "token",
)

LARGE_TEXT_KEYS = {"body", "message", "raw", "text", "content"}
MAX_STRING_PREVIEW = 180


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _sanitize(value: Any, *, key: str | None = None, depth: int = 0) -> Any:
    """Remove secrets and shrink large text while preserving debugging shape."""
    normalized_key = (key or "").lower()
    if any(part in normalized_key for part in SENSITIVE_KEY_PARTS):
        return "[redacted]"

    if depth > 5:
        return "[truncated-depth]"

    if isinstance(value, dict):
        return {
            str(item_key): _sanitize(item_value, key=str(item_key), depth=depth + 1)
            for item_key, item_value in value.items()
        }

    if isinstance(value, list):
        items = [_sanitize(item, key=key, depth=depth + 1) for item in value[:20]]
        if len(value) > 20:
            items.append(f"[{len(value) - 20} more items]")
        return items

    if isinstance(value, str):
        text = value.strip()
        if normalized_key in LARGE_TEXT_KEYS or len(text) > MAX_STRING_PREVIEW:
            return {
                "preview": text[:MAX_STRING_PREVIEW],
                "length": len(text),
                "sha256_16": _hash_text(text),
            }
        return text

    if isinstance(value, (int, float, bool)) or value is None:
        return value

    return str(value)[:MAX_STRING_PREVIEW]


class ToolAuditService:
    async def record(
        self,
        user_id: str | None,
        *,
        tool: str,
        action: str,
        stage: str,
        status: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Best-effort append-only event for side-effecting tool workflows."""
        if not user_id:
            return

        payload = {
            "tool": tool,
            "action": action,
            "stage": stage,
            "status": status,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "metadata": _sanitize(metadata or {}),
        }

        try:
            await supabase_service.create_usage_event(
                user_id=user_id,
                feature="tool_audit",
                amount=1,
                metadata=payload,
            )
        except Exception as e:
            logger.warning("Tool audit write failed for %s/%s/%s: %s", tool, action, stage, e)


tool_audit_service = ToolAuditService()
