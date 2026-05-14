"""Shared helpers for executing scheduled task side effects."""

from __future__ import annotations

import re
from typing import Any

from app.services.n8n_service import n8n_service


def _valid_email(value: str | None) -> str | None:
    email = str(value or "").strip()
    if not email:
        return None
    return email if re.fullmatch(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", email) else None


async def execute_gmail_task(user_id: str, task: dict[str, Any]) -> dict[str, Any]:
    """Execute a persisted Gmail task using metadata captured at creation time."""
    message = str(task.get("description") or task.get("title") or "").strip()
    metadata = task.get("metadata") if isinstance(task.get("metadata"), dict) else {}

    tool_status = await n8n_service.gmail_status(user_id)
    if not tool_status.get("configured"):
        raise RuntimeError("Gmail automation is not configured on the backend.")
    if tool_status.get("storage_error"):
        raise RuntimeError(tool_status.get("message") or "Could not verify Gmail connection because Supabase is unreachable.")
    if not tool_status.get("connected"):
        raise RuntimeError("Gmail is not connected. Connect Gmail in Settings first.")

    gmail_to = _valid_email(metadata.get("gmail_to"))
    if gmail_to:
        body = str(metadata.get("gmail_body") or message).strip()
        result = await n8n_service.run_gmail_action(
            user_id,
            message,
            action="send",
            payload={
                "to": gmail_to,
                "subject": metadata.get("gmail_subject") or "Message from AgentCoolie",
                "body": body,
            },
        )
    else:
        result = await n8n_service.run_gmail_action(user_id, message)

    if not result.get("ok"):
        raise RuntimeError(str(result.get("message") or result.get("body") or "Gmail workflow failed."))

    return result
