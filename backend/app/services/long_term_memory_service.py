"""
Long-term memory selection and retrieval.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any

from app.core.config import settings
from app.services.ai_service import gemini_service
from app.services.supabase_service import is_connectivity_error, supabase_service

logger = logging.getLogger(__name__)


class LongTermMemoryService:
    """Decides which turns deserve durable memory and stores them in Supabase."""

    def _normalize_content(self, content: str) -> str:
        return re.sub(r"\s+", " ", content.strip().lower()).rstrip(".!?")

    def _extract_json(self, text: str) -> dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start:end + 1])
            raise

    def _heuristic_memories(self, user_message: str) -> list[dict[str, Any]]:
        """Extract obvious durable facts before asking the model."""
        text = " ".join(user_message.strip().split())
        lower = text.lower()
        memories: list[dict[str, Any]] = []

        name_match = re.search(r"\b(?:i am|i'm|my name is)\s+([a-z][a-z .'-]{1,60})(?:\s+from\b|[,.]|$)", text, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip()
            memories.append({
                "content": f"User's name is {name}.",
                "importance_score": 0.95,
                "reason": "User shared their name.",
            })

        education_match = re.search(
            r"\bfrom\s+([a-z0-9 .&'-]{2,80}?\b(?:college|university|school|institute))\b",
            text,
            re.IGNORECASE,
        )
        if education_match:
            institution = education_match.group(1).strip()
            memories.append({
                "content": f"User is from {institution}.",
                "importance_score": 0.9,
                "reason": "User shared education/institution information.",
            })

        marks_match = re.search(
            r"\b(?:got|scored|secured|received)\s+(\d{1,3})\s*(?:marks?|%)\s+in\s+([a-z0-9 .&'-]{2,80}?)(?:\s+exam|\s+test|\s+quiz|[,.]|$)",
            lower,
            re.IGNORECASE,
        )
        if marks_match:
            score = marks_match.group(1)
            subject = marks_match.group(2).strip()
            exam_date = None
            if "yesterday" in lower:
                exam_date = (datetime.now() - timedelta(days=1)).date().isoformat()
            date_text = f" on {exam_date}" if exam_date else ""
            memories.append({
                "content": f"User scored {score} marks in {subject}{date_text}.",
                "importance_score": 0.85,
                "reason": "User shared an academic achievement.",
            })

        return memories

    async def _save_memory(
        self,
        user_id: str,
        content: str,
        score: float,
        reason: str | None,
        source: str,
        user_message: str,
        assistant_response: str,
    ) -> None:
        normalized_content = self._normalize_content(content)
        existing = await supabase_service.find_long_term_memory_by_normalized_content(
            user_id=user_id,
            normalized_content=normalized_content,
        )
        if existing:
            logger.debug("Skipping duplicate long-term memory")
            return

        await supabase_service.create_long_term_memory(
            user_id=user_id,
            content=content[:2000],
            normalized_content=normalized_content,
            source=source,
            importance_score=min(max(score, 0), 1),
            reason=reason,
            metadata={
                "normalized_content": normalized_content,
                "user_message": user_message[:4000],
                "assistant_response": assistant_response[:4000],
            },
        )

    async def remember_fact(
        self,
        user_id: str,
        content: str,
        score: float = 0.75,
        reason: str | None = None,
        source: str = "profile",
    ) -> None:
        """Save a known durable user fact with duplicate protection."""
        if not settings.LONG_TERM_MEMORY_ENABLED:
            return

        content = " ".join(content.strip().split())
        if not content:
            return

        await self._save_memory(
            user_id=user_id,
            content=content,
            score=score,
            reason=reason,
            source=source,
            user_message=content,
            assistant_response="Saved as durable user context.",
        )

    async def get_context(self, user_id: str) -> list[dict[str, Any]]:
        if not settings.LONG_TERM_MEMORY_ENABLED:
            return []

        try:
            return await supabase_service.get_long_term_memories(
                user_id,
                limit=settings.LONG_TERM_MEMORY_CONTEXT_LIMIT,
            )
        except Exception as e:
            if is_connectivity_error(e):
                logger.warning("Long-term memory skipped because Supabase is unreachable")
            else:
                logger.warning(f"Long-term memory fetch failed: {e}")
            return []

    async def maybe_save(self, user_id: str, user_message: str, assistant_response: str, source: str = "chat") -> None:
        if not settings.LONG_TERM_MEMORY_ENABLED or not gemini_service:
            return

        saved_heuristic = False
        for item in self._heuristic_memories(user_message):
            try:
                await self._save_memory(
                    user_id=user_id,
                    content=str(item["content"]),
                    score=float(item["importance_score"]),
                    reason=str(item["reason"]),
                    source=source,
                    user_message=user_message,
                    assistant_response=assistant_response,
                )
                saved_heuristic = True
            except Exception as e:
                if is_connectivity_error(e):
                    logger.warning("Long-term memory save skipped because Supabase is unreachable")
                else:
                    logger.warning(f"Heuristic long-term memory save failed: {e}")

        if saved_heuristic:
            return

        prompt = f"""Decide whether this user turn contains stable, important information worth remembering long-term.
Save only durable preferences, identity details, goals, recurring plans, constraints, important relationships, or user-specific facts.
Do not save temporary requests, greetings, one-off commands, secrets, passwords, API keys, or sensitive credentials.

Respond with strict JSON only:
{{"save": true/false, "importance_score": 0.0-1.0, "memory": "one concise first-person-neutral fact to remember", "reason": "short reason"}}

User message:
{user_message}

Assistant response:
{assistant_response}"""

        try:
            raw = await gemini_service.analyze_text(user_message, prompt=prompt)
            decision = self._extract_json(raw if isinstance(raw, str) else json.dumps(raw))
        except Exception as e:
            logger.warning(f"Long-term memory decision failed: {e}")
            return

        should_save = bool(decision.get("save"))
        score = float(decision.get("importance_score") or 0)
        memory = str(decision.get("memory") or "").strip()
        reason = str(decision.get("reason") or "").strip() or None

        if not should_save or score < settings.LONG_TERM_MEMORY_MIN_IMPORTANCE or not memory:
            return

        try:
            await self._save_memory(
                user_id=user_id,
                content=memory,
                score=score,
                reason=reason,
                source=source,
                user_message=user_message,
                assistant_response=assistant_response,
            )
        except Exception as e:
            if is_connectivity_error(e):
                logger.warning("Long-term memory save skipped because Supabase is unreachable")
            else:
                logger.warning(f"Long-term memory save failed: {e}")


long_term_memory_service = LongTermMemoryService()
