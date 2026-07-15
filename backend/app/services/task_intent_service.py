"""Natural-language task creation helpers."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any, Optional

from app.core.config import settings
from app.services.ai_service import gemini_service
from app.services.n8n_service import n8n_service
from app.services.plan_service import plan_service
from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)

TASK_TYPES = {"general", "youtube", "website", "gmail"}
PRIORITIES = {"low", "medium", "high"}
CALL_REMINDER_PATTERN = re.compile(
    r"\b("
    r"call me|phone call|notify (?:me )?by call|remind (?:me )?by call|"
    r"important.*call|urgent.*call|call reminder"
    r")\b",
    re.IGNORECASE,
)

CORE_TRIGGER_PATTERN = re.compile(
    r"\b("
    r"remind me|set (?:a )?(?:reminder|remainder)|create\s+(?:(?:a|the|to)\s+)?(?:task|reminder|remainder)|"
    r"add (?:a )?(?:task|reminder|remainder)|make (?:a )?(?:task|reminder|remainder)|task to|schedule|tomorrow|today|tonight|"
    r"next (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
    r")\b",
    re.IGNORECASE,
)
TIME_PATTERN = re.compile(r"\bat\s+\d{1,2}(?:(?::|\.)\d{2})?\s*(?:am|pm)?\b", re.IGNORECASE)
TIME_DETAIL_PATTERN = re.compile(
    r"\b(?:at|by|time\s*(?:to|is)?|change\s+(?:the\s+)?time\s+to)\s+"
    r"(\d{1,2})(?:(?::|\.)(\d{2}))?\s*(am|pm)?\b",
    re.IGNORECASE,
)
ACTION_PATTERN = re.compile(
    r"\b(open|play|review|send|call|message|email|watch|read|check|do)\b",
    re.IGNORECASE,
)
WEEKDAY_INDEXES = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _local_now() -> datetime:
    try:
        return datetime.now(ZoneInfo(settings.APP_TIMEZONE))
    except Exception:
        return datetime.now().astimezone()


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}


def _normalize_due_date(value: Any) -> Optional[str]:
    if not value:
        return None

    text = str(value).strip()
    if not text or text.lower() == "null":
        return None

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat()


def _fallback_due_date(message: str) -> Optional[str]:
    lowered = message.lower()
    now = _local_now()

    relative_match = re.search(r"\bin\s+(\d{1,4})\s*(minute|minutes|min|mins|hour|hours|hr|hrs)\b", lowered)
    if relative_match:
        amount = int(relative_match.group(1))
        unit = relative_match.group(2)
        if unit.startswith(("hour", "hr")):
            return (now + timedelta(hours=amount)).isoformat()
        return (now + timedelta(minutes=amount)).isoformat()

    time_matches = list(TIME_DETAIL_PATTERN.finditer(lowered))
    if not time_matches:
        return None
    time_match = time_matches[-1]

    hour = int(time_match.group(1))
    minute = int(time_match.group(2) or 0)
    meridiem = time_match.group(3)
    if not meridiem:
        for previous_match in reversed(time_matches[:-1]):
            if previous_match.group(3):
                meridiem = previous_match.group(3)
                break
    if meridiem == "pm" and hour < 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0

    if hour > 23 or minute > 59:
        return None

    explicit_today = "today" in lowered
    if "tomorrow" in lowered:
        target_date = now.date() + timedelta(days=1)
    elif explicit_today or "tonight" in lowered:
        target_date = now.date()
    elif weekday_match := re.search(r"\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", lowered):
        target_weekday = WEEKDAY_INDEXES[weekday_match.group(1)]
        days_ahead = (target_weekday - now.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        target_date = now.date() + timedelta(days=days_ahead)
    else:
        target_date = now.date()

    due_at = datetime.combine(target_date, time(hour=hour, minute=minute), tzinfo=now.tzinfo)
    if due_at <= now and not (explicit_today or "tonight" in lowered or "tomorrow" in lowered or "next " in lowered):
        due_at += timedelta(days=1)
    return due_at.isoformat()


def _extract_action_after_time(message: str) -> Optional[str]:
    """Prefer the action after a relative time expression: "today at 2.05 pm to call Surya"."""
    relative_match = re.search(
        r"\bin\s+\d{1,4}\s*(?:minute|minutes|min|mins|hour|hours|hr|hrs)\s*(?:to|for|that|and)?\s+(.+)$",
        message,
        re.IGNORECASE,
    )
    if relative_match:
        action = relative_match.group(1).strip(" .,-")
        if action.lower() in {"am", "pm"}:
            return None
        action = re.sub(r"^(?:say\s+to|tell\s+me\s+to|remind\s+me\s+to|to)\s+", "", action, flags=re.IGNORECASE)
        return action.strip() or None

    match = re.search(
        r"\b(?:today|tomorrow|tonight)?\s*(?:at|by|time\s*(?:to|is)?|change\s+(?:the\s+)?time\s+to)\s+"
        r"\d{1,2}(?:(?::|\.)\d{2})?\s*(?:am|pm)?\s*(?:to|for|that|and)?\s+(.+)$",
        message,
        re.IGNORECASE,
    )
    if not match:
        return None

    action = match.group(1).strip(" .,-")
    if action.lower() in {"am", "pm"}:
        return None
    action = re.sub(r"^(?:say\s+to|tell\s+me\s+to|remind\s+me\s+to|to)\s+", "", action, flags=re.IGNORECASE)
    return action.strip() or None


def _clean_task_text(message: str) -> str:
    action_after_time = _extract_action_after_time(message)
    if action_after_time:
        return action_after_time

    text = re.sub(
        r"^\s*(?:can\s+(?:you|u)\s+)?(?:please\s+)?(?:create|add|make|set)\s+(?:(?:a|the|to)\s+)?(?:task|reminder|remainder)\s+(?:to\s+)?",
        "",
        message,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\b(?:today|tomorrow|tonight)\b.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\b(?:at|by|time\s*(?:to|is)?|change\s+(?:the\s+)?time\s+to)\s+\d{1,2}(?:(?::|\.)\d{2})?\s*(?:am|pm)?\b",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip(" .,-")
    return text.strip() or message.strip()


def _extract_multi_task_items(message: str) -> list[str]:
    """Extract explicit "another task" style requests into separate task texts."""
    if not re.search(r"\banother\s+(?:task|reminder|remainder)\b|\btask\s*\d+\b", message, re.IGNORECASE):
        return []

    candidate = message.strip()
    sentence_with_split = [
        part.strip()
        for part in re.split(r"[.;]\s+", candidate)
        if re.search(r"\banother\s+(?:task|reminder|remainder)\b", part, re.IGNORECASE)
    ]
    if sentence_with_split:
        candidate = sentence_with_split[0]

    candidate = re.sub(
        r"\s+(?:and\s+)?another\s+(?:task|reminder|remainder)\s+(?:to|for)?\s+",
        " ||| ",
        candidate,
        flags=re.IGNORECASE,
    )
    candidate = re.sub(
        r"\s+(?:and\s+)?task\s*\d+\s+(?:to|for)\s+",
        " ||| ",
        candidate,
        flags=re.IGNORECASE,
    )

    items: list[str] = []
    seen: set[str] = set()
    for raw_part in candidate.split("|||"):
        part = raw_part.strip(" .,-")
        if not part:
            continue
        cleaned = _clean_task_text(part)
        cleaned = re.sub(r"^(?:and\s+)?task\s*\d+\s*(?:and\s*\d+)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^(?:to|for)\s+", "", cleaned, flags=re.IGNORECASE).strip(" .,-")
        normalized = re.sub(r"\s+", " ", cleaned).strip()
        key = normalized.lower()
        if not normalized or _is_generic_task_text(normalized) or key in seen:
            continue
        seen.add(key)
        items.append(normalized)

    return items if len(items) > 1 else []


def _normalize_type(message: str, value: Any) -> str:
    raw_type = str(value or "").strip().lower()
    if raw_type in {"reminder", "task"}:
        raw_type = "general"
    if raw_type in TASK_TYPES:
        return raw_type

    lowered = message.lower()
    if "youtube" in lowered or "song" in lowered or "video" in lowered:
        return "youtube"
    if "website" in lowered or "site" in lowered or re.search(r"\b(open|visit|go to)\b", lowered):
        return "website"
    if "whatsapp" in lowered:
        return "general"
    if "gmail" in lowered or "email" in lowered:
        return "gmail"
    return "general"


def _normalize_priority(value: Any) -> str:
    priority = str(value or "medium").strip().lower()
    if priority == "urgent":
        return "high"
    return priority if priority in PRIORITIES else "medium"


def _wants_call_reminder(message: str, value: Any = None) -> bool:
    if isinstance(value, bool):
        return value
    raw = str(value or "").strip().lower()
    if raw in {"true", "yes", "1", "call", "phone"}:
        return True
    return bool(CALL_REMINDER_PATTERN.search(message))


def _is_generic_task_text(value: str) -> bool:
    return bool(
        re.fullmatch(
            r"(?:task|task reminder|reminder|remainder|new task|scheduled task|untitled task)",
            value.strip(),
            flags=re.IGNORECASE,
        )
    )


class TaskIntentService:
    """Detect and persist tasks from chat messages."""

    def _looks_like_task_request(self, message: str) -> bool:
        return bool(CORE_TRIGGER_PATTERN.search(message)) or (
            bool(TIME_PATTERN.search(message)) and bool(ACTION_PATTERN.search(message))
        )

    def _prepare_task_from_parts(
        self,
        user_id: str,
        *,
        item_text: str,
        due_date: str | None,
        source_message: str,
    ) -> dict[str, Any]:
        task_type = _normalize_type(item_text, None)
        priority = "high" if re.search(r"\b(important|critical|urgent)\b", source_message, re.IGNORECASE) else "medium"
        notify_by_call = _wants_call_reminder(source_message)
        if notify_by_call:
            priority = "high"

        metadata = {"notify_by_call": True} if notify_by_call else {}
        title = item_text.strip()[:80] or "Task"
        description = item_text.strip() or title

        if task_type == "gmail":
            action, gmail_payload, _ = n8n_service.plan_gmail_action(item_text)
            if action == "send" and gmail_payload.get("to") and gmail_payload.get("body"):
                metadata.update(
                    {
                        "gmail_action": "send",
                        "gmail_approved_at": datetime.now(timezone.utc).isoformat(),
                        "gmail_to": gmail_payload["to"],
                        "gmail_subject": gmail_payload.get("subject") or "Message from AgentCoolie",
                        "gmail_body": gmail_payload["body"],
                    }
                )
                title = f"Send email to {gmail_payload['to']}"
                description = gmail_payload["body"]

        return {
            "user_id": user_id,
            "title": title,
            "description": description,
            "type": task_type,
            "priority": priority,
            "due_date": due_date,
            "metadata": metadata,
            "_notify_by_call": notify_by_call,
        }

    async def maybe_create_tasks_from_message(self, user_id: str, message: str) -> list[dict[str, Any]]:
        """Create multiple tasks for explicit multi-task requests."""
        message = message.strip()
        if not message or not self._looks_like_task_request(message):
            return []

        items = _extract_multi_task_items(message)
        if not items:
            return []

        due_date = _fallback_due_date(message)
        if not due_date:
            return []

        prepared_tasks: list[dict[str, Any]] = []
        for item in items:
            prepared_tasks.append(
                self._prepare_task_from_parts(
                    user_id,
                    item_text=item,
                    due_date=due_date,
                    source_message=message,
                )
            )

        task_count = len(prepared_tasks)
        call_count = sum(1 for task in prepared_tasks if task.get("_notify_by_call"))
        gmail_count = sum(1 for task in prepared_tasks if task.get("type") == "gmail")

        await plan_service.ensure_active_task_slot(user_id, amount=task_count)
        if gmail_count:
            await plan_service.ensure_feature_available(user_id, "gmail_sends")
        if call_count:
            await plan_service.ensure_critical_task_slot(user_id, amount=call_count)
            await plan_service.check_and_consume(
                user_id,
                "call_reminders",
                amount=call_count,
                metadata={"source": "chat_multi_task_creation", "task_count": task_count},
            )
            for task in prepared_tasks:
                if task.get("_notify_by_call"):
                    task["metadata"]["call_quota_reserved"] = True
        await plan_service.check_and_consume(
            user_id,
            "task_creations",
            amount=task_count,
            metadata={"source": "chat_multi", "task_count": task_count, "call_count": call_count},
        )

        rows = [
            {key: value for key, value in task.items() if not key.startswith("_")}
            for task in prepared_tasks
        ]
        return await supabase_service.create_tasks(rows)

    async def maybe_create_task_from_message(self, user_id: str, message: str) -> Optional[dict[str, Any]]:
        message = message.strip()
        if not message or not self._looks_like_task_request(message):
            return None

        details: dict[str, Any] = {}
        if gemini_service:
            now = _local_now().isoformat()
            prompt = f"""Decide whether this user message asks AgentCoolie to create a task or reminder.
Return strict JSON only with this schema:
{{
  "should_create": true,
  "title": "short task title",
  "description": "original useful task details",
  "type": "general|youtube|website|gmail",
  "priority": "low|medium|high",
  "notify_by_call": false,
  "due_date": "ISO-8601 datetime with timezone, or null"
}}

Rules:
- Only set should_create=true when the user clearly asks to remind, schedule, add, or create a task.
- For YouTube/song/video opening requests scheduled for later, use type "youtube".
- For website opening requests scheduled for later, use type "website".
- For unscheduled immediate web or YouTube actions, use should_create=false.
- Set notify_by_call=true when the user asks to call/phone them for this task.
- Use priority "high" when the user says the task is important, critical, or urgent.
- Current local datetime: {now}

User message: {message}"""
            try:
                raw = await gemini_service.analyze_text(message, prompt=prompt)
                details = _extract_json(raw)
            except Exception as e:
                logger.warning(f"Task intent AI extraction failed: {e}")

        should_create = bool(details.get("should_create", True))
        fallback_due_date = _fallback_due_date(message)
        due_date = fallback_due_date or _normalize_due_date(details.get("due_date"))
        if not should_create:
            return None

        cleaned_task_text = _clean_task_text(message)
        title = str(details.get("title") or cleaned_task_text).strip()
        description = str(details.get("description") or cleaned_task_text).strip()
        if _is_generic_task_text(title) and cleaned_task_text:
            title = cleaned_task_text
        if _is_generic_task_text(description) and cleaned_task_text:
            description = cleaned_task_text
        email_in_message = re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", message)
        if email_in_message and email_in_message.group(0) not in description:
            description = cleaned_task_text
        if re.fullmatch(r"(task|task reminder|reminder)", title.strip(), flags=re.IGNORECASE) and email_in_message:
            title = f"Send email to {email_in_message.group(0)}"
        if description == message:
            description = cleaned_task_text
        task_type = _normalize_type(message, details.get("type"))
        priority = _normalize_priority(details.get("priority"))
        notify_by_call = _wants_call_reminder(message, details.get("notify_by_call"))
        if notify_by_call and priority == "medium":
            priority = "high"
        metadata = {"notify_by_call": True} if notify_by_call else {}
        if task_type == "gmail":
            action, gmail_payload, _ = n8n_service.plan_gmail_action(cleaned_task_text)
            if action == "send" and gmail_payload.get("to") and gmail_payload.get("body"):
                metadata.update(
                    {
                        "gmail_action": "send",
                        "gmail_approved_at": datetime.now(timezone.utc).isoformat(),
                        "gmail_to": gmail_payload["to"],
                        "gmail_subject": gmail_payload.get("subject") or "Message from AgentCoolie",
                        "gmail_body": gmail_payload["body"],
                    }
                )
                description = gmail_payload["body"]
                if _is_generic_task_text(title) or email_in_message:
                    title = f"Send email to {gmail_payload['to']}"

        await plan_service.ensure_active_task_slot(user_id)
        if task_type == "gmail":
            await plan_service.ensure_feature_available(user_id, "gmail_sends")
        if notify_by_call:
            await plan_service.ensure_critical_task_slot(user_id)
            await plan_service.check_and_consume(
                user_id,
                "call_reminders",
                metadata={"source": "chat_task_creation", "task_type": task_type},
            )
            metadata["call_quota_reserved"] = True
        await plan_service.check_and_consume(
            user_id,
            "task_creations",
            metadata={"source": "chat", "task_type": task_type, "notify_by_call": notify_by_call},
        )

        return await supabase_service.create_task(
            user_id=user_id,
            title=title[:80] or "Task",
            description=description,
            task_type=task_type,
            priority=priority,
            due_date=due_date,
            metadata=metadata,
        )


task_intent_service = TaskIntentService()
