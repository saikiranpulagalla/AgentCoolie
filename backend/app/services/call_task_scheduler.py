"""Backend loop for due tasks that must notify users by phone call."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.services.call_reminder_service import call_reminder_service
from app.services.plan_service import plan_service
from app.services.supabase_service import is_connectivity_error, supabase_service
from app.services.task_execution_service import execute_gmail_task

logger = logging.getLogger(__name__)


class CallTaskScheduler:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._stopping = asyncio.Event()

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stopping.clear()
        self._task = asyncio.create_task(self._run(), name="call-task-scheduler")
        logger.info("Call task scheduler started")

    async def stop(self) -> None:
        self._stopping.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        interval = max(10, int(settings.CALL_REMINDER_POLL_INTERVAL_SECONDS or 30))
        while not self._stopping.is_set():
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning(f"Call task scheduler tick failed: {e}")

            try:
                await asyncio.wait_for(self._stopping.wait(), timeout=interval)
            except asyncio.TimeoutError:
                continue

    async def run_once(self) -> None:
        try:
            due_tasks = await supabase_service.get_due_pending_tasks(limit=25)
        except Exception as e:
            if is_connectivity_error(e):
                logger.warning("Skipping call scheduler tick because Supabase is unreachable")
                return
            raise

        for task in due_tasks:
            task_type = str(task.get("type") or "general")
            metadata = task.get("metadata") if isinstance(task.get("metadata"), dict) else {}
            wants_call = call_reminder_service.task_wants_call(task)
            # The backend should only run actions that can complete while the
            # user's browser is closed. Plain reminders and browser-opening
            # tasks are intentionally left for the frontend runner so it can
            # mark them missed_offline when the PC/app was unavailable.
            if task_type != "gmail" and not wants_call:
                continue
            if task_type in {"youtube", "website"} and metadata.get("call_status") == "placed":
                continue
            await self._process_task(task)

    async def _process_task(self, task: dict[str, Any]) -> None:
        task_id = str(task.get("id") or "")
        user_id = str(task.get("user_id") or "")
        if not task_id or not user_id:
            return

        metadata = task.get("metadata") if isinstance(task.get("metadata"), dict) else {}
        now_iso = datetime.now(timezone.utc).isoformat()
        task_type = str(task.get("type") or "general")
        wants_call = call_reminder_service.task_wants_call(task)
        claim_message = "Call reminder is being placed." if wants_call else "Task is being executed by AgentCoolie."

        try:
            claimed = await supabase_service.claim_pending_task(
                task_id,
                user_id=user_id,
                status="calling",
                completed=False,
                execution_message=claim_message,
                last_attempt_at=now_iso,
            )
            if not claimed:
                return

            await plan_service.check_and_consume(
                user_id,
                "task_executions",
                metadata={"source": "backend_scheduler", "task_type": task_type, "task_id": task_id},
            )
            call_result = None
            updated_metadata = dict(metadata)
            execution_parts: list[str] = []
            if call_reminder_service.task_wants_call(task) and metadata.get("call_status") != "placed":
                call_result = await call_reminder_service.place_task_call(task)
                updated_metadata = {
                    **updated_metadata,
                    "call_status": "placed",
                    "call_sid": call_result.get("sid"),
                    "call_attempted_at": call_result.get("called_at"),
                    "call_message": call_result.get("message"),
                }
                execution_parts.append(f"Call reminder placed: {call_result.get('message')}")

            if task_type == "gmail":
                await execute_gmail_task(user_id, task)
                execution_parts.append("Gmail task completed.")
            elif task_type in {"youtube", "website"}:
                # A call can be delivered server-side, but opening a browser tab
                # cannot. Put the task back to pending with call metadata so the
                # frontend can still open it when the user returns.
                await supabase_service.update_task(
                    task_id,
                    user_id=user_id,
                    status="pending",
                    completed=False,
                    execution_message=" ".join(execution_parts) or "Waiting for the browser to open this task.",
                    last_attempt_at=datetime.now(timezone.utc).isoformat(),
                    metadata=updated_metadata,
                )
                logger.info(f"Placed call side-effect for browser task {task_id}")
                return
            else:
                execution_parts.append("Reminder completed by AgentCoolie.")

            execution_message = " ".join(execution_parts)
            await supabase_service.update_task(
                task_id,
                user_id=user_id,
                status="sent",
                completed=True,
                execution_message=execution_message[:500],
                last_attempt_at=datetime.now(timezone.utc).isoformat(),
                metadata=updated_metadata,
            )
            logger.info(f"Placed call reminder for task {task_id}")

        except Exception as e:
            error_message = str(e)[:500]
            logger.error(f"Failed to place call reminder for task {task_id}: {error_message}")
            await supabase_service.update_task(
                task_id,
                user_id=user_id,
                status="failed",
                completed=False,
                execution_message=error_message,
                last_attempt_at=datetime.now(timezone.utc).isoformat(),
                metadata={**metadata, "call_status": "failed", "call_error": error_message},
            )


call_task_scheduler = CallTaskScheduler()
