"""Plan definitions, entitlement checks, and usage accounting."""

from __future__ import annotations

import asyncio
import logging
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException

from app.core.config import settings
from app.services.supabase_service import is_connectivity_error, supabase_service

logger = logging.getLogger(__name__)


PLAN_COMPANION = "companion"
PLAN_AUTOPILOT = "autopilot"


PLAN_DEFINITIONS: dict[str, dict[str, Any]] = {
    PLAN_COMPANION: {
        "id": PLAN_COMPANION,
        "name": "AgentCoolie Companion",
        "description": "Free personal assistant mode for chat, light memory, simple tasks, and small uploads.",
        "price": {
            "inr_monthly": 0,
            "usd_monthly": 0,
            "inr_yearly": 0,
            "usd_yearly": 0,
        },
        "quotas": {
            "chat_messages": {"day": 15, "month": 150},
            "web_searches": {"day": 3, "month": 25},
            "task_creations": {"day": 3, "month": 25},
            "task_executions": {"day": 1, "month": 10},
            "gmail_drafts": {"month": 0},
            "gmail_sends": {"month": 0},
            "gmail_reads": {"month": 0},
            "whatsapp_messages": {"month": 0},
            "call_reminders": {"month": 1},
            "image_uploads": {"day": 1, "month": 10},
            "pdf_uploads": {"day": 1, "month": 5},
            "audio_uploads": {"day": 1, "month": 10},
            "youtube_opens": {"day": 5, "month": 50},
            "website_opens": {"day": 5, "month": 50},
            "long_term_memory_writes": {"month": 3},
        },
        "caps": {
            "active_chats": 5,
            "chat_history_days": 7,
            "short_memory_turns": 4,
            "long_term_memories": 15,
            "active_tasks": 5,
            "critical_tasks": 1,
            "max_call_seconds": 10,
            "max_image_mb": 3,
            "max_pdf_mb": 3,
            "max_pdf_pages": 2,
            "max_audio_mb": 3,
            "max_audio_seconds": 30,
            "tool_retries": 0,
        },
    },
    PLAN_AUTOPILOT: {
        "id": PLAN_AUTOPILOT,
        "name": "AgentCoolie Autopilot",
        "description": "Paid automation mode for deeper memory, Gmail/WhatsApp tools, scheduled actions, and call reminders.",
        "price": {
            "inr_monthly": 499,
            "usd_monthly": 6,
            "inr_yearly": 4999,
            "usd_yearly": 60,
        },
        "quotas": {
            "chat_messages": {"day": 60, "month": 1000},
            "web_searches": {"day": 20, "month": 250},
            "task_creations": {"day": 30, "month": 300},
            "task_executions": {"day": 15, "month": 200},
            "gmail_drafts": {"month": 100},
            "gmail_sends": {"month": 50},
            "gmail_reads": {"month": 100},
            "whatsapp_messages": {"month": 250},
            "call_reminders": {"month": 10},
            "image_uploads": {"day": 15, "month": 200},
            "pdf_uploads": {"day": 5, "month": 75},
            "audio_uploads": {"day": 10, "month": 100},
            "youtube_opens": {"day": 50, "month": 500},
            "website_opens": {"day": 50, "month": 500},
            "long_term_memory_writes": {"month": 50},
        },
        "caps": {
            "active_chats": 30,
            "chat_history_days": 90,
            "short_memory_turns": 15,
            "long_term_memories": 200,
            "active_tasks": 75,
            "critical_tasks": 10,
            "max_call_seconds": 25,
            "max_image_mb": 10,
            "max_pdf_mb": 15,
            "max_pdf_pages": 25,
            "max_audio_mb": 25,
            "max_audio_seconds": 300,
            "tool_retries": 2,
        },
    },
}


FEATURE_LABELS = {
    "chat_messages": "AI chat messages",
    "web_searches": "web searches",
    "task_creations": "task creations",
    "task_executions": "automated task executions",
    "gmail_drafts": "Gmail drafts",
    "gmail_sends": "Gmail send/reply actions",
    "gmail_reads": "Gmail read/search actions",
    "whatsapp_messages": "WhatsApp messages",
    "call_reminders": "call reminders",
    "image_uploads": "image uploads",
    "pdf_uploads": "PDF uploads",
    "audio_uploads": "audio uploads",
    "youtube_opens": "YouTube open actions",
    "website_opens": "website open actions",
    "long_term_memory_writes": "long-term memory writes",
}


class PlanService:
    """Central source for free/pro entitlements and usage tracking."""

    def __init__(self) -> None:
        self._usage_locks: dict[str, asyncio.Lock] = {}

    def public_plans(self) -> list[dict[str, Any]]:
        return [deepcopy(PLAN_DEFINITIONS[PLAN_COMPANION]), deepcopy(PLAN_DEFINITIONS[PLAN_AUTOPILOT])]

    async def get_user_plan_id(self, user_id: str) -> str:
        try:
            row = await supabase_service.get_user_plan(user_id)
        except Exception as e:
            if is_connectivity_error(e):
                raise
            logger.warning(f"Plan lookup failed for {user_id}; defaulting to Companion: {e}")
            return PLAN_COMPANION

        plan_id = str((row or {}).get("plan") or PLAN_COMPANION).strip().lower()
        if plan_id != PLAN_AUTOPILOT:
            return PLAN_COMPANION

        billing_status = str((row or {}).get("billing_status") or "").strip().lower()
        if billing_status not in {"active", "trialing"}:
            return PLAN_COMPANION

        period_end = (row or {}).get("current_period_end")
        if period_end:
            try:
                expires_at = datetime.fromisoformat(str(period_end).replace("Z", "+00:00"))
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                if expires_at.astimezone(timezone.utc) <= datetime.now(timezone.utc):
                    return PLAN_COMPANION
            except ValueError:
                logger.warning("Invalid plan expiry for %s; treating entitlement as Companion", user_id)
                return PLAN_COMPANION

        return PLAN_AUTOPILOT

    async def get_plan(self, user_id: str) -> dict[str, Any]:
        return deepcopy(PLAN_DEFINITIONS[await self.get_user_plan_id(user_id)])

    def _period_start(self, period: str) -> datetime:
        now = datetime.now(timezone.utc)
        if period == "day":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        if period == "month":
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        raise ValueError(f"Unsupported usage period: {period}")

    def _limit_error(self, plan: dict[str, Any], feature: str, period: str, limit: int) -> HTTPException:
        label = FEATURE_LABELS.get(feature, feature.replace("_", " "))
        plan_name = plan.get("name") or "your plan"
        reset = "tomorrow" if period == "day" else "next month"
        return HTTPException(
            status_code=402,
            detail=(
                f"{plan_name} includes {limit} {label} per {period}. "
                f"You have reached that limit. Try again {reset} or upgrade to AgentCoolie Autopilot."
            ),
        )

    def _dependency_error(self, detail: str) -> HTTPException:
        return HTTPException(status_code=503, detail=detail)

    def _lock_for(self, user_id: str, feature: str) -> asyncio.Lock:
        key = f"{user_id}:{feature}"
        lock = self._usage_locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._usage_locks[key] = lock
        return lock

    async def check_and_consume(
        self,
        user_id: str,
        feature: str,
        amount: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Raise HTTP 402 when a quota is exhausted, then record usage."""
        amount = max(1, int(amount or 1))
        plan = await self.get_plan(user_id)
        quotas = plan.get("quotas", {})
        feature_quota = quotas.get(feature)
        usage_metadata = {"plan": plan["id"], **(metadata or {})}
        if isinstance(feature_quota, dict):
            day_limit = feature_quota.get("day")
            month_limit = feature_quota.get("month")
            day_start = self._period_start("day").isoformat() if day_limit is not None else None
            month_start = self._period_start("month").isoformat() if month_limit is not None else None
            try:
                result = await supabase_service.consume_usage_quota(
                    user_id=user_id,
                    feature=feature,
                    amount=amount,
                    metadata=usage_metadata,
                    day_start=day_start,
                    day_limit=int(day_limit) if day_limit is not None else None,
                    month_start=month_start,
                    month_limit=int(month_limit) if month_limit is not None else None,
                )
                if not result:
                    raise RuntimeError("Usage quota RPC returned no result")
                if result.get("allowed") is False:
                    raise self._limit_error(
                        plan,
                        feature,
                        str(result.get("period") or "month"),
                        int(result.get("limit") or 0),
                    )
                return plan
            except HTTPException:
                raise
            except Exception as e:
                if is_connectivity_error(e):
                    raise
                if not settings.is_local_runtime():
                    logger.error("Atomic usage accounting failed for %s/%s: %s", user_id, feature, e)
                    raise self._dependency_error("Usage accounting is unavailable. Please try again later.") from e
                logger.warning(f"Atomic usage consume failed for {user_id}/{feature}; using local lock fallback: {e}")

            async with self._lock_for(user_id, feature):
                for period in ("day", "month"):
                    limit = feature_quota.get(period)
                    if limit is None:
                        continue
                    try:
                        used = await supabase_service.count_usage_events(
                            user_id=user_id,
                            feature=feature,
                            since=self._period_start(period).isoformat(),
                        )
                    except Exception as e:
                        if is_connectivity_error(e):
                            raise
                        raise self._dependency_error("Usage accounting is unavailable. Please try again later.") from e
                    if used + amount > int(limit):
                        raise self._limit_error(plan, feature, period, int(limit))

                try:
                    await supabase_service.create_usage_event(
                        user_id=user_id,
                        feature=feature,
                        amount=amount,
                        metadata=usage_metadata,
                    )
                except Exception as e:
                    if is_connectivity_error(e):
                        raise
                    raise self._dependency_error("Usage accounting is unavailable. Please try again later.") from e
                return plan

        try:
            await supabase_service.create_usage_event(
                user_id=user_id,
                feature=feature,
                amount=amount,
                metadata=usage_metadata,
            )
        except Exception as e:
            if is_connectivity_error(e):
                raise
            if settings.ENV.lower() != "development":
                raise self._dependency_error("Usage accounting is unavailable. Please try again later.") from e
            logger.warning(f"Usage write failed for {user_id}/{feature}; allowing in development: {e}")

        return plan

    async def ensure_feature_available(self, user_id: str, feature: str) -> dict[str, Any]:
        """Raise HTTP 402 when a plan has explicitly disabled a feature."""
        plan = await self.get_plan(user_id)
        feature_quota = plan.get("quotas", {}).get(feature)
        if isinstance(feature_quota, dict) and any(int(limit or 0) <= 0 for limit in feature_quota.values()):
            label = FEATURE_LABELS.get(feature, feature.replace("_", " "))
            raise HTTPException(
                status_code=402,
                detail=f"{label.capitalize()} are available on AgentCoolie Autopilot.",
            )
        return plan

    async def ensure_active_task_slot(self, user_id: str, amount: int = 1) -> dict[str, Any]:
        plan = await self.get_plan(user_id)
        limit = int(plan.get("caps", {}).get("active_tasks") or 0)
        try:
            active_count = await supabase_service.count_active_tasks(user_id)
        except Exception as e:
            if is_connectivity_error(e):
                raise
            raise self._dependency_error("Task quota accounting is unavailable. Please try again later.") from e
        if limit and active_count + amount > limit:
            raise HTTPException(
                status_code=402,
                detail=(
                    f"{plan['name']} allows {limit} active tasks. "
                    "Complete or delete an existing task, or upgrade to AgentCoolie Autopilot."
                ),
            )
        return plan

    async def ensure_critical_task_slot(self, user_id: str, amount: int = 1) -> dict[str, Any]:
        plan = await self.get_plan(user_id)
        limit = int(plan.get("caps", {}).get("critical_tasks") or 0)
        if limit <= 0:
            raise HTTPException(
                status_code=402,
                detail="Phone-call critical tasks are available on AgentCoolie Autopilot.",
            )
        try:
            active_count = await supabase_service.count_active_tasks(user_id, notify_by_call=True)
        except Exception as e:
            if is_connectivity_error(e):
                raise
            raise self._dependency_error("Critical task quota accounting is unavailable. Please try again later.") from e
        if active_count + amount > limit:
            raise HTTPException(
                status_code=402,
                detail=f"{plan['name']} allows {limit} active phone-call tasks.",
            )
        return plan

    async def ensure_long_term_memory_slot(self, user_id: str) -> bool:
        plan = await self.get_plan(user_id)
        limit = int(plan.get("caps", {}).get("long_term_memories") or 0)
        try:
            current_count = await supabase_service.count_long_term_memories(user_id)
        except Exception as e:
            if is_connectivity_error(e):
                raise
            logger.warning(f"Memory count failed for {user_id}; skipping memory write: {e}")
            return False
        return not limit or current_count < limit

    async def consume_upload(self, user_id: str, kind: str, byte_count: int) -> dict[str, Any]:
        feature = {
            "image": "image_uploads",
            "pdf": "pdf_uploads",
            "audio": "audio_uploads",
        }.get(kind)
        if not feature:
            raise ValueError(f"Unsupported upload kind: {kind}")

        plan = await self.get_plan(user_id)
        cap_key = f"max_{kind}_mb"
        max_mb = float(plan.get("caps", {}).get(cap_key) or 0)
        max_bytes = int(max_mb * 1024 * 1024)
        if max_bytes and byte_count > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"{plan['name']} allows {max_mb:g} MB {kind} uploads.",
            )
        await self.check_and_consume(user_id, feature, metadata={"bytes": byte_count})
        return plan

    async def account_summary(self, user_id: str) -> dict[str, Any]:
        plan = await self.get_plan(user_id)
        usage: dict[str, Any] = {}
        for feature, limits in plan.get("quotas", {}).items():
            item: dict[str, Any] = {"limits": limits}
            for period in ("day", "month"):
                if period not in limits:
                    continue
                try:
                    item[period] = await supabase_service.count_usage_events(
                        user_id=user_id,
                        feature=feature,
                        since=self._period_start(period).isoformat(),
                    )
                except Exception as e:
                    if is_connectivity_error(e):
                        raise
                    item[period] = None
            usage[feature] = item

        try:
            active_tasks = await supabase_service.count_active_tasks(user_id)
            long_term_memories = await supabase_service.count_long_term_memories(user_id)
        except Exception as e:
            if is_connectivity_error(e):
                raise
            active_tasks = None
            long_term_memories = None

        return {
            "plan": plan,
            "usage": usage,
            "counts": {
                "active_tasks": active_tasks,
                "long_term_memories": long_term_memories,
            },
            "plans": self.public_plans(),
        }

    async def activate_demo_autopilot(self, user_id: str) -> dict[str, Any]:
        """Activate Autopilot through the temporary no-real-payment demo checkout."""
        now = datetime.now(timezone.utc)
        period_end = now + timedelta(days=30)
        await supabase_service.upsert_user_plan(
            user_id=user_id,
            plan=PLAN_AUTOPILOT,
            billing_status="active",
            provider="demo_checkout",
            provider_customer_id=None,
            provider_subscription_id=f"demo_{user_id[:12]}_{int(now.timestamp())}",
            current_period_start=now.isoformat(),
            current_period_end=period_end.isoformat(),
        )
        return await self.account_summary(user_id)


plan_service = PlanService()
