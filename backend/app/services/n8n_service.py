"""n8n webhook client for external automation tools."""

from __future__ import annotations

import logging
import re
from typing import Any

import aiohttp

from app.core.config import settings
from app.services.plan_service import plan_service
from app.services.runtime_config_service import runtime_config_service
from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)


class N8NService:
    def __init__(self) -> None:
        self.gmail_action_path = settings.N8N_GMAIL_ACTION_PATH
        self.gmail_credentials_path = settings.N8N_GMAIL_CREDENTIALS_PATH

    async def _config(self) -> dict[str, str | None]:
        values = await runtime_config_service.get_secrets(
            [
                "N8N_BASE_URL",
                "N8N_GMAIL_ACTION_PATH",
                "N8N_GMAIL_CREDENTIALS_PATH",
                "N8N_TOOL_SECRET",
            ]
        )
        values["N8N_GMAIL_ACTION_PATH"] = values.get("N8N_GMAIL_ACTION_PATH") or self.gmail_action_path
        values["N8N_GMAIL_CREDENTIALS_PATH"] = values.get("N8N_GMAIL_CREDENTIALS_PATH") or self.gmail_credentials_path
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

        path = config.get(path) if path in {"N8N_GMAIL_ACTION_PATH", "N8N_GMAIL_CREDENTIALS_PATH"} else path
        url = self._url(base_url, path or "")
        headers = {}
        tool_secret = config.get("N8N_TOOL_SECRET")
        if settings.ENV.lower() != "development" and not tool_secret:
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

    async def save_gmail_credentials(
        self,
        user_id: str,
        credentials: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return await self._post(
            "N8N_GMAIL_CREDENTIALS_PATH",
            {
                "userId": user_id,
                "credentials": credentials,
            },
        )

    async def run_gmail_action(
        self,
        user_id: str,
        message: str,
        action: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not await supabase_service.get_credentials(user_id, "gmail"):
            return {
                "ok": False,
                "status": 409,
                "message": "Gmail is not connected. Connect Gmail in Settings first.",
            }

        planned_payload = payload or {}
        if not action:
            action, planned_payload, planner_message = self.plan_gmail_action(message)
            if not action:
                return {
                    "ok": False,
                    "status": 400,
                    "message": planner_message or "Please specify a Gmail action.",
                }

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
        return result

    async def gmail_status(self, user_id: str) -> dict[str, Any]:
        """Return whether Gmail can be used for this user before running a tool call."""
        connected = False
        try:
            connected = bool(await supabase_service.get_credentials(user_id, "gmail"))
        except Exception as e:
            logger.warning(f"Could not check Gmail credentials for {user_id}: {e}")

        configured = await self.is_configured()
        return {
            "configured": configured,
            "connected": connected,
            "base_url": configured,
        }


n8n_service = N8NService()
