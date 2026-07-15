"""Twilio-backed phone call reminders for critical tasks."""

from __future__ import annotations

import asyncio
import html
import logging
import re
from datetime import datetime, timezone
from typing import Any

import requests

from app.core.config import settings
from app.services.plan_service import plan_service
from app.services.runtime_config_service import runtime_config_service
from app.services.supabase_service import supabase_service
from app.services.tool_audit_service import tool_audit_service

logger = logging.getLogger(__name__)

PHONE_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


class CallReminderError(RuntimeError):
    """User-safe call reminder failure with optional provider metadata."""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        provider_status: int | None = None,
        more_info: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.provider_status = provider_status
        self.more_info = more_info


def _friendly_twilio_error(status_code: int, payload: dict[str, Any] | None, raw_text: str) -> CallReminderError:
    code = str((payload or {}).get("code") or "")
    provider_message = str((payload or {}).get("message") or raw_text or "").strip()
    more_info = str((payload or {}).get("more_info") or "").strip() or None

    if code == "21219" or "unverified" in provider_message.lower():
        return CallReminderError(
            (
                "I could not place the call because this phone number is not verified in your Twilio trial account. "
                "Open Twilio Console and verify this recipient number, or save a verified call number in Settings."
            ),
            code="twilio_unverified_number",
            provider_status=status_code,
            more_info=more_info,
        )

    if code in {"21211", "21217"} or "invalid" in provider_message.lower():
        return CallReminderError(
            "I could not place the call because the phone number looks invalid. Save it in E.164 format, for example +919000000000.",
            code="invalid_phone_number",
            provider_status=status_code,
            more_info=more_info,
        )

    if code == "21606" or "from" in provider_message.lower() and "not" in provider_message.lower():
        return CallReminderError(
            "I could not place the call because the Twilio caller number is not configured correctly.",
            code="twilio_from_number_invalid",
            provider_status=status_code,
            more_info=more_info,
        )

    return CallReminderError(
        "I could not place the call right now. Please check the saved phone number and Twilio setup, then try again.",
        code=f"twilio_{code}" if code else "twilio_call_failed",
        provider_status=status_code,
        more_info=more_info,
    )


def normalize_phone_number(value: str | None) -> str | None:
    """Normalize a phone number to basic E.164, with India-friendly handling."""
    digits = re.sub(r"\D", "", value or "")
    if not digits:
        return None
    if value and value.strip().startswith("+"):
        candidate = f"+{digits}"
    elif len(digits) == 10 and re.match(r"^[6-9]", digits):
        candidate = f"+91{digits}"
    elif len(digits) == 12 and digits.startswith("91"):
        candidate = f"+{digits}"
    else:
        candidate = f"+{digits}"
    return candidate if PHONE_PATTERN.match(candidate) else None


def _task_metadata(task: dict[str, Any]) -> dict[str, Any]:
    metadata = task.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def task_wants_call(task: dict[str, Any]) -> bool:
    metadata = _task_metadata(task)
    return bool(metadata.get("notify_by_call") or metadata.get("call_reminder"))


def _safe_task_detail(task: dict[str, Any]) -> str:
    detail = str(task.get("description") or task.get("title") or "your task").strip()
    detail = re.sub(r"\s+", " ", detail)
    detail = detail.replace("<", " ").replace(">", " ")
    if len(detail) > 180:
        detail = detail[:177].rstrip() + "..."
    return detail or "your task"


def build_tenglish_call_message(task: dict[str, Any]) -> str:
    """Build a task-specific Tenglish reminder for Twilio text-to-speech."""
    detail = _safe_task_detail(task)
    return (
        "Idi AgentCoolie reminder. "
        f"Mee important task ippudu due ayyindi: {detail}. "
        "Dayachesi ventane complete cheyyandi."
    )


class CallReminderService:
    async def get_twilio_config(self) -> dict[str, str | None]:
        return await runtime_config_service.get_secrets(
            ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER"]
        )

    async def is_configured(self) -> bool:
        config = await self.get_twilio_config()
        return bool(
            config.get("TWILIO_ACCOUNT_SID")
            and config.get("TWILIO_AUTH_TOKEN")
            and config.get("TWILIO_FROM_NUMBER")
        )

    def task_wants_call(self, task: dict[str, Any]) -> bool:
        return task_wants_call(task)

    async def get_user_phone(self, user_id: str) -> str | None:
        credentials = await supabase_service.get_credentials(user_id, "call_reminder")
        data = credentials.get("data") if credentials else None
        if not isinstance(data, dict):
            return None
        return normalize_phone_number(str(data.get("phone_number") or ""))

    async def save_user_phone(self, user_id: str, phone_number: str) -> dict[str, Any]:
        normalized = normalize_phone_number(phone_number)
        if not normalized:
            raise ValueError("Phone number must be in E.164 format, e.g. +919000000000")
        return await supabase_service.save_credentials(
            user_id,
            "call_reminder",
            {"phone_number": normalized},
        )

    async def delete_user_phone(self, user_id: str) -> bool:
        return await supabase_service.delete_credentials(user_id, "call_reminder")

    async def resolve_task_phone(self, task: dict[str, Any]) -> str | None:
        metadata = _task_metadata(task)
        task_phone = normalize_phone_number(str(metadata.get("call_phone") or ""))
        user_id = str(task.get("user_id") or "")
        saved_phone = await self.get_user_phone(user_id) if user_id else None
        if task_phone and task_phone != saved_phone:
            raise RuntimeError(
                "Call reminders can only use the phone number saved in your AgentCoolie Settings."
            )
        return saved_phone

    async def place_task_call(self, task: dict[str, Any]) -> dict[str, Any]:
        user_id = str(task.get("user_id") or "")
        task_id = str(task.get("id") or "")
        config = await self.get_twilio_config()
        account_sid = config.get("TWILIO_ACCOUNT_SID")
        auth_token = config.get("TWILIO_AUTH_TOKEN")
        from_number = config.get("TWILIO_FROM_NUMBER")
        if not account_sid or not auth_token or not from_number:
            await tool_audit_service.record(
                user_id,
                tool="call_reminder",
                action="place_call",
                stage="blocked",
                status="not_configured",
                metadata={"task_id": task_id},
            )
            raise RuntimeError("Twilio call reminders are not configured on the backend.")

        to_number = await self.resolve_task_phone(task)
        if not to_number:
            await tool_audit_service.record(
                user_id,
                tool="call_reminder",
                action="place_call",
                stage="blocked",
                status="missing_phone",
                metadata={"task_id": task_id},
            )
            raise RuntimeError("No call-reminder phone number is saved for this user.")

        metadata = _task_metadata(task)
        if user_id and not metadata.get("call_quota_reserved"):
            await plan_service.check_and_consume(
                user_id,
                "call_reminders",
                metadata={"source": "task_call", "task_id": task.get("id")},
            )

        message = build_tenglish_call_message(task)
        twiml = (
            "<Response>"
            f"<Say voice=\"alice\">{html.escape(message)}</Say>"
            "</Response>"
        )

        await tool_audit_service.record(
            user_id,
            tool="call_reminder",
            action="place_call",
            stage="started",
            status="pending",
            metadata={"task_id": task_id, "to": to_number, "message": message},
        )

        def _send() -> dict[str, Any]:
            response = requests.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json",
                data={
                    "To": to_number,
                    "From": from_number,
                    "Twiml": twiml,
                },
                auth=(account_sid, auth_token),
                timeout=30,
            )
            if response.status_code >= 400:
                try:
                    payload = response.json()
                except ValueError:
                    payload = None
                raise _friendly_twilio_error(response.status_code, payload, response.text[:300])
            return response.json()

        try:
            result = await asyncio.to_thread(_send)
        except Exception as e:
            await tool_audit_service.record(
                user_id,
                tool="call_reminder",
                action="place_call",
                stage="completed",
                status="failed",
                metadata={
                    "task_id": task_id,
                    "to": to_number,
                    "error": str(e),
                    "error_code": getattr(e, "code", None),
                    "provider_status": getattr(e, "provider_status", None),
                    "more_info": getattr(e, "more_info", None),
                },
            )
            raise

        await tool_audit_service.record(
            user_id,
            tool="call_reminder",
            action="place_call",
            stage="completed",
            status="success",
            metadata={
                "task_id": task_id,
                "to": to_number,
                "sid": result.get("sid"),
                "provider_status": result.get("status"),
            },
        )
        return {
            "provider": "twilio",
            "to": to_number,
            "message": message,
            "sid": result.get("sid"),
            "provider_status": result.get("status"),
            "called_at": datetime.now(timezone.utc).isoformat(),
        }


call_reminder_service = CallReminderService()
