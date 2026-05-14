"""Unified chat routing and persistence workflow."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from fastapi import HTTPException

from app.agents import ChatAgent
from app.core.config import settings
from app.services.long_term_memory_service import long_term_memory_service
from app.services.n8n_service import n8n_service
from app.services.plan_service import plan_service
from app.services.redis_memory_service import redis_memory_service
from app.services.supabase_service import supabase_service
from app.services.task_intent_service import _fallback_due_date, task_intent_service
from app.services.tracing_service import traceable
from app.services.web_search_service import web_search_service

logger = logging.getLogger(__name__)


def _looks_like_gmail_action(message: str) -> bool:
    text = message.lower()
    if task_intent_service._looks_like_task_request(message):
        return False
    has_recipient_email = bool(_extract_email(message))
    if has_recipient_email and any(word in text for word in ("send", "email", "mail", "reply", "letter")):
        return True
    if not any(word in text for word in ("gmail", "email", "mail", "inbox", "letter")):
        return False
    return any(
        phrase in text
        for phrase in (
            "send",
            "draft",
            "reply",
            "read",
            "check",
            "search",
            "summarize",
            "latest",
            "unread",
            "letter",
        )
    )


def _extract_email(text: str) -> str | None:
    match = re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text or "")
    return match.group(0) if match else None


def _is_send_confirmation(text: str) -> bool:
    normalized = " ".join((text or "").lower().split())
    return normalized in {
        "send",
        "send it",
        "ok send",
        "okay send",
        "yes send",
        "send now",
        "draft and send",
        "use this draft and send",
    } or bool(re.search(r"\b(ok|okay|yes|draft)\b.*\bsend\b", normalized))


def _extract_leave_details(text: str) -> dict[str, str]:
    details: dict[str, str] = {}
    date_match = re.search(
        r"(?:on\s+date\s+|on\s+|for\s+)?((?:\d{1,2}(?:st|nd|rd|th)?\s+)?(?:jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)(?:\s+\d{1,2}(?:st|nd|rd|th)?)?)",
        text or "",
        re.I,
    )
    if date_match:
        details["date"] = date_match.group(1).strip()

    if re.search(r"\bsick\b", text or "", re.I):
        details["reason"] = "sick leave"
    else:
        reason_match = re.search(r"\bfor\s+(.+?)(?:\s+leave)?$", text or "", re.I)
        if reason_match:
            details["reason"] = reason_match.group(1).strip()
    return details


def _looks_like_time_detail(text: str) -> bool:
    lowered = (text or "").lower()
    return bool(
        _fallback_due_date(text or "")
        or re.search(r"\b(today|tomorrow|tonight|next\s+\w+)\b", lowered)
        or re.search(r"\b(?:at|by)\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b", lowered)
    )


def _format_task_created_response(task: dict[str, Any]) -> str:
    title = str(task.get("title") or "Task").strip()
    due = task.get("due_date")
    metadata = task.get("metadata") if isinstance(task.get("metadata"), dict) else {}
    response = f"Done. I created this task in your Tasks page: {title}"
    if due:
        response += f" for {due}"
    if metadata.get("notify_by_call"):
        response += " with a phone call reminder"
    return response + "."


def _compose_leave_email(recipient: str, date_text: str, reason: str, sender_name: str | None) -> dict[str, str]:
    name = " ".join(str(sender_name or "").split()) or "Restitutor Orbis"
    reason_text = reason or "leave"
    subject = f"Leave Request - {reason_text.title()} - {date_text}"
    body = (
        "Dear Sir/Madam,\n\n"
        f"I am writing to request leave on {date_text} due to {reason_text}.\n\n"
        "I kindly request you to approve my leave for the mentioned date. "
        "Please let me know if any additional information is required.\n\n"
        "Thank you for your understanding.\n\n"
        f"Sincerely,\n{name}"
    )
    return {"to": recipient, "subject": subject, "body": body}


def _format_n8n_result(result: dict[str, Any]) -> str:
    body = result.get("body")
    if isinstance(body, dict):
        action = str(body.get("action") or result.get("action") or "").strip()
        payload = result.get("payload") if isinstance(result.get("payload"), dict) else {}
        if body.get("status") == "success":
            if action == "send":
                recipient = payload.get("to") or payload.get("recipient")
                return f"Email sent to {recipient}." if recipient else "Email sent successfully."
            if action in {"list", "search", "listByLabel"}:
                messages = body.get("messages")
                if isinstance(messages, list):
                    if not messages:
                        return "No matching emails found."
                    lines = []
                    for item in messages[:5]:
                        if not isinstance(item, dict):
                            continue
                        sender = item.get("from") or "Unknown sender"
                        subject = item.get("subject") or "(no subject)"
                        lines.append(f"- {subject} - {sender}")
                    return "Found these emails:\n" + "\n".join(lines) if lines else "Emails found."
            if isinstance(body.get("message"), str) and body["message"].strip():
                return body["message"].strip()
            return "Gmail action completed successfully."
        for key in ("response", "message", "text", "summary", "result", "output"):
            value = body.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return json.dumps(body, indent=2)
    if isinstance(body, list):
        return json.dumps(body, indent=2)
    if body:
        return str(body)
    return "Gmail workflow completed."


def _combine_message_with_attachments(message: str, attachment_context: list[str] | None) -> str:
    context = [item.strip() for item in attachment_context or [] if item and item.strip()]
    if not context:
        return message
    return (
        f"{message.strip() or 'Please help with the attached content.'}\n\n"
        "Attached content context:\n"
        + "\n\n".join(context)
    )


def _detect_preference_update(message: str) -> dict[str, Any] | None:
    text = " ".join((message or "").lower().split())
    if not text:
        return None

    updates: dict[str, Any] = {}
    emoji_words = r"(emoji|emojis|emogi|emogis)"
    if re.search(rf"\b(no|dont|don't|do not|never|stop|disable|turn off|avoid|without)\b.*\b{emoji_words}\b", text):
        updates["include_emojis"] = False
    elif re.search(rf"\b(include|use|add|enable|turn on)\b.*\b{emoji_words}\b", text):
        updates["include_emojis"] = True

    if re.search(r"\b(brief|short|concise)\b", text) and re.search(r"\b(response|responses|reply|replies|answer|answers)\b", text):
        updates["response_length"] = "brief"
    elif re.search(r"\b(detailed|long|elaborate)\b", text) and re.search(r"\b(response|responses|reply|replies|answer|answers)\b", text):
        updates["response_length"] = "detailed"
    elif re.search(r"\b(moderate|balanced)\b", text) and re.search(r"\b(response|responses|reply|replies|answer|answers)\b", text):
        updates["response_length"] = "moderate"

    for tone in ("professional", "casual", "friendly", "formal"):
        if re.search(rf"\b{tone}\b", text) and re.search(r"\b(tone|style|speak|respond|reply)\b", text):
            updates["tone"] = tone

    if re.search(r"\b(more formal|high formality)\b", text):
        updates["formality"] = "high"
    elif re.search(r"\b(less formal|casual formality|low formality)\b", text):
        updates["formality"] = "low"

    return updates or None


def _format_preferences_saved(preferences: dict[str, Any]) -> str:
    emoji_text = "enabled" if preferences.get("include_emojis") else "disabled"
    return (
        "Done. I updated your personalization preferences:\n"
        f"- Tone: {preferences.get('tone', 'friendly')}\n"
        f"- Response length: {preferences.get('response_length', 'moderate')}\n"
        f"- Formality: {preferences.get('formality', 'medium')}\n"
        f"- Emojis: {emoji_text}"
    )


class ChatWorkflowService:
    """Single backend workflow for chat, tools, memory, and DB writes."""

    async def _get_preferences_for_prompt(self, user_id: str) -> dict[str, Any] | None:
        try:
            return await supabase_service.get_preferences(user_id)
        except Exception as e:
            logger.warning(f"Skipping personalization context for {user_id}: {e}")
            return None

    async def _maybe_update_preferences(self, user_id: str, message: str) -> tuple[str | None, dict[str, Any] | None]:
        updates = _detect_preference_update(message)
        if not updates:
            return None, None
        current = await self._get_preferences_for_prompt(user_id) or {}
        preferences = {
            "tone": current.get("tone") or "friendly",
            "response_length": current.get("response_length") or "moderate",
            "formality": current.get("formality") or "medium",
            "include_emojis": bool(current.get("include_emojis", False)),
            **updates,
        }
        saved = await supabase_service.upsert_preferences(user_id, preferences)
        merged = {**preferences, **(saved or {})}
        return _format_preferences_saved(merged), merged

    async def _maybe_create_task(self, user_id: str, message: str) -> tuple[dict[str, Any] | None, str | None]:
        try:
            task = await task_intent_service.maybe_create_task_from_message(user_id, message)
            return task, None
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Could not create task from message for {user_id}: {e}")
            return None, str(e)

    async def _remember_profile_name(self, user_id: str, user_name: str | None) -> None:
        name = " ".join(str(user_name or "").strip().split())
        if not name or name.lower() in {"anonymous", "user", "none", "null"}:
            return

        try:
            await long_term_memory_service.remember_fact(
                user_id=user_id,
                content=f"User's display name is {name}.",
                score=0.8,
                reason="Firebase profile display name.",
                source="profile",
            )
        except Exception as e:
            logger.debug(f"Could not save profile display name memory for {user_id}: {e}")

    async def _save_chat_messages(
        self,
        user_id: str,
        message: str,
        response: str,
        conversation_id: str | None = None,
    ) -> dict[str, Any] | None:
        try:
            await supabase_service.create_message(
                user_id=user_id,
                content=message,
                role="user",
                conversation_id=conversation_id,
            )
            return await supabase_service.create_message(
                user_id=user_id,
                content=response,
                role="assistant",
                model=settings.GEMINI_MODEL,
                conversation_id=conversation_id,
            )
        except Exception as e:
            logger.warning(f"Could not persist chat messages for {user_id}: {e}")
            return None

    async def _handle_pending_gmail(
        self,
        user_id: str,
        message: str,
        user_name: str | None,
        conversation_id: str | None = None,
    ) -> tuple[str | None, str | None, dict[str, Any] | None]:
        pending = await redis_memory_service.get_state(user_id, "gmail", conversation_id=conversation_id)
        text = (message or "").strip()
        if not pending:
            if re.search(r"\bsend\b", text, re.I) and re.search(r"\bleave\s+letter\b|\bletter\b", text, re.I):
                recipient = _extract_email(text)
                details = _extract_leave_details(text)
                pending = {
                    "action": "send",
                    "intent": "leave_letter",
                    "recipient": recipient,
                    "date": details.get("date"),
                    "reason": details.get("reason"),
                }
                await redis_memory_service.set_state(user_id, "gmail", pending, conversation_id=conversation_id)
                if not recipient:
                    return "Who should I send the leave letter to?", "gmail", {"configured": True, "connected": True}
            else:
                return None, None, None

        if pending.get("intent") != "leave_letter":
            return None, None, None

        recipient = pending.get("recipient") or _extract_email(text)
        if recipient:
            pending["recipient"] = recipient

        details = _extract_leave_details(text)
        if details.get("date"):
            pending["date"] = details["date"]
        if details.get("reason"):
            pending["reason"] = details["reason"]

        if not pending.get("recipient"):
            await redis_memory_service.set_state(user_id, "gmail", pending, conversation_id=conversation_id)
            return "Who should I send the leave letter to?", "gmail", {"configured": True, "connected": True}

        if not pending.get("date") or not pending.get("reason"):
            await redis_memory_service.set_state(user_id, "gmail", pending, conversation_id=conversation_id)
            return "Please tell me the leave date and reason.", "gmail", {"configured": True, "connected": True}

        payload = pending.get("payload")
        if not isinstance(payload, dict):
            payload = _compose_leave_email(
                recipient=str(pending["recipient"]),
                date_text=str(pending["date"]),
                reason=str(pending["reason"]),
                sender_name=user_name,
            )
            pending["payload"] = payload

        if _is_send_confirmation(text):
            try:
                await plan_service.ensure_feature_available(user_id, "gmail_sends")
            except HTTPException as e:
                return str(e.detail), "gmail", {"plan_limited": True}
            tool_status = await n8n_service.gmail_status(user_id)
            if not tool_status.get("configured"):
                return "Gmail automation is not configured on the backend yet.", "gmail", tool_status
            if not tool_status.get("connected"):
                return "Gmail is not connected. Go to Settings and connect Gmail first, then ask me again.", "gmail", tool_status

            gmail_tool_result = await n8n_service.run_gmail_action(user_id, text, action="send", payload=payload)
            await redis_memory_service.delete_state(user_id, "gmail", conversation_id=conversation_id)
            if gmail_tool_result.get("ok"):
                return _format_n8n_result(gmail_tool_result), "gmail", tool_status
            return str(
                gmail_tool_result.get("message")
                or gmail_tool_result.get("body")
                or "The Gmail workflow is not ready yet."
            ), "gmail", tool_status

        await redis_memory_service.set_state(user_id, "gmail", pending, conversation_id=conversation_id)
        return (
            "Here is the draft:\n\n"
            f"Subject: {payload['subject']}\n\n"
            f"{payload['body']}\n\n"
            f"Send this to {payload['to']}?",
            "gmail",
            {"configured": True, "connected": True},
        )

    @traceable(name="tool_state.handle_pending_task", run_type="chain")
    async def _handle_pending_task(
        self,
        user_id: str,
        message: str,
        conversation_id: str | None = None,
    ) -> tuple[str | None, dict[str, Any] | None, str | None]:
        text = (message or "").strip()
        if not text:
            return None, None, None

        pending = await redis_memory_service.get_state(user_id, "task", conversation_id=conversation_id)
        if pending:
            original = str(pending.get("message") or "").strip()
            combined = f"{original}. {text}".strip()
            if not _fallback_due_date(combined):
                await redis_memory_service.set_state(
                    user_id,
                    "task",
                    {"message": combined},
                    conversation_id=conversation_id,
                )
                return "Got it. What date and time should I do this?", None, None

            task = await task_intent_service.maybe_create_task_from_message(user_id, combined)
            await redis_memory_service.delete_state(user_id, "task", conversation_id=conversation_id)
            if task:
                return None, task, None
            return "I could not save that task. Please send the task and time in one message.", None, "task_parse_failed"

        if not task_intent_service._looks_like_task_request(text):
            return None, None, None

        if _fallback_due_date(text):
            return None, None, None

        await redis_memory_service.set_state(user_id, "task", {"message": text}, conversation_id=conversation_id)
        return "Sure. When should I do this task?", None, None

    @traceable(name="chat_workflow.process", run_type="chain")
    async def process(
        self,
        user_id: str,
        message: str,
        user_name: str | None = None,
        attachment_context: list[str] | None = None,
        save_messages: bool = True,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        plan = await plan_service.check_and_consume(
            user_id,
            "chat_messages",
            metadata={"conversation_id": conversation_id},
        )
        original_message = (message or "").strip()
        effective_message = _combine_message_with_attachments(original_message, attachment_context)

        chat_agent = ChatAgent(user_id=user_id)
        await self._remember_profile_name(user_id, user_name)

        short_memory_turns = int(plan.get("caps", {}).get("short_memory_turns") or settings.REDIS_MEMORY_CONTEXT_EXCHANGES)
        context = await redis_memory_service.get_recent_exchanges(
            user_id,
            limit=short_memory_turns,
            conversation_id=conversation_id,
        )
        long_term_memories = await long_term_memory_service.get_context(user_id)
        preferences = await self._get_preferences_for_prompt(user_id)
        preference_response, updated_preferences = await self._maybe_update_preferences(
            user_id,
            original_message or effective_message,
        )
        if updated_preferences:
            preferences = updated_preferences
        pending_task_response, created_task, task_error = await self._handle_pending_task(
            user_id,
            original_message or effective_message,
            conversation_id=conversation_id,
        )
        if not pending_task_response and not created_task and not task_error:
            created_task, task_error = await self._maybe_create_task(user_id, original_message or effective_message)

        web_results: list[dict[str, Any]] = []
        web_search_attempted = web_search_service.should_search(original_message or effective_message)
        if web_search_attempted:
            await plan_service.check_and_consume(
                user_id,
                "web_searches",
                metadata={"source": "chat", "conversation_id": conversation_id},
            )
            web_results = await web_search_service.search(original_message or effective_message, limit=5)

        document_state = await redis_memory_service.get_state(user_id, "document", conversation_id=conversation_id)
        if document_state and isinstance(document_state, dict):
            document_text = str(document_state.get("text") or "").strip()
            if document_text and not any(str(item).startswith("PDF") for item in attachment_context or []):
                attachment_context = [
                    *(attachment_context or []),
                    (
                        f"Recent PDF context from {document_state.get('filename') or 'the last uploaded PDF'} "
                        f"(pages read: {document_state.get('pages_read')}; total pages: {document_state.get('page_count')}; "
                        f"truncated: {document_state.get('truncated')}):\n{document_text}"
                    ),
                ]
                effective_message = _combine_message_with_attachments(original_message, attachment_context)

        tool_used = None
        tool_status: dict[str, Any] | None = None
        pending_response, pending_tool, pending_status = await self._handle_pending_gmail(
            user_id,
            original_message or effective_message,
            user_name,
            conversation_id=conversation_id,
        )
        if preference_response:
            response = preference_response
            tool_used = "preferences"
        elif created_task:
            response = _format_task_created_response(created_task)
            tool_used = "tasks"
        elif pending_response:
            response = pending_response
            tool_used = pending_tool
            tool_status = pending_status
        elif pending_task_response:
            response = pending_task_response
            tool_used = "tasks"
        elif _looks_like_gmail_action(original_message or effective_message):
            try:
                await plan_service.ensure_feature_available(user_id, "gmail_sends")
            except HTTPException as e:
                response = str(e.detail)
                tool_status = {"plan_limited": True}
                tool_used = "gmail"
            else:
                tool_status = await n8n_service.gmail_status(user_id)
                if not tool_status.get("configured"):
                    response = "Gmail automation is not configured on the backend yet."
                elif not tool_status.get("connected"):
                    response = "Gmail is not connected. Go to Settings and connect Gmail first, then ask me again."
                else:
                    gmail_tool_result = await n8n_service.run_gmail_action(user_id, original_message or effective_message)
                    tool_used = "gmail"
                    if gmail_tool_result.get("ok"):
                        response = _format_n8n_result(gmail_tool_result)
                    else:
                        response = str(
                            gmail_tool_result.get("message")
                            or gmail_tool_result.get("body")
                            or "The Gmail workflow is not ready yet."
                        )
        else:
            response = await chat_agent.chat(
                effective_message,
                context=context,
                long_term_memories=long_term_memories,
                preferences=preferences,
                web_results=web_results,
                web_search_attempted=web_search_attempted,
            )

        if task_error:
            response += "\n\nI understood this as a task request, but I could not save it to the Tasks page right now."

        await redis_memory_service.append_exchange(
            user_id,
            original_message or effective_message,
            response,
            conversation_id=conversation_id,
        )
        await long_term_memory_service.maybe_save(user_id, original_message or effective_message, response)
        assistant_message = None
        if save_messages:
            assistant_message = await self._save_chat_messages(
                user_id,
                original_message or effective_message,
                response,
                conversation_id=conversation_id,
            )

        return {
            "response": response,
            "assistant_message": assistant_message,
            "tool_used": tool_used,
            "tool_status": tool_status,
            "task": created_task,
            "preferences": updated_preferences,
            "web_search_attempted": web_search_attempted,
        }


chat_workflow_service = ChatWorkflowService()
