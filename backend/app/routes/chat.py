"""
Chat routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from app.models import ChatMessageRequest, ChatMessageResponse, ErrorResponse
from app.services import supabase_service, firebase_service
from app.agents import ChatAgent
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
        # Create chat agent for user
        agent = ChatAgent(user_id)

        # Generate response
        response = await agent.chat(request.content)

        # Save message to database
        user_message = await supabase_service.create_message(
            user_id=user_id,
            content=request.content,
            role="user",
        )

        assistant_message = await supabase_service.create_message(
            user_id=user_id,
            content=response,
            role="assistant",
            model="gemini-pro",
        )

        return {
            "id": assistant_message.get("id"),
            "content": response,
            "role": "assistant",
            "timestamp": assistant_message.get("created_at"),
            "model": "gemini-pro",
        }

    except Exception as e:
        logger.error(f"Chat message failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        agent = ChatAgent(user_id)
        analysis = await agent.analyze_sentiment(request.content)
        return analysis
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
