"""
Reminder compatibility routes.

The current frontend Tasks page still speaks the older reminders/SSE API.
These routes map that surface onto the existing tasks table.
"""

import asyncio
import json
import logging
import re
import time
import uuid
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.services import call_reminder_service, firebase_service, plan_service, supabase_service
from app.services.supabase_service import is_connectivity_error
from app.services.task_execution_service import execute_gmail_task

router = APIRouter(prefix="/api", tags=["reminders"])
logger = logging.getLogger(__name__)

_sse_connect_ids: dict[str, dict] = {}
SSE_CONNECT_TTL_SECONDS = 300
SSE_MAX_IDS_PER_USER = 5
SUPABASE_UNREACHABLE_DETAIL = "Could not reach Supabase. Check internet/DNS and SUPABASE_URL in .env."


def _storage_http_exception(operation: str, error: Exception) -> HTTPException:
    logger.error(f"Failed to {operation}: {error}")
    if is_connectivity_error(error):
        return HTTPException(status_code=503, detail=SUPABASE_UNREACHABLE_DETAIL)
    return HTTPException(status_code=500, detail=f"Failed to {operation}")


def get_current_user(authorization: str = Header(None)) -> str:
    """Extract user ID from Firebase token in Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        parts = authorization.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise ValueError("Invalid authorization header format")
        decoded = firebase_service.verify_id_token(parts[1])
        user_id = decoded.get("uid")
        if not user_id:
            raise ValueError("Invalid token: missing uid")
        return user_id
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def _task_to_reminder(row: dict) -> dict:
    task_type = row.get("type") or "general"
    status = row.get("status")
    if not status:
        status = "sent" if row.get("completed") else "pending"
    if status == "completed":
        status = "sent"

    metadata = row.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    return {
        "id": row.get("id"),
        "user_id": row.get("user_id"),
        "type": "general" if task_type == "reminder" else task_type,
        "message": row.get("description") or row.get("title") or "",
        "datetime": row.get("due_date"),
        "priority": row.get("priority") or "medium",
        "status": status,
        "execution_message": row.get("execution_message"),
        "last_attempt_at": row.get("last_attempt_at"),
        "notify_by_call": bool(metadata.get("notify_by_call") or metadata.get("call_reminder")),
        "gmail_to": metadata.get("gmail_to"),
        "call_status": metadata.get("call_status"),
        "call_error_code": metadata.get("call_error_code"),
        "created_at": row.get("created_at"),
    }


def _website_url_from_message(message: str) -> str | None:
    import re

    url_match = re.search(r"https?://[^\s\)\"']+", message)
    if url_match:
        return url_match.group(0)

    domain_match = re.search(r"(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}", message)
    if domain_match:
        domain = domain_match.group(0)
        if not domain.startswith("www."):
            domain = f"www.{domain}"
        return f"https://{domain}"

    stop_words = {
        "open", "go", "to", "visit", "show", "me", "navigate", "launch",
        "website", "site", "link", "the", "a", "an", "can", "you", "u",
        "please", "in", "browser", "tomorrow", "today", "tonight", "at",
    }
    tokens = re.findall(r"[a-zA-Z0-9-]+", message.lower())
    candidates = [token for token in tokens if token not in stop_words and not token.isdigit()]
    if not candidates:
        return None
    return f"https://www.{candidates[-1]}.com"


def _cleanup_sse_connect_ids() -> None:
    now = time.time()
    expired = [
        connect_id for connect_id, data in _sse_connect_ids.items()
        if float(data.get("expires_at") or 0) <= now
    ]
    for connect_id in expired:
        _sse_connect_ids.pop(connect_id, None)


def _valid_email(value: str | None) -> str | None:
    email = str(value or "").strip()
    if not email:
        return None
    return email if re.fullmatch(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", email) else None


@router.get("/reminders")
async def get_reminders(user_id: str = Depends(get_current_user)) -> list[dict]:
    """Return reminders using the frontend's legacy shape."""
    try:
        tasks = await supabase_service.get_tasks(user_id)
    except Exception as e:
        logger.error(f"Failed to fetch reminders: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail=SUPABASE_UNREACHABLE_DETAIL)
        raise HTTPException(status_code=500, detail="Failed to fetch reminders")
    return [_task_to_reminder(task) for task in tasks]


@router.post("/reminders")
async def create_reminder(
    request: dict,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Create a reminder using the existing tasks table."""
    message = str(request.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    task_type = request.get("type") or "general"
    if task_type == "reminder":
        task_type = "general"
    if task_type == "whatsapp":
        task_type = "general"
    if task_type not in {"general", "gmail", "youtube", "website"}:
        raise HTTPException(status_code=400, detail="Unsupported reminder type")

    due_date: Optional[str] = request.get("datetime")
    if due_date:
        try:
            datetime.fromisoformat(str(due_date).replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid datetime")

    try:
        notify_by_call = bool(request.get("notify_by_call"))
        metadata: dict = {}
        gmail_to = _valid_email(request.get("user_email") or request.get("gmail_to") or request.get("to"))
        if task_type == "gmail":
            raw_email = str(request.get("user_email") or request.get("gmail_to") or request.get("to") or "").strip()
            if raw_email and not gmail_to:
                raise HTTPException(status_code=400, detail="Invalid Gmail recipient email")
            if not gmail_to:
                raise HTTPException(
                    status_code=400,
                    detail="Gmail tasks need a recipient. Create the email through chat if you want AgentCoolie to draft it first.",
                )
            gmail_body = str(request.get("body") or message).strip()
            gmail_subject = str(request.get("subject") or "Message from AgentCoolie").strip()
            if not gmail_body or len(gmail_body) > 10000 or len(gmail_subject) > 180:
                raise HTTPException(status_code=400, detail="Gmail subject or body is invalid or too long")
            metadata.update({
                "gmail_action": "send",
                "gmail_approved_at": datetime.now().astimezone().isoformat(),
                "gmail_to": gmail_to,
                "gmail_subject": gmail_subject,
                "gmail_body": gmail_body,
            })
        if notify_by_call:
            metadata["notify_by_call"] = True
            if str(request.get("call_phone") or "").strip():
                raise HTTPException(
                    status_code=400,
                    detail="Save the call phone number in Settings. Task-level call phone overrides are not allowed.",
                )

        await plan_service.ensure_active_task_slot(user_id)
        if task_type == "gmail":
            await plan_service.ensure_feature_available(user_id, "gmail_sends")
        if notify_by_call:
            await plan_service.ensure_critical_task_slot(user_id)
            await plan_service.check_and_consume(
                user_id,
                "call_reminders",
                metadata={"source": "reminders_api_creation", "task_type": task_type},
            )
            metadata["call_quota_reserved"] = True
        await plan_service.check_and_consume(
            user_id,
            "task_creations",
            metadata={"source": "reminders_api", "task_type": task_type, "notify_by_call": notify_by_call},
        )

        task = await supabase_service.create_task(
            user_id=user_id,
            title=message[:40] or "Reminder",
            description=message,
            task_type=task_type,
            priority="high" if notify_by_call else "low",
            due_date=due_date,
            metadata=metadata,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create reminder task: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail=SUPABASE_UNREACHABLE_DETAIL)
        raise HTTPException(status_code=500, detail="Failed to create reminder")

    return _task_to_reminder(task)


@router.patch("/reminders/{reminder_id}")
async def update_reminder(
    reminder_id: str,
    request: dict,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Update reminder status or content."""
    updates: dict = {}
    if "status" in request:
        status_value = str(request.get("status") or "").strip()
        if status_value not in {"pending", "sent", "missed_offline", "failed", "calling"}:
            raise HTTPException(status_code=400, detail="Unsupported reminder status")
        updates["status"] = status_value
        updates["completed"] = status_value == "sent"
    if "execution_message" in request:
        updates["execution_message"] = str(request.get("execution_message") or "")[:500]
    if "last_attempt_at" in request:
        updates["last_attempt_at"] = request.get("last_attempt_at")
    if "notify_by_call" in request or "call_phone" in request:
        try:
            task = await supabase_service.get_task(reminder_id, user_id=user_id)
        except Exception as e:
            raise _storage_http_exception("load reminder", e)
        if not task:
            raise HTTPException(status_code=404, detail="Reminder not found")
        metadata = task.get("metadata") if isinstance(task.get("metadata"), dict) else {}
        if "notify_by_call" in request:
            previous_notify_by_call = bool(metadata.get("notify_by_call") or metadata.get("call_reminder"))
            next_notify_by_call = bool(request.get("notify_by_call"))
            if next_notify_by_call and not previous_notify_by_call:
                await plan_service.ensure_critical_task_slot(user_id)
                await plan_service.check_and_consume(
                    user_id,
                    "call_reminders",
                    metadata={"source": "reminders_api_update", "task_id": reminder_id},
                )
                metadata["call_quota_reserved"] = True
            metadata["notify_by_call"] = next_notify_by_call
            if not next_notify_by_call:
                metadata.pop("call_quota_reserved", None)
        if "call_phone" in request:
            if str(request.get("call_phone") or "").strip():
                raise HTTPException(
                    status_code=400,
                    detail="Save the call phone number in Settings. Task-level call phone overrides are not allowed.",
                )
            metadata.pop("call_phone", None)
        updates["metadata"] = metadata
    if "message" in request:
        message = str(request.get("message") or "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        updates["title"] = message[:40]
        updates["description"] = message
    if "datetime" in request:
        updates["due_date"] = request.get("datetime")

    if not updates:
        raise HTTPException(status_code=400, detail="No supported updates supplied")

    try:
        task = await supabase_service.update_task(reminder_id, user_id=user_id, **updates)
    except Exception as e:
        raise _storage_http_exception("update reminder", e)
    if not task:
        raise HTTPException(status_code=404, detail="Reminder not found")

    if updates.get("status") == "missed_offline":
        try:
            await supabase_service.create_notification(
                user_id=user_id,
                title="Task missed while offline",
                message=updates.get("execution_message") or "A scheduled task was due while this device was offline or the app was closed.",
                notification_type="task",
            )
        except Exception as e:
            logger.warning(f"Failed to create missed-offline notification: {e}")

    return _task_to_reminder(task)


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(
    reminder_id: str,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Delete a reminder."""
    try:
        deleted = await supabase_service.delete_task(reminder_id, user_id=user_id)
    except Exception as e:
        raise _storage_http_exception("delete reminder", e)
    if not deleted:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "success", "message": "Reminder deleted"}


@router.post("/reminders/{reminder_id}/execute")
async def execute_reminder(
    reminder_id: str,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Execute a due task through the backend/tool layer and persist status."""
    try:
        task = await supabase_service.get_task(reminder_id, user_id=user_id)
    except Exception as e:
        raise _storage_http_exception("load reminder", e)
    if not task:
        raise HTTPException(status_code=404, detail="Reminder not found")

    task_type = task.get("type") or "general"
    existing_metadata = task.get("metadata") if isinstance(task.get("metadata"), dict) else {}
    current_status = str(task.get("status") or ("sent" if task.get("completed") else "pending"))
    if current_status in {"calling", "failed"} and task_type in {"youtube", "website"}:
        open_url = existing_metadata.get("browser_open_url")
        if isinstance(open_url, str) and open_url.strip():
            return {
                "status": "browser_action_required",
                "task": _task_to_reminder(task),
                "action": {"open_url": open_url.strip()},
            }
    if current_status in {"sent", "missed_offline", "failed"}:
        return {
            "status": "already_handled",
            "task": _task_to_reminder(task),
            "action": {},
        }

    now_iso = datetime.now().astimezone().isoformat()
    claim_metadata = {
        **existing_metadata,
        "execution_scope": "manual_execute",
        "execution_attempt": int(existing_metadata.get("execution_attempt") or 0) + 1,
        "execution_claimed_at": now_iso,
        "execution_lease_seconds": max(60, int(settings.TASK_EXECUTION_LEASE_SECONDS or 300)),
    }

    try:
        claim = await supabase_service.claim_pending_task(
            reminder_id,
            user_id=user_id,
            status="calling",
            completed=False,
            execution_message="Task is being executed by AgentCoolie.",
            last_attempt_at=now_iso,
            metadata=claim_metadata,
        )
    except Exception as e:
        raise _storage_http_exception("claim reminder execution", e)
    if not claim:
        try:
            latest = await supabase_service.get_task(reminder_id, user_id=user_id) or task
        except Exception as e:
            raise _storage_http_exception("load reminder", e)
        return {
            "status": "already_handled",
            "task": _task_to_reminder(latest),
            "action": {},
        }
    task = claim

    message = task.get("description") or task.get("title") or ""
    execution_message = "Task completed by AgentCoolie."
    action: dict = {}
    status_value = "sent"

    try:
        if task_type == "youtube":
            await plan_service.check_and_consume(
                user_id,
                "youtube_opens",
                metadata={"source": "reminders_execute", "task_id": reminder_id},
            )
        elif task_type == "website":
            await plan_service.check_and_consume(
                user_id,
                "website_opens",
                metadata={"source": "reminders_execute", "task_id": reminder_id},
            )
        await plan_service.check_and_consume(
            user_id,
            "task_executions",
            metadata={"source": "reminders_execute", "task_type": task_type, "task_id": reminder_id},
        )
        call_result = None
        existing_metadata = task.get("metadata") if isinstance(task.get("metadata"), dict) else claim_metadata
        if call_reminder_service.task_wants_call(task) and existing_metadata.get("call_status") != "placed":
            await supabase_service.update_task(
                reminder_id,
                user_id=user_id,
                status="calling",
                completed=False,
                execution_message="Call reminder is being placed.",
                last_attempt_at=datetime.now().astimezone().isoformat(),
                metadata=existing_metadata,
            )
            call_result = await call_reminder_service.place_task_call(task)
            metadata = existing_metadata
            metadata = {
                **metadata,
                "call_status": "placed",
                "call_sid": call_result.get("sid"),
                "call_attempted_at": call_result.get("called_at"),
                "call_message": call_result.get("message"),
            }
            execution_message = f"Call reminder placed: {call_result.get('message')}"
            task = {**task, "metadata": metadata}
            action["call"] = call_result

        if task_type == "gmail":
            await execute_gmail_task(user_id, task)
            execution_message = (
                f"{execution_message} Gmail task completed."
                if call_result
                else "Gmail task completed."
            )

        elif task_type == "youtube":
            action["open_url"] = f"https://www.youtube.com/results?{urlencode({'search_query': message})}"
            execution_message = (
                f"{execution_message} YouTube task is ready to open in the browser."
                if call_result
                else "YouTube task is ready to open in the browser."
            )
            metadata = task.get("metadata") if isinstance(task.get("metadata"), dict) else {}
            updated = await supabase_service.update_task(
                reminder_id,
                user_id=user_id,
                status="calling",
                completed=False,
                execution_message=execution_message,
                last_attempt_at=datetime.now().astimezone().isoformat(),
                metadata={
                    **metadata,
                    "browser_open_url": action["open_url"],
                    "execution_scope": "browser_action_required",
                },
            )
            return {
                "status": "browser_action_required",
                "task": _task_to_reminder(updated),
                "action": action,
            }

        elif task_type == "website":
            url = _website_url_from_message(message)
            if not url:
                raise RuntimeError("Could not determine which website to open.")
            action["open_url"] = url
            execution_message = (
                f"{execution_message} Website task is ready to open in the browser."
                if call_result
                else "Website task is ready to open in the browser."
            )
            metadata = task.get("metadata") if isinstance(task.get("metadata"), dict) else {}
            updated = await supabase_service.update_task(
                reminder_id,
                user_id=user_id,
                status="calling",
                completed=False,
                execution_message=execution_message,
                last_attempt_at=datetime.now().astimezone().isoformat(),
                metadata={
                    **metadata,
                    "browser_open_url": action["open_url"],
                    "execution_scope": "browser_action_required",
                },
            )
            return {
                "status": "browser_action_required",
                "task": _task_to_reminder(updated),
                "action": action,
            }

        update_payload = {
            "status": status_value,
            "completed": True,
            "execution_message": execution_message,
            "last_attempt_at": datetime.now().astimezone().isoformat(),
        }
        if isinstance(task.get("metadata"), dict):
            update_payload["metadata"] = {
                **task["metadata"],
                "execution_scope": "completed",
                "execution_completed_at": datetime.now().astimezone().isoformat(),
            }
        updated = await supabase_service.update_task(reminder_id, user_id=user_id, **update_payload)
        return {"status": "success", "task": _task_to_reminder(updated), "action": action}

    except Exception as e:
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail=SUPABASE_UNREACHABLE_DETAIL)
        error_message = str(e)[:500]
        metadata = task.get("metadata") if isinstance(task.get("metadata"), dict) else claim_metadata
        metadata = {**metadata, "execution_scope": "failed"}
        if call_reminder_service.task_wants_call(task):
            metadata = {
                **metadata,
                "call_status": "failed",
                "call_error": error_message,
                "call_error_code": getattr(e, "code", None) or "call_failed",
                "call_provider_status": getattr(e, "provider_status", None),
                "call_more_info": getattr(e, "more_info", None),
            }
        try:
            updated = await supabase_service.update_task(
                reminder_id,
                user_id=user_id,
                status="failed",
                completed=False,
                execution_message=error_message,
                last_attempt_at=datetime.now().astimezone().isoformat(),
                metadata=metadata,
            )
        except Exception as storage_error:
            raise _storage_http_exception("record reminder failure", storage_error)
        return {"status": "failed", "task": _task_to_reminder(updated), "error": error_message}


@router.post("/sse/connect")
async def create_sse_connection(user_id: str = Depends(get_current_user)) -> dict:
    """Create a short-lived SSE connection id."""
    _cleanup_sse_connect_ids()
    user_ids = [
        connect_id for connect_id, data in _sse_connect_ids.items()
        if data.get("user_id") == user_id
    ]
    excess = max(0, len(user_ids) - SSE_MAX_IDS_PER_USER + 1)
    for connect_id in user_ids[:excess]:
        _sse_connect_ids.pop(connect_id, None)
    connect_id = str(uuid.uuid4())
    _sse_connect_ids[connect_id] = {
        "user_id": user_id,
        "expires_at": time.time() + SSE_CONNECT_TTL_SECONDS,
    }
    return {"connectId": connect_id}


@router.get("/sse/stream/{connect_id}")
async def stream_reminders(connect_id: str):
    """Keep the legacy SSE endpoint alive with heartbeat events."""
    _cleanup_sse_connect_ids()
    connection = _sse_connect_ids.get(connect_id)
    if not connection:
        raise HTTPException(status_code=404, detail="SSE connection not found")

    async def event_stream():
        try:
            yield f"event: ready\ndata: {json.dumps({'status': 'connected'})}\n\n"
            while True:
                await asyncio.sleep(30)
                yield f"event: ping\ndata: {json.dumps({'status': 'ok'})}\n\n"
        finally:
            _sse_connect_ids.pop(connect_id, None)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
