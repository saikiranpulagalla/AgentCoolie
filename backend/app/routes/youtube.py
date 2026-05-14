"""
YouTube video detection and opening routes.
Also serves as webhook proxy for chat messages.
"""

from fastapi import APIRouter, HTTPException, status, Request, Depends, Header
from pydantic import BaseModel
from typing import Optional, List
from app.services import (
    gemini_service,
    firebase_service,
    supabase_service,
    chat_workflow_service,
    redis_memory_service,
)
from app.agents import ChatAgent
from app.services.ai_service import extract_pdf_text_with_metadata
import logging
import json
import base64
import re
from urllib.parse import quote_plus

import requests

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["youtube", "webhook"])


def _clean_youtube_query(query: str) -> str:
    cleaned = re.sub(r"\b(can|could|would)\s+(u|you)\b", " ", query, flags=re.I)
    cleaned = re.sub(r"\b(open|play|show|find|search|watch|in|on|youtube|video)\b", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"[?!.]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip() or query.strip()


def _search_youtube_first_video(query: str) -> dict | None:
    search_query = _clean_youtube_query(query)
    url = f"https://www.youtube.com/results?search_query={quote_plus(search_query)}"
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 AgentCoolie/2.0"},
        timeout=10,
    )
    response.raise_for_status()

    seen: set[str] = set()
    for video_id in re.findall(r'"videoId":"([^"]{11})"', response.text):
        if video_id in seen:
            continue
        seen.add(video_id)
        title_match = re.search(
            rf'"videoId":"{re.escape(video_id)}".{{0,2500}}?"title":\{{"runs":\[\{{"text":"([^"]+)"',
            response.text,
            flags=re.DOTALL,
        )
        channel_match = re.search(
            rf'"videoId":"{re.escape(video_id)}".{{0,3500}}?"ownerText":\{{"runs":\[\{{"text":"([^"]+)"',
            response.text,
            flags=re.DOTALL,
        )
        title = title_match.group(1).encode("utf-8").decode("unicode_escape") if title_match else search_query
        channel = channel_match.group(1).encode("utf-8").decode("unicode_escape") if channel_match else "YouTube"
        return {
            "title": title,
            "channel": channel,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "searchQuery": search_query,
        }
    return None


async def _get_preferences_for_prompt(user_id: str) -> dict | None:
    try:
        return await supabase_service.get_preferences(user_id)
    except Exception as e:
        logger.warning(f"Skipping personalization context for {user_id}: {e}")
        return None


async def _maybe_create_task(user_id: str, message: str) -> tuple[dict | None, str | None]:
    try:
        task = await task_intent_service.maybe_create_task_from_message(user_id, message)
        return task, None
    except Exception as e:
        logger.warning(f"Could not create task from webhook message for {user_id}: {e}")
        return None, str(e)


async def _remember_profile_name(user_id: str, user_name: str | None) -> None:
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


def _looks_like_gmail_action(message: str) -> bool:
    text = message.lower()
    if not any(word in text for word in ("gmail", "email", "mail", "inbox")):
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
        )
    )


def _format_n8n_result(result: dict) -> str:
    body = result.get("body")
    if isinstance(body, dict):
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


class YouTubeRequest(BaseModel):
    """Request to detect and open YouTube videos."""
    query: str


class YouTubeResponse(BaseModel):
    """Response from YouTube detection."""
    status: str
    isVideoRequest: bool = False
    confidence: float = 0.0
    video: Optional[dict] = None


class ChatWebhookRequest(BaseModel):
    """Chat webhook request format."""
    message: str
    userId: Optional[str] = None
    userName: Optional[str] = None
    conversationId: Optional[str] = None
    conversation_id: Optional[str] = None


@router.post("/youtube/open", response_model=YouTubeResponse)
async def detect_youtube_video(
    request: YouTubeRequest,
    user_id: str = Depends(get_current_user),
) -> dict:
    """
    Detect if user is asking to open a YouTube video and return video info.
    
    This endpoint uses AI (Gemini) to determine if the user is asking for
    a video and if so, searches for and returns video information.
    
    Args:
        request: YouTube detection request
        
    Returns:
        Response with video detection result and video info if found
    """
    try:
        query = request.query.strip()
        
        if not query:
            return {
                "status": "error",
                "isVideoRequest": False,
                "confidence": 0.0,
                "video": None
            }

        looks_like_video = bool(
            re.search(r"\b(open|play|show|find|search|watch)\b", query, re.I)
            and re.search(r"\b(song|video|youtube|trailer|clip)\b", query, re.I)
        )
        if looks_like_video:
            try:
                video = _search_youtube_first_video(query)
                if video:
                    return {
                        "status": "success",
                        "isVideoRequest": True,
                        "confidence": 0.95,
                        "video": video,
                    }
            except Exception as e:
                logger.warning(f"YouTube scrape search failed, falling back to AI detection: {e}")
        
        # Use Gemini to analyze if this is a video request
        # This is optional - if Gemini is not available, we return false
        if not gemini_service:
            logger.debug("Gemini service not available, skipping video detection")
            return {
                "status": "success",
                "isVideoRequest": False,
                "confidence": 0.0,
                "video": None
            }
        
        prompt = f"""Determine whether this user message is asking to open or find a YouTube/video result.
Respond with strict JSON only:
{{"isVideoRequest": true/false, "confidence": 0.0-1.0, "video": {{"title": "string", "channel": "string", "url": "https://www.youtube.com/..."}} or null}}

User message: {query}"""
        analysis = await gemini_service.analyze_text(text=query, prompt=prompt)
        
        # Try to parse the response
        try:
            result = json.loads(analysis) if isinstance(analysis, str) else analysis
            is_video_request = result.get("isVideoRequest", False)
            confidence = result.get("confidence", 0.0)
            video_info = result.get("video", None)
            if is_video_request and confidence > 0.6 and not (isinstance(video_info, dict) and video_info.get("url")):
                try:
                    video_info = _search_youtube_first_video(query)
                except Exception as e:
                    logger.warning(f"YouTube fallback search failed: {e}")
            
            logger.debug(f"Video detection result: isVideoRequest={is_video_request}, confidence={confidence}")
            
            return {
                "status": "success",
                "isVideoRequest": is_video_request,
                "confidence": confidence,
                "video": video_info
            }
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Failed to parse Gemini response: {e}")
            return {
                "status": "success",
                "isVideoRequest": False,
                "confidence": 0.0,
                "video": None
            }
        
    except Exception as e:
        logger.error(f"YouTube detection error: {e}")
        # Return graceful failure instead of 500 - video detection is optional
        return {
            "status": "success",
            "isVideoRequest": False,
            "confidence": 0.0,
            "video": None
        }


@router.post("/webhook/proxy")
async def webhook_proxy(
    request: Request,
    user_id: str = Depends(get_current_user),
) -> dict:
    """
    Proxy endpoint for chat messages from frontend.
    Accepts both JSON and FormData (multipart) requests.
    
    This endpoint forwards messages to the ChatAgent for processing.
    Automatically detects request format and parses accordingly.
    
    Args:
        request: FastAPI request object
        
    Returns:
        ChatAgent response
    """
    try:
        # Detect content type
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            # JSON request
            data = await request.json()
            message = data.get("message") or ""
            user_name = data.get("userName", "Anonymous")
            conversation_id = data.get("conversationId") or data.get("conversation_id")
            attachments = data.get("attachments") or []
            files = []
        else:
            # FormData request
            form_data = await request.form()
            message = form_data.get("message") or ""
            user_name = form_data.get("userName", "Anonymous")
            conversation_id = form_data.get("conversationId") or form_data.get("conversation_id")
            files = form_data.getlist("files") if "files" in form_data else []
            attachments = []
        
        image_attachment = next(
            (
                item for item in attachments
                if isinstance(item, dict)
                and str(item.get("mime", "")).startswith("image/")
                and str(item.get("url", "")).startswith("data:")
            ),
            None,
        )
        pdf_attachment = next(
            (
                item for item in attachments
                if isinstance(item, dict)
                and str(item.get("mime", "")) == "application/pdf"
                and str(item.get("url", "")).startswith("data:")
            ),
            None,
        )
        file_attachments = [file for file in files if hasattr(file, "read")]
        image_file = next(
            (
                file for file in file_attachments
                if str(getattr(file, "content_type", "") or "").startswith("image/")
            ),
            None,
        )
        pdf_file = next(
            (
                file for file in file_attachments
                if str(getattr(file, "content_type", "") or "") == "application/pdf"
                or str(getattr(file, "filename", "") or "").lower().endswith(".pdf")
            ),
            None,
        )
        audio_file = next(
            (
                file for file in file_attachments
                if str(getattr(file, "content_type", "") or "").startswith("audio/")
            ),
            None,
        )

        if not message and image_attachment:
            message = "Please analyze this image."

        if not message and image_file:
            message = "Please analyze this image."

        if not message and pdf_attachment:
            message = "Please summarize this PDF."

        if not message and pdf_file:
            message = "Please summarize this PDF."

        if not message and audio_file:
            message = (
                "Transcribe this audio message, then answer it as AgentCoolie. "
                "If the audio contains a command or question, respond directly."
            )

        if not message and files:
            message = "Please analyze the attached file."

        if not message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message or attachment is required"
            )
        
        logger.debug(f"Webhook proxy received message: {str(message)[:50]}...")

        attachment_context: list[str] = []
        if image_attachment and gemini_service:
            image_url = str(image_attachment.get("url", ""))
            image_base64 = image_url.split(",", 1)[1] if "," in image_url else image_url
            image_summary = await gemini_service.analyze_image(
                image_base64,
                prompt=f"Describe the image and extract any text relevant to this user request: {message}",
            )
            attachment_context.append(f"Image analysis: {image_summary}")
        if image_file and gemini_service:
            image_bytes = await image_file.read()
            image_base64 = base64.b64encode(image_bytes).decode("ascii")
            image_summary = await gemini_service.analyze_image(
                image_base64,
                prompt=f"Describe the image and extract any text relevant to this user request: {message}",
            )
            attachment_context.append(f"Image analysis: {image_summary}")
        if pdf_attachment:
            pdf_url = str(pdf_attachment.get("url", ""))
            pdf_base64 = pdf_url.split(",", 1)[1] if "," in pdf_url else pdf_url
            pdf_info = extract_pdf_text_with_metadata(pdf_base64)
            pdf_text = str(pdf_info.get("text") or "")
            if pdf_text:
                await redis_memory_service.set_state(
                    user_id,
                    "document",
                    {
                        "kind": "pdf",
                        "filename": pdf_attachment.get("name") or "uploaded PDF",
                        **pdf_info,
                    },
                    ttl_seconds=3600,
                    conversation_id=str(conversation_id) if conversation_id else None,
                )
                limit_note = (
                    f"I can read up to {pdf_info.get('max_pages')} PDF pages per upload. "
                    f"For this file I read {pdf_info.get('pages_read')} of {pdf_info.get('page_count')} pages."
                )
                attachment_context.append(f"PDF text excerpt ({limit_note}): {pdf_text}")
        if pdf_file:
            pdf_bytes = await pdf_file.read()
            pdf_base64 = base64.b64encode(pdf_bytes).decode("ascii")
            pdf_info = extract_pdf_text_with_metadata(pdf_base64)
            pdf_text = str(pdf_info.get("text") or "")
            if pdf_text:
                await redis_memory_service.set_state(
                    user_id,
                    "document",
                    {
                        "kind": "pdf",
                        "filename": getattr(pdf_file, "filename", None) or "uploaded PDF",
                        **pdf_info,
                    },
                    ttl_seconds=3600,
                    conversation_id=str(conversation_id) if conversation_id else None,
                )
                limit_note = (
                    f"I can read up to {pdf_info.get('max_pages')} PDF pages per upload. "
                    f"For this file I read {pdf_info.get('pages_read')} of {pdf_info.get('page_count')} pages."
                )
                attachment_context.append(f"PDF text excerpt ({limit_note}): {pdf_text}")
        if audio_file and gemini_service:
            audio_bytes = await audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode("ascii")
            try:
                transcript = await gemini_service.transcribe_audio(
                    audio_base64,
                    mime_type=str(getattr(audio_file, "content_type", "") or "audio/webm"),
                )
                if transcript.strip():
                    attachment_context.append(f"Audio transcript: {transcript.strip()}")
                    if message.startswith("Transcribe this audio message"):
                        message = transcript.strip()
            except Exception as e:
                logger.warning(f"Audio transcription failed: {e}")
                if message.startswith("Transcribe this audio message"):
                    message = "I could not transcribe that audio. Please try recording again or type the message."

        result = await chat_workflow_service.process(
            user_id=user_id,
            message=message,
            user_name=user_name,
            attachment_context=attachment_context,
            save_messages=True,
            conversation_id=str(conversation_id) if conversation_id else None,
        )
        response = result["response"]
        
        return {
            "status": "success",
            "response": response,
            "userId": user_id,
            "userName": user_name,
            "tool_used": result.get("tool_used"),
            "tool_status": result.get("tool_status"),
            "preferences": result.get("preferences"),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook proxy error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )


@router.post("/webhook/proxy/json", response_model=dict)
async def webhook_proxy_json(
    request: ChatWebhookRequest,
    user_id: str = Depends(get_current_user),
) -> dict:
    """
    JSON version of webhook proxy for simpler requests without files.
    
    Args:
        request: Chat webhook request
        
    Returns:
        ChatAgent response
    """
    try:
        if not request.message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is required"
            )
        
        logger.debug(f"Webhook JSON received message: {request.message[:50]}...")
        
        result = await chat_workflow_service.process(
            user_id=user_id,
            message=request.message,
            user_name=request.userName,
            save_messages=True,
            conversation_id=request.conversationId or request.conversation_id,
        )
        response = result["response"]
        
        return {
            "status": "success",
            "response": response,
            "userId": user_id,
            "userName": request.userName,
            "tool_used": result.get("tool_used"),
            "tool_status": result.get("tool_status"),
            "preferences": result.get("preferences"),
        }
        
    except Exception as e:
        logger.error(f"Webhook JSON proxy error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )
