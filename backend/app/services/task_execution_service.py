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
    """Execute only a previously approved, structured Gmail send task."""
    message = str(task.get("description") or task.get("title") or "").strip()
    metadata = task.get("metadata") if isinstance(task.get("metadata"), dict) else {}

    if metadata.get("gmail_action") != "send" or not metadata.get("gmail_approved_at"):
        raise RuntimeError(
            "This scheduled Gmail task has no approved structured email payload. "
            "Create it again through the AgentCoolie chat confirmation flow."
        )

    tool_status = await n8n_service.gmail_status(user_id)
    if not tool_status.get("configured"):
        raise RuntimeError("Gmail automation is not configured on the backend.")
    if tool_status.get("storage_error"):
        raise RuntimeError(tool_status.get("message") or "Could not verify Gmail connection because Supabase is unreachable.")
    if not tool_status.get("connected"):
        raise RuntimeError("Gmail is not connected. Connect Gmail in Settings first.")

    gmail_to = _valid_email(metadata.get("gmail_to"))
    body = str(metadata.get("gmail_body") or "").strip()
    subject = str(metadata.get("gmail_subject") or "Message from AgentCoolie").strip()
    if not gmail_to or not body:
        raise RuntimeError("This scheduled Gmail task is missing a valid recipient or email body.")
    if len(subject) > 180 or len(body) > 10000:
        raise RuntimeError("This scheduled Gmail task exceeds email size limits.")

    result = await n8n_service.run_gmail_action(
        user_id,
        message,
        action="send",
        payload={"to": gmail_to, "subject": subject, "body": body},
    )

    if not result.get("ok"):
        raise RuntimeError(str(result.get("message") or result.get("body") or "Gmail workflow failed."))

    return result
