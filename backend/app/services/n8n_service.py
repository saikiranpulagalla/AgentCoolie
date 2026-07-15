"""n8n webhook client for external automation tools."""

from __future__ import annotations

import logging
import re
from typing import Any

import aiohttp

from app.core.config import settings
from app.services.plan_service import plan_service
from app.services.runtime_config_service import runtime_config_service
from app.services.supabase_service import is_connectivity_error, supabase_service
from app.services.tool_audit_service import tool_audit_service

logger = logging.getLogger(__name__)

GMAIL_ACTIONS = frozenset({
    "send", "list", "get", "listByLabel", "markRead", "markUnread",
    "addLabel", "removeLabel", "delete", "reply", "search",
})
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}")
_MESSAGE_ID_RE = re.compile(r"[A-Za-z0-9_-]{6,256}")
_LABEL_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,256}")


class N8NService:
    def __init__(self) -> None:
        self.gmail_action_path = settings.N8N_GMAIL_ACTION_PATH

    async def _config(self) -> dict[str, str | None]:
        values = await runtime_config_service.get_secrets(
            [
                "N8N_BASE_URL",
                "N8N_GMAIL_ACTION_PATH",
                "N8N_TOOL_SECRET",
            ]
        )
        values["N8N_GMAIL_ACTION_PATH"] = values.get("N8N_GMAIL_ACTION_PATH") or self.gmail_action_path
        return values

    async def is_configured(self) -> bool:
        config = await self._config()
        return bool((config.get("N8N_BASE_URL") or "").strip())

    def _url(self, base_url: str, path: str) -> str:
        clean_path = path if path.startswith("/") else f"/{path}"
        return f"{base_url.rstrip('/')}{clean_path}"

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        config = await self._config()
        base_url = (config.get("N8N_BASE_URL") or "").rstrip("/")
        if not base_url:
            return {
                "ok": False,
                "status": 503,
                "message": "n8n is not configured for this backend.",
            }

        path = config.get(path) if path == "N8N_GMAIL_ACTION_PATH" else path
        url = self._url(base_url, path or "")
        headers = {}
        tool_secret = config.get("N8N_TOOL_SECRET")
        if not settings.is_local_runtime() and not tool_secret:
            return {
                "ok": False,
                "status": 503,
                "message": "n8n tool secret is not configured for production.",
            }
        if tool_secret:
            headers["x-agentcoolie-secret"] = tool_secret
        if payload.get("userId"):
            headers["x-user-id"] = str(payload["userId"])
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=45)) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    text = await response.text()
                    try:
                        body = await response.json(content_type=None)
                    except Exception:
                        body = {"text": text}
                    return {
                        "ok": 200 <= response.status < 300,
                        "status": response.status,
                        "body": body,
                    }
        except Exception as e:
            logger.warning(f"n8n webhook request failed for {url}: {e}")
            return {
                "ok": False,
                "status": 502,
                "message": f"Could not reach n8n workflow: {e}",
            }

    def plan_gmail_action(self, message: str) -> tuple[str | None, dict[str, Any], str | None]:
        """Small deterministic planner for common Gmail commands."""
        text = " ".join(message.strip().split())
        lower = text.lower()

        if any(word in lower for word in ("latest", "recent", "check", "read", "list", "inbox", "unread")):
            query = ""
            if "unread" in lower:
                query = "is:unread"
            return "list", {"maxResults": 5, "query": query}, None

        if "search" in lower or "find" in lower:
            query = re.sub(r"\b(search|find|gmail|email|mail|for|in|my)\b", " ", text, flags=re.I)
            query = " ".join(query.split())
            return "search", {"maxResults": 10, "query": query or text}, None

        if "send" in lower:
            email_match = re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text)
            if not email_match:
                return None, {}, "Who should I send the email to?"
            subject_match = re.search(r"\bsubject\s+(.+?)(?:\s+body\s+|\s+message\s+|$)", text, re.I)
            body_match = re.search(r"\b(?:body|message|saying|that says)\s+(.+)$", text, re.I)
            subject = subject_match.group(1).strip() if subject_match else "Message from AgentCoolie"
            if body_match:
                body = body_match.group(1).strip()
            else:
                body = text[: email_match.start()] + text[email_match.end() :]
                body = re.sub(r"\bsubject\s+.+$", " ", body, flags=re.I)
                body = re.sub(
                    r"^(?:can\s+(?:you|u)|could\s+(?:you|u)|would\s+you|will\s+you|please)\s+",
                    "",
                    body,
                    flags=re.I,
                )
                body = re.sub(r"^\s*send(?:\s+(?:an?|the))?(?:\s+(?:email|gmail|mail|message))?\s*", "", body, flags=re.I)
                body = re.sub(r"\b(?:to|for)\s*$", "", body, flags=re.I)
                body = re.sub(r"\s+", " ", body).strip(" ,.-:")
            body = re.sub(r"\s+\bto\s+[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}\s*$", "", body, flags=re.I).strip()
            body = re.sub(r"^(?:a\s+)?message\s*:\s*", "", body, flags=re.I).strip()
            body = re.sub(r"^(?:a\s+)?message\s+", "", body, flags=re.I).strip()
            if not body:
                return None, {}, "What message should I send?"
            return "send", {"to": email_match.group(0), "subject": subject, "body": body}, None

        return None, {}, "I can use Gmail for list, search, and send actions. Please specify what you want to do."

    def _validate_gmail_action(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Reject malformed or unexpected n8n actions before they cross the tool boundary."""
        if action not in GMAIL_ACTIONS:
            raise ValueError("Unsupported Gmail action")

        normalized = dict(payload or {})
        try:
            max_results = int(normalized.get("maxResults", 10))
        except (TypeError, ValueError) as e:
            raise ValueError("maxResults must be a number") from e
        if action in {"list", "listByLabel", "search"}:
            normalized["maxResults"] = max(1, min(max_results, 20))
            query = str(normalized.get("query") or "").strip()
            if len(query) > 500:
                raise ValueError("Gmail search queries are limited to 500 characters")
            normalized["query"] = query

        if action == "send":
            recipient = str(normalized.get("to") or normalized.get("recipient") or "").strip()
            subject = str(normalized.get("subject") or "Message from AgentCoolie").strip()
            body = str(normalized.get("body") or "").strip()
            if not _EMAIL_RE.fullmatch(recipient):
                raise ValueError("A valid recipient email is required")
            if not body:
                raise ValueError("Email body is required")
            if len(subject) > 180 or len(body) > 10000:
                raise ValueError("Email subject or body is too long")
            return {"to": recipient, "subject": subject, "body": body}

        if action in {"get", "markRead", "markUnread", "addLabel", "removeLabel", "delete"}:
            message_id = str(normalized.get("messageId") or "").strip()
            if not _MESSAGE_ID_RE.fullmatch(message_id):
                raise ValueError("A valid Gmail message id is required")
            normalized["messageId"] = message_id

        if action in {"addLabel", "removeLabel"}:
            label_ids = normalized.get("labelIds")
            if not isinstance(label_ids, list) or not 1 <= len(label_ids) <= 10:
                raise ValueError("Provide between one and ten Gmail label ids")
            if not all(_LABEL_ID_RE.fullmatch(str(label_id or "")) for label_id in label_ids):
                raise ValueError("One or more Gmail label ids are invalid")
            normalized["labelIds"] = [str(label_id) for label_id in label_ids]

        if action == "reply":
            recipient = str(normalized.get("to") or "").strip()
            thread_id = str(normalized.get("threadId") or "").strip()
            body = str(normalized.get("body") or "").strip()
            if not _EMAIL_RE.fullmatch(recipient) or not _MESSAGE_ID_RE.fullmatch(thread_id) or not body:
                raise ValueError("Reply requires a valid recipient, thread id, and message body")
            if len(body) > 10000:
                raise ValueError("Reply body is too long")
            normalized.update({"to": recipient, "threadId": thread_id, "body": body})

        return normalized

    def _audit_payload(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Keep audit usefulness without copying full private email bodies into logs."""
        safe = {"action": action}
        if payload.get("to"):
            safe["to"] = str(payload["to"])
        if payload.get("messageId"):
            safe["message_id"] = str(payload["messageId"])
        if payload.get("query"):
            safe["query_length"] = len(str(payload["query"]))
        if payload.get("body"):
            safe["body_length"] = len(str(payload["body"]))
        return safe

    async def run_gmail_action(
        self,
        user_id: str,
        message: str,
        action: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not await supabase_service.get_credentials(user_id, "gmail"):
            await tool_audit_service.record(
                user_id,
                tool="gmail",
                action=action or "unknown",
                stage="blocked",
                status="not_connected",
                metadata={"reason": "missing_gmail_credentials"},
            )
            return {
                "ok": False,
                "status": 409,
                "message": "Gmail is not connected. Connect Gmail in Settings first.",
            }

        planned_payload = payload or {}
        if not action:
            action, planned_payload, planner_message = self.plan_gmail_action(message)
            if not action:
                await tool_audit_service.record(
                    user_id,
                    tool="gmail",
                    action="plan",
                    stage="blocked",
                    status="planner_error",
                    metadata={"message": message, "planner_message": planner_message},
                )
                return {
                    "ok": False,
                    "status": 400,
                    "message": planner_message or "Please specify a Gmail action.",
                }

        try:
            planned_payload = self._validate_gmail_action(str(action), planned_payload)
        except ValueError as e:
            await tool_audit_service.record(
                user_id,
                tool="gmail",
                action=str(action),
                stage="blocked",
                status="invalid_payload",
                metadata={"reason": str(e)},
            )
            return {"ok": False, "status": 400, "message": str(e)}

        feature = "gmail_reads"
        if action in {"send", "reply", "delete"}:
            feature = "gmail_sends"
        elif action == "draft":
            feature = "gmail_drafts"
        await plan_service.check_and_consume(
            user_id,
            feature,
            metadata={"source": "n8n_gmail", "action": action},
        )

        await tool_audit_service.record(
            user_id,
            tool="gmail",
            action=action,
            stage="started",
            status="pending",
            metadata={"feature": feature, **self._audit_payload(str(action), planned_payload)},
        )
        result = await self._post(
            "N8N_GMAIL_ACTION_PATH",
            {
                "userId": user_id,
                "message": message,
                "action": action,
                "payload": planned_payload,
            },
        )
        result["action"] = action
        result["payload"] = planned_payload
        await tool_audit_service.record(
            user_id,
            tool="gmail",
            action=action,
            stage="completed",
            status="success" if result.get("ok") else "failed",
            metadata={
                "provider_status": result.get("status"),
                "message": result.get("message"),
                **self._audit_payload(str(action), planned_payload),
            },
        )
        return result

    async def gmail_status(self, user_id: str) -> dict[str, Any]:
        """Return whether Gmail can be used for this user before running a tool call."""
        connected = False
        try:
            connected = bool(await supabase_service.get_credentials(user_id, "gmail"))
        except Exception as e:
            logger.warning(f"Could not check Gmail credentials for {user_id}: {e}")
            if is_connectivity_error(e):
                return {
                    "configured": await self.is_configured(),
                    "connected": False,
                    "storage_error": True,
                    "message": "Could not reach Supabase to check Gmail connection status.",
                }

        configured = await self.is_configured()
        return {
            "configured": configured,
            "connected": connected,
            "base_url": configured,
        }


n8n_service = N8NService()
