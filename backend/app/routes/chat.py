"""
Chat routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from app.models import ChatMessageRequest, ChatMessageResponse, ErrorResponse
from app.services import (
    supabase_service,
    firebase_service,
    chat_workflow_service,
    redis_memory_service,
    long_term_memory_service,
)
from app.core.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


def get_current_user(authorization: str = Header(None)) -> str:
    """Extract user ID from Firebase token in Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        # Extract bearer token
        parts = authorization.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise ValueError("Invalid authorization header format")
        token = parts[1]
        
        # Verify with Firebase and extract user ID
        decoded = firebase_service.verify_id_token(token)
        return decoded.get("uid")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    user_id: str = Depends(get_current_user),
) -> dict:
    """
    Send message to AI assistant.

    Args:
        request: Chat message request
        user_id: User ID from authenticated token

    Returns:
        Assistant response
    """
    try:
        result = await chat_workflow_service.process(
            user_id=user_id,
            message=request.content,
            save_messages=True,
            conversation_id=request.conversationId or request.conversation_id,
        )
        response = result["response"]
        assistant_message = result.get("assistant_message") or {}

        return {
            "id": assistant_message.get("id") or "",
            "content": response,
            "role": "assistant",
            "timestamp": assistant_message.get("created_at") or datetime.now().astimezone().isoformat(),
            "model": settings.GEMINI_MODEL,
        }

    except Exception as e:
        logger.error(f"Chat message failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}/memory")
async def delete_conversation_memory(
    conversation_id: str,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Delete Redis short memory and pending tool state for one chat."""
    try:
        await redis_memory_service.delete_conversation(user_id, conversation_id)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to delete chat memory {conversation_id} for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat memory")


@router.post("/conversations/{conversation_id}/memory/exchange")
async def append_conversation_memory(
    conversation_id: str,
    request: dict,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Record a client-handled exchange in chat-scoped Redis memory."""
    user_message = str(request.get("userMessage") or "").strip()
    assistant_message = str(request.get("assistantMessage") or "").strip()
    if not user_message or not assistant_message:
        raise HTTPException(status_code=400, detail="userMessage and assistantMessage are required")

    try:
        await redis_memory_service.append_exchange(
            user_id,
            user_message,
            assistant_message,
            conversation_id=conversation_id,
        )
        await long_term_memory_service.maybe_save(user_id, user_message, assistant_message)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to append chat memory {conversation_id} for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to append chat memory")


@router.get("/history", response_model=list[ChatMessageResponse])
async def get_chat_history(
    limit: int = 50,
    user_id: str = Depends(get_current_user),
) -> list[dict]:
    """
    Get chat history for current user.

    Args:
        limit: Number of messages to retrieve
        user_id: User ID from authenticated token

    Returns:
        List of chat messages
    """
    try:
        messages = await supabase_service.get_messages(user_id, limit=limit)
        return messages
    except Exception as e:
        logger.error(f"Failed to fetch chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-sentiment")
async def analyze_sentiment(
    request: ChatMessageRequest,
    user_id: str = Depends(get_current_user),
) -> dict:
    """
    Analyze sentiment of text.

    Args:
        request: Text to analyze
        user_id: User ID

    Returns:
        Sentiment analysis result
    """
    try:
        from app.agents import ChatAgent
        agent = ChatAgent(user_id)
        analysis = await agent.analyze_sentiment(request.content)
        return analysis
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
